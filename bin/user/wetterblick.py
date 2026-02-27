# Copyright 2013-2020 Matthew Wall + MSlabs
"""
Upload data to wetterblick.com
  https://wetterblick.com

[StdRESTful]
    [[Wetterblick]]
        enable = true | false
        username = STATION ID
        password = STATION PASSWORD
"""

try:
    # Python 3
    import queue
except ImportError:
    import Queue as queue
import re
import sys
import time
try:
    # Python 3
    from urllib.parse import urlencode
except ImportError:
    # Python 2
    from urllib import urlencode

import weewx
import weewx.restx
import weewx.units

VERSION = "0.1"
API_VERSION = "1.0.0 - 2026/02/01"

if weewx.__version__ < "3":
    raise weewx.UnsupportedFeature("weewx 3 is required, found %s" %
                                   weewx.__version__)

try:
    # Test for new-style weewx logging by trying to import weeutil.logger
    import weeutil.logger
    import logging
    log = logging.getLogger(__name__)

    def logdbg(msg):
        log.debug(msg)

    def loginf(msg):
        log.info(msg)

    def logerr(msg):
        log.error(msg)

except ImportError:
    # Old-style weewx logging
    import syslog

    def logmsg(level, msg):
        syslog.syslog(level, 'Wetterblick: %s' % msg)

    def logdbg(msg):
        logmsg(syslog.LOG_DEBUG, msg)

    def loginf(msg):
        logmsg(syslog.LOG_INFO, msg)

    def logerr(msg):
        logmsg(syslog.LOG_ERR, msg)


class Wetterblick(weewx.restx.StdRESTful):
    def __init__(self, engine, config_dict):
        """This service recognizes standard restful options plus the following:

        username: username

        password: password
        """
        super(Wetterblick, self).__init__(engine, config_dict)
        loginf("service version is %s" % VERSION)
        loginf("wetterblick API version is %s" % API_VERSION)
        site_dict = weewx.restx.get_site_dict(config_dict, 'Wetterblick', 'username', 'password')
        if site_dict is None:
            return

        site_dict['manager_dict'] = weewx.manager.get_manager_dict_from_config(
            config_dict, 'wx_binding')

        self.archive_queue = queue.Queue()
        self.archive_thread = WetterblickThread(self.archive_queue, **site_dict)
        self.archive_thread.start()
        self.bind(weewx.NEW_ARCHIVE_RECORD, self.new_archive_record)
        loginf("Data will be uploaded for station id %s" % site_dict['username'])

    def new_archive_record(self, event):
        self.archive_queue.put(event.record)

class WetterblickThread(weewx.restx.RESTThread):

    _SERVER_URL = 'https://wetterblick-api.com/sd'
    _DATA_MAP = {
        'temp': ('outTemp', '%.1f'),       # C
        'relhum': ('outHumidity', '%.0f'), # percent
        'pressure': ('barometer', '%.1f'), # hPa
        'wind': ('windSpeed', '%.1f'),     # m/s
        'gusts': ('windGust', '%.1f'),     # m/s
        'rain': ('rainRate', '%.2f'),      # mm/hr
        'rain1h': ('hourRain', '%.2f'),    # mm
        'rainday': ('dayRain', '%.2f'),    # mm
        'dewpoint': ('dewpoint', '%.1f')   # C
    }

    def __init__(self, queue, username, password, manager_dict,
                 server_url=_SERVER_URL, skip_upload=False,
                 post_interval=None, max_backlog=sys.maxsize, stale=None,
                 log_success=True, log_failure=True,
                 timeout=60, max_tries=3, retry_wait=5):
        super(WetterblickThread, self).__init__(queue,
                                                protocol_name='Wetterblick',
                                                manager_dict=manager_dict,
                                                post_interval=post_interval,
                                                max_backlog=max_backlog,
                                                stale=stale,
                                                log_success=log_success,
                                                log_failure=log_failure,
                                                max_tries=max_tries,
                                                timeout=timeout,
                                                retry_wait=retry_wait,
                                                skip_upload=skip_upload)
        self.username = username
        self.password = password
        self.server_url = server_url

    def check_response(self, response):
        """Override, and check for wetterblick errors."""
        txt = response.read().decode().lower()
        if txt.find('"errorcode":"100"') != -1 or \
           txt.find('"errorcode":"101"') != -1 or \
           txt.find('"errorcode":"102"') != -1:
            raise weewx.restx.BadLogin(txt)
        elif txt.find('"status":"error"') != -1:
            raise weewx.restx.FailedPost("Server returned '%s'" % txt)

    def format_url(self, in_record):
        """Override, and format an URL for wetterblick"""
        # put everything into the right units
        record = weewx.units.to_METRICWX(in_record)

        # put data into expected scaling, structure, and format
        values = {}
        values['user'] = self.username
        values['pw'] = self.password
        values['date'] = time.strftime('%d.%m.%Y', time.localtime(record['dateTime']))
        values['time'] = time.strftime('%H:%M:%S', time.localtime(record['dateTime']))
        for key in self._DATA_MAP:
            rkey = self._DATA_MAP[key][0]
            if rkey in record and record[rkey] is not None:
                values[key] = self._DATA_MAP[key][1] % record[rkey]
            else:
                values[key] = ''

        values['wind-dir'] = self._deg_to_compass(record.get('windDir'))
        values['sensor-time'] = ''
        values['air-pressure-tendency-text'] = ''
        values['air-pressure-tendency-3h'] = ''

        url = "%s?%s" % (self.server_url, urlencode(values))
        if weewx.debug >= 2:
            logdbg('url: %s' % re.sub(r"pw=[^\&]*", "pw=XXX", url))
        return url

    @staticmethod
    def _deg_to_compass(deg):
        if deg is None:
            return ''
        try:
            deg = float(deg) % 360.0
        except (TypeError, ValueError):
            return ''
        dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        idx = int((deg + 11.25) / 22.5) % 16
        return dirs[idx]


# Do direct testing of this extension like this:
#   PYTHONPATH=WEEWX_BINDIR python WEEWX_BINDIR/user/wetterblick.py
if __name__ == "__main__":
    import optparse

    weewx.debug = 2

    try:
        # WeeWX V4 logging
        weeutil.logger.setup('wetterblick', {})
    except NameError:
        # WeeWX V3 logging
        syslog.openlog('wetterblick', syslog.LOG_PID | syslog.LOG_CONS)
        syslog.setlogmask(syslog.LOG_UPTO(syslog.LOG_DEBUG))

    usage = """%prog --user USERNAME --pw PASSWORD [--version] [--help]"""

    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--version', dest='version', action='store_true',
                      help='display driver version')
    parser.add_option('--user', metavar='USERNAME',
                      help='The username')
    parser.add_option('--pw', metavar='PASSWORD', help='Password for USERNAME')
    (options, args) = parser.parse_args()

    if options.version:
        print("wetterblick uploader version %s" % VERSION)
        exit(0)

    if options.user is None or options.pw is None:
        exit("You must supply both option --user and option --pw.")

    print("Using username '%s' and password '%s'" % (options.user, options.pw))
    q = queue.Queue()
    t = WetterblickThread(q, options.user, options.pw, manager_dict=None)
    t.start()
    q.put({'dateTime': int(time.time() + 0.5),
           'usUnits': weewx.US,
           'outTemp': 32.5,
           'inTemp': 75.8,
           'outHumidity': 24})
    q.put(None)
    t.join(20)

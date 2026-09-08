# installer for wetterblick.com
# Copyright 2014-2020 Matthew Wall + MSlabs
# Distributed under the terms of the GNU Public License (GPLv3)

from weecfg.extension import ExtensionInstaller

def loader():
    return WetterblickInstaller()

class WetterblickInstaller(ExtensionInstaller):
    def __init__(self):
        super(WetterblickInstaller, self).__init__(
            version="0.2",
            name='wetterblick',
            description='Upload weather data to wetterblick.com.',
            author="Matthew Wall + MSlabs",
            author_email="",
            restful_services='user.wetterblick.Wetterblick',
            config={
                'StdRESTful': {
                    'Wetterblick': {
                        'username': 'INSERT_USERNAME_HERE',
                        'password': 'INSERT_PASSWORD_HERE',
                        # Wetterblick timestamps a measurement with its own
                        # clock, rounded down to ten minutes -- the timestamp in
                        # the record is ignored. After an outage weewx would
                        # post its whole backlog, and every one of those records
                        # would land in the current slot, overwriting each
                        # other. Skipping records older than one slot keeps the
                        # station from reporting old data as current.
                        'stale': '600'}}},
            files=[('bin/user', ['bin/user/wetterblick.py'])]
            )

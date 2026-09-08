wetterblick - weewx extension that sends data to wetterblick.com
Adapted in 2026 by MSlabs, special thanks to Matthew Wall (2014-2020) for the original Code.
Distributed under the terms of the GNU Public License (GPLv3)

Before you start: register your station at

  https://www.wetterblick.com/netzwerk

You get a station key (wb_st_...) there. It is what goes into `password` below --
not your Wetterblick account password.

Installation instructions:

1) download

wget -O weewx-wetterblick.zip https://github.com/marcelS97/weewx-wetterblick/archive/main.zip

2) run the installer:

weectl extension install weewx-wetterblick.zip     # weewx 5
wee_extension --install weewx-wetterblick.zip      # weewx 4

3) modify weewx.conf:

[StdRESTful]
    [[Wetterblick]]
        enable = true
        username = STATION NAME
        password = STATION KEY
        stale = 600

4) restart weewx

sudo systemctl restart weewx                       # systemd
sudo /etc/init.d/weewx restart                     # sysvinit

Notes:

- Keep the weewx archive interval at 5 minutes (the default). Wetterblick stores
  measurements in ten minute slots; a longer interval occasionally leaves a slot
  empty, which looks like an outage on the map.
- Wetterblick expects km/h, hPa, mm and degrees Celsius. The extension converts
  the m/s that weewx reports internally.
- `stale = 600` drops records older than ten minutes instead of posting them.
  Wetterblick stamps a measurement with its own clock, so a backlog posted after
  an outage would show up as current data. Ten minutes is one Wetterblick slot.

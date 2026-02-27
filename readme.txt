wetterblick - weewx extension that sends data to wetterblick.com
Adapted in 2026 by MSlabs, special thanks to Matthew Wall (2014-2020) for the original Code.
Distributed under the terms of the GNU Public License (GPLv3)

Installation instructions:

1) download

wget -O weewx-wetterblick.zip https://github.com/marcels97/weewx-wetterblick/archive/main.zip

1) run the installer:

wee_extension -install weewx-wetterblick.zip

2) modify weewx.conf:

[StdRESTful]
    [[Wetterblick]]
        username = USERNAME
        password = PASSWORD

3) restart weewx

sudo /etc/init.d/weewx stop
sudo /etc/init.d/weewx start

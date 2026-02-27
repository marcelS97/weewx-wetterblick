# installer for wetterblick.com
# Copyright 2014-2020 Matthew Wall + MSlabs
# Distributed under the terms of the GNU Public License (GPLv3)

from weecfg.extension import ExtensionInstaller

def loader():
    return WetterblickInstaller()

class WetterblickInstaller(ExtensionInstaller):
    def __init__(self):
        super(WetterblickInstaller, self).__init__(
            version="0.1",
            name='wetterblick',
            description='Upload weather data to wetterblick.com.',
            author="Matthew Wall + MSlabs",
            author_email="",
            restful_services='user.wetterblick.Wetterblick',
            config={
                'StdRESTful': {
                    'Wetterblick': {
                        'username': 'INSERT_USERNAME_HERE',
                        'password': 'INSERT_PASSWORD_HERE'}}},
            files=[('bin/user', ['bin/user/wetterblick.py'])]
            )

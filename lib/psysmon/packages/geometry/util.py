# LICENSE
#
# This file is part of pSysmon.
#
# If you use pSysmon in any program or publication, please inform and
# acknowledge its author Stefan Mertl (stefan@mertl-research.at).
#
# pSysmon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
'''
The geometry util module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    http://www.gnu.org/licenses/gpl-3.0.html

This module contains helper functions used in the geometry package.
'''
def lon2UtmZone(lon):
    '''
    Convert a longitude to the UTM zone.

    The formula is based on the wikipedia description:
    The UTM system divides the surface of Earth between 80S and 84N latitude 
    into 60 zones, each 6 of longitude in width. Zone 1 covers longitude 180 
    to 174 W; zone numbering increases eastward to zone 60 that covers 
    longitude 174 to 180 East.
    '''
    if lon < -180 or lon > 180:
        raise ValueError('The longitude must be between -180 and 180.')

    return (int((180 + lon) / 6.0) + 1) % 60


def zone2UtmCentralMeridian(zone):
    '''
    Compute the middle meridian of a given UTM zone.
    '''
    if zone < 1 or zone > 60:
        raise ValueError('The zone must be between 1 and 60.')

    return zone * 6 - 180 - 3

ellipsoids = {}
ellipsoids['wgs84'] = (6378137, 6356752.314245179)

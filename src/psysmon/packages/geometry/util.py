# LICENSE
#
# This file is part of pSysmon.
#
# If you use pSysmon in any program or publication, please inform and
# acknowledge its author Stefan Mertl (info@stefanmertl.com).
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
    '''
    return int((180 + lon) / 6) + 1


def zone2UtmCentralMeridian(zone):
    '''
    Compute the middle meridian of a given UTM zone.
    '''
    return zone * 6 - 180 - 3

ellipsoids = {}
ellipsoids['wgs84'] = (6378137, 6356752.3142)

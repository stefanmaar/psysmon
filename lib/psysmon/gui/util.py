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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from obspy.core import UTCDateTime
from wx import DateTime


def wxdate2pydate(date):
    if date is None:
        return None

    assert isinstance(date, DateTime)
    if date.IsValid():
        ymd = list(map(int, date.FormatISODate().split('-')))
        return UTCDateTime(*ymd)
    else:
        return None


def pydate2wxdate(date):
    if date is None:
        return None

    assert isinstance(date, UTCDateTime)
    tt = date.timetuple()
    dmy = (tt[2], tt[1] - 1, tt[0])
    return DateTime.FromDMY(*dmy)

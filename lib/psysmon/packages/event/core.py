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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from obspy.core.event import Event as ObspyEvent
from obspy.core.event import ResourceIdentifier
from obspy.core.event import Comment
from obspy.core.event import CreationInfo
from obspy.core.utcdatetime import UTCDateTime

class Event(ObspyEvent):

    def __init__(self, start_time, end_time, db_id = None, tags = [], *args, **kwargs):
        ObspyEvent.__init__(self, *args, **kwargs)

        # The unique database id.
        self.db_id = db_id

        # Check for None values in the event limits.
        if start_time is None or end_time is None:
            raise ValueError("None values are not allowed for the event time limits.")

        # Check the event limits.
        if end_time < start_time:
            raise ValueError("The end_time %s is smaller than the start_time %s.", end_time, start_time)
        elif end_time == start_time:
            raise ValueError("The end_time %s is equal to the start_time %s.", end_time, start_time)


        # The start time of the event.
        self.start_time = UTCDateTime(start_time)

        # The end time of the event.
        self.end_time = UTCDateTime(end_time)

        # The tags of the event.
        self.tags = []

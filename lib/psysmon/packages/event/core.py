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


from obspy.core.event import Event
from obspy.core.event import ResourceIdentifier
from obspy.core.event import Comment
from obspy.core.event import CreationInfo
from obspy.core.utcdatetime import UTCDateTime

class PsysmonEvent(Event):

    def __init__(self, *args, **kwargs):
        Event.__init__(self, *args, **kwargs)

        # The start time of the event.
        self.start_time = UTCDateTime()

        # The end time of the event.
        self.end_time = UTCDateTime()

        # The number of stations on which the event is detected on.
        self.num_stations = None

        # The tags of the event.
        self.tags = []

        # The id of the eventset.
        self.set_id = None



class EventParameters:
    ''' An event container.

    An event set can be used to group events into sets. The events are stored 
    in a list.

    Attributes
    ----------
    resource_id : :class:`~obspy.core.event.ResourceIdentifier`
        The unique resource id of the eventset. Should be 
        smi:psysmon.AUTHOR.PROJECTNAME/eventset/DB_EVENTSET_ID

    mode : String
        The mode of the event set (psysmon, bulletin).

    events : List of :class:`PsysmonEvent`
        The event instances contained in the event set.

    '''

    def __init__(self, 
                 public_id = ResourceIdentifier(), 
                 description = None, 
                 comment = Comment(), 
                 creation_info = CreationInfo()):
        ''' The constructor.

        Parameters
        ---------
        public_id : :class:`~obspy.core.event.ResourceIdentifier`
            The unique resource id of the eventset. Should be 
            smi:psysmon.AUTHOR.PROJECTNAME/eventset/DB_EVENTSET_ID

        description : String
            The description of the event parameters.

        comment : :class:`~obspy.core.event.Comment`
            The comment of the event parameters.

        creation_info : :class:`~obspy.core.event.CreationInfo`
            The creation information of the event parameters.
        '''

        # The resource id of the event set.
        self.public_id = public_id

        # The discription of the event parameters.
        self.description = description

        # The comment of the event parameters.
        self.comment = comment

        # The creation information of the event parameters.
        self.creation_info = creation_info

        # The mode of the event set (psysmon, bulletin).
        self.mode = None

        # The events contained in the event set.
        self.events = []

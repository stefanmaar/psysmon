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
from obspy.core.event import Catalog as ObspyCatalog
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


    def write_to_database(self, project):
        ''' Write the event to the pSysmon database.
        '''
        if self.db_id is None:
            # If the db_id is None, insert a new event.
            if self.creation_info.creation_time is not None:
                creation_time = self.creation_info.creation_time.timestamp
            else:
                creation_time = None

            db_session = project.getDbSession()
            db_event_orm = project.dbTables['event']
            db_event = db_event_orm(start_time = repr(self.start_time.timestamp),
                                    end_time = repr(self.end_time.timestamp),
                                    public_id = self.resource_id,
                                    pref_origin_id = None,
                                    pref_magnitude_id = None, 
                                    pref_focmec_id = None,
                                    ev_type = self.event_type,
                                    ev_type_certainty = self.event_type_certainty,
                                    agency_id = self.creation_info.agency_id,
                                    agency_uri = self.creation_info.agency_uri,
                                    author = self.creation_info.author,
                                    author_uri = self.creation_info.author_uri,
                                    creation_time = repr(creation_time),
                                    version = self.creation_info.version
                                   )
            db_session.add(db_event)
            db_session.commit()
            db_session.close()

        else:
            # If the db_id is not None, update the existing event.
            pass



class Catalog(ObspyCatalog):

    def __init__(self, db_id = None, *args, **kwargs):
        ObspyCatalog.__init__(self, *args, **kwargs)

        self.db_id = db_id


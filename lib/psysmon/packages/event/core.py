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


import obspy.core.utcdatetime as utcdatetime

class Event(object):

    def __init__(self, start_time, end_time, db_id = None, public_id = None, event_type = None,
            event_type_certainty = None, description = None, comment = None,
            tags = [], agency_uri = None, author_uri = None, creation_time = None,
            parent = None):
        ''' Instance initialization

        '''
        # Check for correct input arguments.
        # Check for None values in the event limits.
        if start_time is None or end_time is None:
            raise ValueError("None values are not allowed for the event time limits.")

        # Check the event limits.
        if end_time < start_time:
            raise ValueError("The end_time %s is smaller than the start_time %s.", end_time, start_time)
        elif end_time == start_time:
            raise ValueError("The end_time %s is equal to the start_time %s.", end_time, start_time)

        # The parent object holding this event. Most likely this is a event
        # Catalog instance.
        self.parent = parent

        # The unique database id.
        self.db_id = db_id

        # The unique public id.
        self.public_id = public_id

        # The start time of the event.
        self.start_time = utcdatetime.UTCDateTime(start_time)

        # The end time of the event.
        self.end_time = utcdatetime.UTCDateTime(end_time)

        # The event type.
        self.event_type = event_type

        # The certainty of the event_type.
        self.event_type_certainty = event_type_certainty

        # The description of the event.
        self.description = description

        # The comment added to the event.
        self.comment = comment

        # The tags of the event.
        self.tags = tags

        # The agency_uri of the creator.
        self.agency_uri = agency_uri

        # The author_uri of the creator.
        self.author_uri = author_uri

        # The time of creation of this event.
        if creation_time is None:
            creation_time = utcdatetime.UTCDateTime()
        self.creation_time = utcdatetime.UTCDateTime(creation_time)


    def write_to_database(self, project):
        ''' Write the event to the pSysmon database.
        '''
        if self.db_id is None:
            # If the db_id is None, insert a new event.
            if self.creation_time is not None:
                creation_time = self.creation_time.isoformat()
            else:
                creation_time = None

            if self.parent is not None:
                catalog_id = self.parent.db_id
            else:
                catalog_id = None

            db_session = project.getDbSession()
            db_event_orm = project.dbTables['event']
            db_event = db_event_orm(ev_catalog_id = catalog_id,
                                    start_time = self.start_time.timestamp,
                                    end_time = self.end_time.timestamp,
                                    public_id = self.public_id,
                                    pref_origin_id = None,
                                    pref_magnitude_id = None,
                                    pref_focmec_id = None,
                                    ev_type = self.event_type,
                                    ev_type_certainty = self.event_type_certainty,
                                    description = self.description,
                                    agency_uri = self.agency_uri,
                                    author_uri = self.author_uri,
                                    creation_time = creation_time
                                   )
            db_session.add(db_event)
            db_session.commit()
            self.db_id = db_event.id
            db_session.close()

        else:
            # If the db_id is not None, update the existing event.
            db_session = project.getDbSession()
            db_event_orm = project.dbTables['event']
            query = db_session.query(db_event_orm).filter(db_event_orm.id == self.db_id)
            if db_session.query(query.exists()):
                db_event = query.scalar()
                if self.parent is not None:
                    db_event.ev_catalog_id = self.parent.db_id
                else:
                    db_event.ev_catalog_id = None
                db_event.start_time = self.start_time.timestamp
                db_event.end_time = self.end_time.timestamp
                db_event.public_id = self.public_id
                #db_event.pref_origin_id = self.pref_origin_id
                #db_event.pref_magnitude_id = self.pref_magnitude_id
                #db_event.pref_focmec_id = self.pref_focmec_id
                db_event.ev_type = self.event_type
                db_event.ev_type_certainty = self.event_type_certainty
                db_event.agency_uri = self.agency_uri
                db_event.author_uri = self.author_uri
                if self.creation_time is not None:
                    db_event.creation_time = self.creation_time.isoformat()
                else:
                    db_event.creation_time = None
                db_session.commit()
                db_session.close()
            else:
                raise RuntimeError("The event with ID=%d was not found in the database.", self.db_id)




class Catalog(object):

    def __init__(self, name, db_id = None, description = None, agency_uri = None,
            author_uri = None, creation_time = None, events = None):
        ''' Instance initialization.
        '''
        # The unique database ID.
        self.db_id = db_id

        # The name of the catalog.
        self.name = name

        # The description of the catalog.
        self.description = description

        # The agency_uri of the creator.
        self.agency_uri = agency_uri

        # The author_uri of the creator.
        self.author_uri = author_uri

        # The time of creation of this event.
        if creation_time is None:
            self.creation_time = utcdatetime.UTCDateTime();
        else:
            self.creation_time = utcdatetime.UTCDateTime(creation_time);

        # The events of the catalog.
        if events is None:
            self.events = []
        else:
            self.events = events


    def add_events(self, events):
        ''' Add one or more events to the events.

        Parameters
        ----------
        events : list of :class:`Event`
            The events to add to the catalog.
        '''
        for cur_event in events:
            cur_event.parent = self
        self.events.extend(events)


    def write_to_database(self, project):
        ''' Write the catalog to the database.

        '''
        if self.db_id is None:
            # If the db_id is None, insert a new catalog.
            if self.creation_time is not None:
                creation_time = self.creation_time.isoformat()
            else:
                creation_time = None

            db_session = project.getDbSession()
            db_catalog_orm = project.dbTables['event_catalog']
            db_catalog = db_catalog_orm(name = self.name,
                                    description = self.description,
                                    agency_uri = self.agency_uri,
                                    author_uri = self.author_uri,
                                    creation_time = creation_time
                                   )
            db_session.add(db_catalog)
            db_session.commit()
            self.db_id = db_catalog.id
            db_session.close()

        else:
            # If the db_id is not None, update the existing event.
            db_session = project.getDbSession()
            db_catalog_orm = project.dbTables['event_catalog']
            query = db_session.query(db_catalog_orm).filter(db_catalog_orm.id == self.db_id)
            if db_session.query(query.exists()):
                db_catalog = query.scalar()

                db_catalog.name = self.name
                db_catalog.description = self.description
                db_catalog.agency_uri = self.agency_uri
                db_catalog.author_uri = self.author_uri
                if self.creation_time is not None:
                    db_catalog.creation_time = self.creation_time.isoformat()
                else:
                    db_catalog.creation_time = None

                db_session.commit()
                db_session.close()
            else:
                raise RuntimeError("The event catalog with ID=%d was not found in the database.", self.db_id)


        # Write or update all events of the catalog to the database.
        for cur_event in self.events:
            cur_event.write_to_database(project)



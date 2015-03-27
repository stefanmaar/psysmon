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
            parent = None, changed = True):
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

        # Flag to indicate a change of the event attributes.
        self.changed = changed


    @property
    def rid(self):
        ''' The resource ID of the event.
        '''
        return '/event/' + str(self.db_id)


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
                                    ev_type_id = None,
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

    @classmethod
    def from_db_event(cls, db_event):
        ''' Convert a database orm mapper event to a event.

        Parameters
        ----------
        db_event : SQLAlchemy ORM
            The ORM of the events database table.
        '''
        event = cls(start_time = db_event.start_time,
                    end_time = db_event.end_time,
                    db_id = db_event.id,
                    public_id = db_event.public_id,
                    event_type = None,
                    event_type_certainty = db_event.ev_type_certainty,
                    description = db_event.description,
                    tags = db_event.tags,
                    agency_uri = db_event.agency_uri,
                    author_uri = db_event.author_uri,
                    creation_time = db_event.creation_time,
                    changed = False
                    )
        return event




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


    def write_to_database(self, project, only_changed_events = True):
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
        for cur_event in [x for x in self.events if x.changed is True]:
            cur_event.write_to_database(project)


    def load_events(self, project, start_time = None, end_time = None, event_id = None):
        ''' Load events from the database.

        The query can be limited using the allowed keyword arguments.

        Parameters
        ----------
        start_time : :class:`obspy.core.utcdatetime.UTCDateTime`
            The begin of the time-span to load.

        end_time : :class:`obspy.core.utcdatetime.UTCDateTime`
            The end of the time-span to load.
        '''
        if project is None:
            raise RuntimeError("The project is None. Can't query the database without a project.")

        db_session = project.getDbSession()
        try:
            events_table = project.dbTables['event']
            query = db_session.query(events_table).\
                    filter(events_table.ev_catalog_id == self.db_id)

            if start_time:
                query = query.filter(events_table.start_time >= start_time.timestamp)

            if end_time:
                query = query.filter(events_table.start_time <= end_time.timestamp)

            if event_id:
                query = query.filter(events_table.id in event_id)

            events_to_add = []
            for cur_orm in query:
                cur_event = Event.from_db_event(cur_orm)
                events_to_add.append(cur_event)
            self.add_events(events_to_add)

        finally:
            db_session.close()


    def clear_events(self):
        ''' Clear the events list.
        '''
        self.events = []


    @classmethod
    def from_db_catalog(cls, db_catalog, load_events = False):
        ''' Convert a database orm mapper catalog to a catalog.

        Parameters
        ----------
        db_catalog : SQLAlchemy ORM
            The ORM of the events catalog database table.

        load_events : Boolean
            If true all events contained in the catalog are loaded
            from the database.
        '''
        catalog = cls(name = db_catalog.name,
                      db_id = db_catalog.id,
                      description = db_catalog.description,
                      agency_uri = db_catalog.agency_uri,
                      author_uri = db_catalog.author_uri,
                      creation_time = db_catalog.creation_time
                      )

        # Add the events to the catalog.
        if load_events is True:
            for cur_db_event in db_catalog.events:
                cur_event = Event.from_db_event(cur_db_event)
                catalog.add_events([cur_event,])
        return catalog




class Library(object):
    ''' Manage a set of event catalogs.
    '''

    def __init__(self, name):
        ''' Initialize the instance.
        '''

        # The name of the library.
        self.name = name

        # The catalogs of the library.
        self.catalogs = {}


    def add_catalog(self, catalog):
        ''' Add one or more catalogs to the library.

        Parameters
        ----------
        catalog : :class:`Catalog` or list of :class:`Catalog`
            The catalog(s) to add to the library.
        '''

        if isinstance(catalog, list):
            for cur_catalog in catalog:
                self.add_catalog(cur_catalog)
        else:
            self.catalogs[catalog.name] = catalog


    def remove_catalog(self, name):
        ''' Remove a catalog from the library.

        Parameters
        ----------
        name : String
            The name of the catalog to remove.

        Returns
        -------
        removed_catalog : :class:`Catalog`
            The removed catalog. None if no catalog was removed.
        '''
        if name in self.catalogs.keys():
            return self.catalogs.pop(name)
        else:
            return None


    def get_catalogs_in_db(self, project):
        ''' Query the available catalogs in the database.

        Parameters
        ----------
        project : :class:`psysmon.core.project.Project`
            The project managing the database.

        Returns
        -------
        catalog_names : List of Strings
            The available catalog names in the database.
        '''
        catalog_names = []
        db_session = project.getDbSession()
        try:
            db_catalog_orm = project.dbTables['event_catalog']
            query = db_session.query(db_catalog_orm)
            if db_session.query(query.exists()):
                catalog_names = [x.name for x in query.order_by(db_catalog_orm.name)]
        finally:
            db_session.close()

        return catalog_names


    def load_catalog_from_db(self, project, name, load_events = False):
        ''' Load catalogs from the database.

        Parameters
        ----------
        project : :class:`psysmon.core.project.Project`
            The project managing the database.

        name : String or list of Strings
            The name of the catalog to load from the database.
        '''
        if isinstance(name, basestring):
            name = [name, ]

        db_session = project.getDbSession()
        try:
            db_catalog_orm = project.dbTables['event_catalog']
            query = db_session.query(db_catalog_orm).filter(db_catalog_orm.name.in_(name))
            if db_session.query(query.exists()):
                for cur_db_catalog in query:
                    cur_catalog = Catalog.from_db_catalog(cur_db_catalog, load_events)
                    self.add_catalog(cur_catalog)
        finally:
            db_session.close()




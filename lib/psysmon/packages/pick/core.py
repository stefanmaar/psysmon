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

import logging
import psysmon
import obspy.core.utcdatetime as utcdatetime


class Catalog(object):

    def __init__(self, name, mode = 'time', description = None,
                 agency_uri = None, author_uri = None, creation_time = None,
                 db_id = None):
        ''' Initialize the instance.
        '''
        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The unique database ID.
        self.db_id = db_id

        # The name of the catalog.
        self.name = name

        # The mode of the catalog ('time', 'amplitude', 'amplitude-range').
        self.mode = mode

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

        # The picks of the catalog.
        self.picks = []


    def add_picks(self, picks):
        ''' Add one or more picks to the picks.

        Parameters
        ----------
        picks : list of :class:`Pick`
            The picks to add to the catalog.
        '''
        for cur_pick in picks:
            cur_pick.parent = self
        self.picks.extend(picks)


    def write_to_database(self, project, only_changed_picks = True):
        ''' Write the catalog to the database.

        '''
        if self.db_id is None:
            # If the db_id is None, insert a new catalog.
            if self.creation_time is not None:
                creation_time = self.creation_time.isoformat()
            else:
                creation_time = None

            db_session = project.getDbSession()
            db_catalog_orm = project.dbTables['pick_catalog']
            db_catalog = db_catalog_orm(name = self.name,
                                        mode = self.mode,
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
            db_catalog_orm = project.dbTables['pick_catalog']
            query = db_session.query(db_catalog_orm).filter(db_catalog_orm.id == self.db_id)
            if db_session.query(query.exists()):
                db_catalog = query.scalar()

                db_catalog.name = self.name
                db_catalog.mode = self.mode
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
        for cur_pick in [x for x in self.picks if x.changed is True]:
            cur_pick.write_to_database(project)


    def load_picks(self, project, start_time = None, end_time = None,
            pick_id = None):
        ''' Load picks from the database.

        The query can be limited using the allowed keyword arguments.

        Parameters
        ----------
        start_time : :class:`obspy.core.utcdatetime.UTCDateTime`
            The begin of the time-span to load.

        end_time : :class:`obspy.core.utcdatetime.UTCDateTime`
            The end of the time-span to load.

        pick_id : Integer
            The database ID of the pick.
        '''
        if project is None:
            raise RuntimeError("The project is None. Can't query the database without a project.")

        db_session = project.getDbSession()
        try:
            pick_table = project.dbTables['pick']
            query = db_session.query(pick_table).\
                    filter(pick_table.ev_catalog_id == self.db_id)

            if start_time:
                query = query.filter(pick_table.start_time >= start_time.timestamp)

            if end_time:
                query = query.filter(pick_table.start_time <= end_time.timestamp)

            if pick_id:
                query = query.filter(pick_table.id in pick_id)

            picks_to_add = []
            for cur_orm in query:
                try:
                    cur_event = Pick.from_db_event(cur_orm)
                    picks_to_add.append(cur_event)
                except:
                    self.logger.exception("Error when creating an event object from database values for event %d. Skipping this event.", cur_orm.id)
            self.add_events(picks_to_add)

        finally:
            db_session.close()


    def clear_picks(self):
        ''' Clear the picks list.
        '''
        self.picks = []


    @classmethod
    def from_orm(cls, catalog_orm, load_picks = False):
        ''' Convert a database orm mapper catalog to a catalog.

        Parameters
        ----------
        catalog_orm : SQLAlchemy ORM
            The ORM of the events catalog database table.

        load_picks : Boolean
            If true all picks contained in the catalog are loaded
            from the database.
        '''
        catalog = cls(name = catalog_orm.name,
                      mode = catalog_orm.mode,
                      db_id = catalog_orm.id,
                      description = catalog_orm.description,
                      agency_uri = catalog_orm.agency_uri,
                      author_uri = catalog_orm.author_uri,
                      creation_time = catalog_orm.creation_time
                      )

        # Add the events to the catalog.
        if load_picks is True:
            for cur_pick_orm in catalog_orm.picks:
                cur_pick = Pick.from_orm(cur_pick_orm)
                catalog.add_picks([cur_pick,])
        return catalog



class Pick(object):

    def __init__(self, label, time, amp1, channel,
                 amp2 = None, first_motion = 0, error = None,
                 agency_uri = None, author_uri = None, creation_time = None,
                 db_id = None, parent = None, changed = True):
        ''' Initialize the instance.
        '''
        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The parent object holding this pick.
        self.parent = parent

        # The unique database id.
        self.db_id = db_id

        # The label of the pick.
        self.label = label

        # The picked time value.
        self.time = time

        # The picked amplitude value.
        self.amp1 = amp1

        # The channel instance with which the pick is associated.
        self.channel = channel

        # The second amplitude value used for amplitude range picking.
        self.amp2 = amp2

        # The first motion assigend to the pick (up: 1, down: -1, undefinded:
        # 0).
        self.first_motion = first_motion

        # The error of the time pick.
        self.error = error

        # The agency_uri of the creator.
        self.agency_uri = agency_uri

        # The author_uri of the creator.
        self.author_uri = author_uri

        # The time of creation of this event.
        if creation_time is None:
            self.creation_time = utcdatetime.UTCDateTime();
        else:
            self.creation_time = utcdatetime.UTCDateTime(creation_time);

        # Flag to indicate a change of the event attributes.
        self.changed = changed

    @property
    def rid(self):
        ''' The resource id of the pick.
        '''
        return '/pick/' + str(self.db_id)


    def write_to_database(self, project):
        ''' Write the pick to the pSysmon database.
        '''
        stream_timebox = self.channel.get_stream(start_time = self.time,
                                                 end_time = self.time)

        if not stream_timebox:
            self.logger.error('No stream in channel %s found for the time pick: %f.', self.channel.scnl, self.time)
            return

        if len(stream_timebox) > 1:
            self.logger.error("More than one stream found for channel %s and time pick %f. This shouldn't happen. Check your geometry database for miss-assigend streams.", self.channel.scnl, self.time)
            return
        else:
            stream = stream_timebox[0].item

        if self.db_id is None:
            # If the db_id is None, insert a new pick.
            if self.creation_time is not None:
                creation_time = self.creation_time.isoformat()
            else:
                creation_time = None

            if self.parent is not None:
                catalog_id = self.parent.db_id
            else:
                catalog_id = None

            db_session = project.getDbSession()
            pick_orm_class = project.dbTables['pick']
            pick_orm = pick_orm_class(catalog_id = catalog_id,
                                      stream_id = stream.id,
                                      label = self.label,
                                      time = self.time.timestamp,
                                      amp1 = self.amp1,
                                      amp2 = self.amp2,
                                      first_motion = self.first_motion,
                                      error = self.error,
                                      agency_uri = self.agency_uri,
                                      author_uri = self.author_uri,
                                      creation_time = creation_time
                                    )
            db_session.add(pick_orm)
            db_session.commit()
            self.db_id = pick_orm.id
            db_session.close()
        else:
            # If the db_id is not None, update the existing pick.
            db_session = project.getDbSession()
            pick_orm_class = project.dbTables['pick']
            query = db_session.query(pick_orm_class).filter(pick_orm_class.id == self.db_id)
            if db_session.query(query.exists()):
                pick_orm = query.scalar()
                if self.parent is not None:
                    pick_orm.ev_catalog_id = self.parent.db_id
                else:
                    pick_orm.ev_catalog_id = None
                pick_orm.stream_id = stream.id
                pick_orm.label = self.label
                pick_orm.time = self.time.timestamp
                pick_orm.amp1 = self.amp1
                pick_orm.amp2 = self.amp2
                pick_orm.first_motion = self.first_motion
                pick_orm.error = self.error
                pick_orm.agency_uri = self.agency_uri
                pick_orm.author_uri = self.author_uri
                if self.creation_time is not None:
                    pick_orm.creation_time = self.creation_time.isoformat()
                else:
                    pick_orm.creation_time = None
                db_session.commit()
                db_session.close()
            else:
                raise RuntimeError("The event with ID=%d was not found in the database.", self.db_id)




    def from_orm(cls, pick_orm):
        ''' Convert a database orm mapper pick to a pick instance.

        Parameters
        ----------
        pick_orm : SQLAlchemy ORM
            The ORM of the pick database table.
        '''
        pass

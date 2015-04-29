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
import warnings
import numpy as np



class Library(object):
    ''' Manage a set of pick catalogs.
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
            catalog_orm_class = project.dbTables['pick_catalog']
            query = db_session.query(catalog_orm_class)
            if db_session.query(query.exists()):
                catalog_names = [x.name for x in query.order_by(catalog_orm_class.name)]
        finally:
            db_session.close()

        return catalog_names


    def load_catalog_from_db(self, project, name, load_picks = False):
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
            catalog_orm_class = project.dbTables['pick_catalog']
            query = db_session.query(catalog_orm_class).filter(catalog_orm_class.name.in_(name))
            if db_session.query(query.exists()):
                for cur_orm in query:
                    cur_catalog = Catalog.from_orm(cur_orm, load_picks)
                    self.add_catalog(cur_catalog)
        finally:
            db_session.close()


    def clear(self):
        ''' Remove all catalogs.
        '''
        self.catalogs = {}




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


    def get_pick(self, start_time = None, end_time = None, station = None, **kwargs):
        ''' Get picks from the catalog.

        Parameters
        ----------
        id : Integer
            The unique ID of the pick.

        label : String
            The label of the pick.

        start_time : UTDDateTime
            The start time of the time window to search.

        end_time: UTCDateTime.
            The end time of the time window to search.

        station : String
            The name of the station to which the pick is assigned to.
        '''
        ret_picks = self.picks

        valid_keys = ['id', 'label']

        for cur_key, cur_value in kwargs.iteritems():
            if cur_key in valid_keys:
                ret_picks = [x for x in ret_picks if getattr(x, cur_key) == cur_value]
            else:
                warnings.warn('Search attribute %s is not existing.' % cur_key, RuntimeWarning)

        if start_time is not None:
            ret_picks = [x for x in ret_picks if x.time >= start_time]

        if end_time is not None:
            ret_picks = [x for x in ret_picks if x.time <= end_time]

        if station is not None:
            ret_picks = [x for x in ret_picks if x.channel.parent_station.name == station]

        return ret_picks


    def get_nearest_pick(self, pick_time, **kwargs):
        ''' Get the pick nearest to the specified pick time.
        '''
        picks = self.get_pick(**kwargs)
        nearest_pick = None
        if picks:
            nearest_pick = picks[0]
            dist = np.abs(pick_time - nearest_pick.time)
            for cur_pick in picks[1:]:
                cur_dist = np.abs(pick_time - cur_pick.time)
                if cur_dist < dist:
                    dist = cur_dist
                    nearest_pick = cur_pick

        return nearest_pick


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
                    filter(pick_table.catalog_id == self.db_id)

            if start_time:
                query = query.filter(pick_table.time >= start_time.timestamp)

            if end_time:
                query = query.filter(pick_table.time <= end_time.timestamp)

            if pick_id:
                query = query.filter(pick_table.id in pick_id)

            picks_to_add = []
            for cur_orm in query:
                try:
                    cur_pick = Pick.from_orm(cur_orm, inventory = project.geometry_inventory)
                    picks_to_add.append(cur_pick)
                except:
                    self.logger.exception("Error when creating an pick object from database values for pick %d. Skipping this pick.", cur_orm.id)
            self.add_picks(picks_to_add)

        finally:
            db_session.close()

    def delete_picks_from_db(self, project, picks):
        ''' Delete picks from the database and the catalog.
        '''
        for cur_pick in picks:
            res = cur_pick.delete_from_db(project = project)
            if res == 1:
                self.picks.remove(cur_pick)


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


    def delete_from_db(self, project):
        ''' Delete a pick from the database.
        '''
        pick_orm_class = project.dbTables['pick']
        result = project.dbEngine.execute(pick_orm_class.__table__.delete().where(pick_orm_class.id == self.db_id))
        return result.rowcount


    @classmethod
    def from_orm(cls, pick_orm, inventory = None):
        ''' Convert a database orm mapper pick to a pick instance.

        Parameters
        ----------
        pick_orm : SQLAlchemy ORM
            The ORM of the pick database table.
        '''
        if inventory is None:
            channel = None
        else:
            channel = inventory.get_channel_from_stream(name = pick_orm.stream.name,
                                                       serial = pick_orm.stream.parent.serial,
                                                       start_time = utcdatetime.UTCDateTime(pick_orm.time),
                                                       end_time = utcdatetime.UTCDateTime(pick_orm.time))
            if channel:
                if len(channel) == 1:
                    channel = channel[0]
                else:
                    channel = None
            else:
                channel = None

        pick = cls(db_id = pick_orm.id,
                   channel = channel,
                   label = pick_orm.label,
                   time = utcdatetime.UTCDateTime(pick_orm.time),
                   amp1 = pick_orm.amp1,
                   amp2 = pick_orm.amp2,
                   first_motion = pick_orm.first_motion,
                   error = pick_orm.error,
                   agency_uri = pick_orm.agency_uri,
                   author_uri = pick_orm.author_uri,
                   creation_time = utcdatetime.UTCDateTime(pick_orm.creation_time)
                  )


        return pick

# -*- coding: utf-8 -*-
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
''' Event detection.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

'''
#from profilehooks import profile

import logging
import warnings


import numpy as np
import scipy.signal
import obspy.core.utcdatetime as utcdatetime

import psysmon
import psysmon.core.lib_signal as lib_signal
import psysmon.packages.event.lib_detect_sta_lta as lib_detect_sta_lta


class Detection(object):
    ''' A detection of a signal on a timeseries.
    '''
    def __init__(self, start_time, end_time, db_id = None, rec_stream_id = None, catalog_id = None,
                 method = None, agency_uri = None, author_uri = None, creation_time = None,
                 parent = None, changed = True):
        ''' Initialize the instance.
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

        # The parent object holding this event. Most likely this is a detection
        # Catalog instance or an event instance.
        self.parent = parent

        # The unique database id.
        self.db_id = db_id

        # The recorder stream id on which the detection was made.
        self.rec_stream_id = rec_stream_id

        # The channel matching the rec_stream_id. This is loaded only if a
        self.channel = None

        # The catalog id to which the detection belongs.
        self.catalog_id = catalog_id

        # The start time of the event.
        self.start_time = utcdatetime.UTCDateTime(start_time)

        # The end time of the event.
        self.end_time = utcdatetime.UTCDateTime(end_time)

        # The detection method.
        self.method = None

        # The agency_uri of the creator.
        self.agency_uri = agency_uri

        # The author_uri of the creator.
        self.author_uri = author_uri

        # The time of creation of this event.
        if creation_time is None:
            creation_time = utcdatetime.UTCDateTime()
        self.creation_time = utcdatetime.UTCDateTime(creation_time)

        # Flag to indicate a change of the detection attributes.
        self.changed = changed

    @property
    def rid(self):
        ''' The resource ID of the detection.
        '''
        return '/event/' + str(self.db_id)


    @property
    def start_time_string(self):
        ''' The string representation of the start time.
        '''
        return self.start_time.isoformat()


    @property
    def end_time_string(self):
        ''' The string representation of the end time.
        '''
        return self.end_time.isoformat()


    @property
    def length(self):
        ''' The length of the detection in seconds.
        '''
        return self.end_time - self.start_time

    @property
    def scnl(self):
        ''' The SCNL code of the related channel.
        '''
        if self.channel is None:
            return None
        else:
            return self.channel.scnl


    @property
    def snl(self):
        ''' The SCNL code of the related channel.
        '''
        if self.channel is None:
            return None
        else:
            return (self.channel.scnl[0], self.channel.scnl[2], self.channel.scnl[3])


    def set_channel_from_inventory(self, inventory):
        ''' Set the channel matching the recorder stream.
        '''
        self.channel = inventory.get_channel_from_stream(start_time = self.start_time,
                                                         end_time = self.end_time)


    def write_to_database(self, project):
        ''' Write the detection to the pSysmon database.
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
            db_detection_orm = project.dbTables['detection']
            db_detection = db_detection_orm(catalog_id = catalog_id,
                                            rec_stream_id = self.rec_stream_id,
                                            start_time = self.start_time.timestamp,
                                            end_time = self.end_time.timestamp,
                                            method = self.method,
                                            agency_uri = self.agency_uri,
                                            author_uri = self.author_uri,
                                            creation_time = creation_time)
            db_session.add(db_detection)
            db_session.commit()
            self.db_id = db_detection.id
            db_session.close()

        else:
            # If the db_id is not None, update the existing event.
            db_session = project.getDbSession()
            db_detection_orm = project.dbTables['detection']
            query = db_session.query(db_detection_orm).filter(db_detection_orm.id == self.db_id)
            if db_session.query(query.exists()):
                db_detection = query.scalar()
                if self.parent is not None:
                    db_detection.catalog_id = self.parent.db_id
                else:
                    db_detection.catalog_id = None
                db_detection.rec_stream_id = self.rec_stream_id
                db_detection.start_time = self.start_time.timestamp
                db_detection.end_time = self.end_time.timestamp
                db_detection.method = self.method
                db_detection.agency_uri = self.agency_uri
                db_detection.author_uri = self.author_uri
                if self.creation_time is not None:
                    db_detection.creation_time = self.creation_time.isoformat()
                else:
                    db_detection.creation_time = None
                db_session.commit()
                db_session.close()
            else:
                raise RuntimeError("The detection with ID=%d was not found in the database.", self.db_id)

    def get_db_orm(self, project):
        ''' Get an orm representation to use it for bulk insertion into
        the database.
        '''
        db_detection_orm = project.dbTables['detection']

        if self.creation_time is not None:
            creation_time = self.creation_time.isoformat()
        else:
            creation_time = None

        if self.parent is not None:
            catalog_id = self.parent.db_id
        else:
            catalog_id = None

        labels = ['catalog_id', 'rec_stream_id',
                  'start_time', 'end_time',
                  'method', 'agency_uri',
                  'author_uri', 'creation_time']
        db_dict = dict(zip(labels,
                           (catalog_id,
                            self.rec_stream_id,
                            self.start_time.timestamp,
                            self.end_time.timestamp,
                            self.method,
                            self.agency_uri,
                            self.author_uri,
                            creation_time)))
        db_detection = db_detection_orm(**db_dict)
        db_detection.id = self.db_id
        return db_detection

    @classmethod
    def from_db_detection(cls, detection_orm):
        ''' Convert a database orm mapper detection to a detection.

        Parameters
        ----------
        detection_orm : SQLAlchemy ORM
            The ORM of the detection_orm database table.
        '''
        detection = cls(start_time = detection_orm.start_time,
                        end_time = detection_orm.end_time,
                        db_id = detection_orm.id,
                        rec_stream_id = detection_orm.rec_stream_id,
                        catalog_id = detection_orm.catalog_id,
                        method = detection_orm.method,
                        agency_uri = detection_orm.agency_uri,
                        author_uri = detection_orm.author_uri,
                        creation_time = detection_orm.creation_time)
        return detection



class Catalog(object):
    ''' A detection catalog.
    '''

    def __init__(self, name, db_id = None, description = None, agency_uri = None,
            author_uri = None, creation_time = None, detections = None):
        ''' Instance initialization.
        '''
        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

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

        # The detections of the catalog.
        if detections is None:
            self.detections = []
        else:
            self.events = detections


    def add_detections(self, detections):
        ''' Add one or more detections to the catalog.

        Parameters
        ----------
        detections : list of :class:`Detection`
            The detections to add to the catalog.
        '''
        # Check for potential duplicates.
        # TODO: add a compare method for the detection class.
        db_ids = [x.db_id for x in self.detections]
        detections = [x for x in detections if x.db_id is None or x.db_id not in db_ids]

        for cur_detection in detections:
            cur_detection.parent = self
        self.detections.extend(detections)


    def remove_detections(self, detections):
        ''' Remove the detections from the catalog.

        Parameters
        ----------
        detections : list of :class:`Detection`
            The detections to add to the catalog.
        '''
        for cur_detection in detections:
            if cur_detection in self.detections:
                self.detections.remove(cur_detection)


    def get_detections(self, start_time = None, end_time = None,
                       start_inside = False, end_inside = False, **kwargs):
        ''' Get detections using search criteria passed as keywords.

        Parameters
        ----------
        start_time : class:`~obspy.core.utcdatetime.UTCDateTime`
            The minimum starttime of the detections.

        end_time : class:`~obspy.core.utcdatetime.UTCDateTime`
            The maximum end_time of the detections.

        start_inside : Boolean
            If True, select only those detection with a start time
            inside the search window.

        end_inside : Boolean
            If True, select only those detection with an end time
            inside the search window.

        scnl : tuple of Strings
            The scnl code of the channel (e.g. ('GILA, 'HHZ', 'XX', '00')).
        '''
        ret_detections = self.detections

        valid_keys = ['scnl']

        for cur_key, cur_value in kwargs.iteritems():
            if cur_key in valid_keys:
                ret_detections = [x for x in ret_detections if getattr(x, cur_key) == cur_value]
            else:
                warnings.warn('Search attribute %s is not existing.' % cur_key, RuntimeWarning)

        if start_time is not None:
            if start_inside:
                ret_detections = [x for x in ret_detections if (x.end_time is None) or (x.start_time >= start_time)]
            else:
                ret_detections = [x for x in ret_detections if (x.end_time is None) or (x.end_time > start_time)]

        if end_time is not None:
            if end_inside:
                ret_detections = [x for x in ret_detections if x.end_time <= end_time]
            else:
                ret_detections = [x for x in ret_detections if x.start_time < end_time]

        return ret_detections


    def assign_channel(self, inventory):
        ''' Set the channels according to the rec_stream_ids.
        '''
        # Get the unique stream ids.
        id_list = [x.rec_stream_id for x in self.detections]
        id_list = list(set(id_list))
        # Get the channels for the ids.
        channels = [inventory.get_channel_from_stream(id = x) for x in id_list]
        channels = [x[0] if len(x) == 1 else None for x in channels]
        channels = dict(zip(id_list, channels))

        for cur_detection in self.detections:
            cur_detection.channel = channels[cur_detection.rec_stream_id]


    #@profile(immediate=True)
    def load_detections(self, project, start_time = None, end_time = None,
                        min_detection_length = None):
        ''' Load detections from the database.

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
            detection_table = project.dbTables['detection']
            query = db_session.query(detection_table).\
                    filter(detection_table.catalog_id == self.db_id).\
                    filter(detection_table.end_time > detection_table.start_time)

            if start_time:
                query = query.filter(detection_table.start_time >= start_time.timestamp)

            if end_time:
                query = query.filter(detection_table.start_time <= end_time.timestamp)

            if min_detection_length:
                query = query.filter(detection_table.end_time - detection_table.start_time >= min_detection_length)

            detections_to_add = []
            for cur_orm in query:
                try:
                    cur_detection = Detection.from_db_detection(cur_orm)
                    detections_to_add.append(cur_detection)
                except:
                    self.logger.exception("Error when creating a detection object from database values for detection id %d. Skipping this detection.", cur_orm.id)
            self.add_detections(detections_to_add)

        finally:
            db_session.close()


    def clear_detections(self):
        ''' Clear the detections list.
        '''
        self.detections = []


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
            db_catalog_orm = project.dbTables['detection_catalog']
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
            # If the db_id is not None, update the existing catalog.
            db_session = project.getDbSession()
            db_catalog_orm = project.dbTables['detection_catalog']
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
                raise RuntimeError("The detection catalog with ID=%d was not found in the database.", self.db_id)


        # Write or update all detections of the catalog to the database.
        for cur_detection in [x for x in self.detections if x.changed is True]:
            cur_detection.write_to_database(project)



    @classmethod
    def from_db_catalog(cls, db_catalog, load_detections = False):
        ''' Convert a database orm mapper catalog to a catalog.

        Parameters
        ----------
        db_catalog : SQLAlchemy ORM
            The ORM of the events catalog database table.

        load_detections : Boolean
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

        # Add the detections to the catalog.
        if load_detections is True:
            for cur_detection_orm in db_catalog.detections:
                cur_detection = Detection.from_db_detection(cur_detection_orm)
                catalog.add_detections([cur_detection,])
        return catalog



class Library(object):
    ''' Manage detection catalogs.
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
        if name in self.catalogs.iterkeys():
            return self.catalogs.pop(name)
        else:
            return None


    def clear(self):
        ''' Remove all catalogs.
        '''
        self.catalogs = {}


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
            db_catalog_orm = project.dbTables['detection_catalog']
            query = db_session.query(db_catalog_orm)
            if db_session.query(query.exists()):
                catalog_names = [x.name for x in query.order_by(db_catalog_orm.name)]
        finally:
            db_session.close()

        return catalog_names


    def load_catalog_from_db(self, project, name, load_detections = False):
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
            db_catalog_orm = project.dbTables['detection_catalog']
            query = db_session.query(db_catalog_orm).filter(db_catalog_orm.name.in_(name))
            if db_session.query(query.exists()):
                for cur_db_catalog in query:
                    cur_catalog = Catalog.from_db_catalog(cur_db_catalog, load_detections)
                    self.add_catalog(cur_catalog)
        finally:
            db_session.close()


class StaLtaDetector(object):
    ''' Run a standard STA/LTA Detection.
    '''

    def __init__(self, data = None, cf_type = 'square', n_sta = 2,
                 n_lta = 10, thr = 3, fine_thr = None, turn_limit = 0.05,
                 stop_growth = 0.001):
        ''' Initialize the instance.
        '''
        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The type of the characteristic function.
        self.allowed_cf_type = ['abs', 'square', 'envelope', 'envelope^2']
        if cf_type not in self.allowed_cf_type:
            raise ValueError("Wrong value for cf_type. Allowed are: %s." % self.allowed_cf_type)
        self.cf_type = cf_type

        # The length of the STA in samples.
        self.n_sta = n_sta

        # The length of the LTA in samples.
        self.n_lta = n_lta

        # The threshold of the STA/LTA ratio when to declare the begin of an
        # event.
        self.thr = thr

        # The fine threshold of the STA/LTA ratio used to refine an already
        # detected event start.
        if fine_thr is None:
            self.fine_thr = self.thr
        else:
            self.fine_thr = fine_thr

        # The turning limit when to stop the event begin refinement if the fine_thr is
        # not reached.
        self.turn_limit = turn_limit

        # The ratio with which the stop_value is grown to ensure the reaching
        # of the stop criterium.
        self.stop_growth = stop_growth

        # The data array.
        if data is None:
            self.data = np.empty((0,0))
        else:
            self.data = data

        # The computed STA/LTA data.
        self.cf = np.empty((0,0))
        self.sta = np.empty((0,0))
        self.lta = np.empty((0,0))
        self.valid_ind = None


    def set_data(self, data):
        ''' Set the data array an clear all related features.
        '''
        self.data = data

        self.cf = np.empty((0,0))
        self.sta = np.empty((0,0))
        self.lta = np.empty((0,0))
        self.valid_ind = None



    def compute_cf(self):
        ''' Compute the characteristic function.
        '''
        if self.cf_type not in self.allowed_cf_type:
            raise ValueError("Wrong value for cf_type. Allowed are: %s." % self.allowed_cf_type)

        if self.cf_type == 'abs':
            self.cf = np.abs(self.data)
        elif self.cf_type == 'square':
            self.cf = self.data**2
        elif self.cf_type == 'envelope':
            data_comp = scipy.signal.hilbert(self.data)
            self.cf = np.sqrt(np.real(data_comp)**2 + np.imag(data_comp)**2)
        elif self.cf_type == 'envelope^2':
            data_comp = scipy.signal.hilbert(self.data)
            self.cf = np.sqrt(np.real(data_comp)**2 + np.imag(data_comp)**2)
            self.cf = self.cf ** 2


    def compute_sta_lta(self):
        ''' Compute the STA and LTA function.

        '''
        clib_signal = lib_signal.clib_signal

        n_cf = len(self.cf)
        cf = np.ascontiguousarray(self.cf, dtype = np.float64)
        self.sta = np.empty(n_cf, dtype = np.float64)
        ret_val = clib_signal.moving_average(n_cf, self.n_sta, cf, self.sta)
        self.lta = np.empty(n_cf, dtype = np.float64)
        ret_val = clib_signal.moving_average(n_cf, self.n_lta, cf, self.lta)

        # Use non-overlapping STA and LTA windows. The LTA is computed using
        # samples prior to the STA window.
        self.lta[self.n_sta:] = self.lta[:-self.n_sta]
        self.lta[:self.n_sta] = 0.

        # Set the index from which on the STA/LTA is valid.
        self.valid_ind = self.n_lta + self.n_sta


    def compute_event_limits(self, stop_delay = 0):
        ''' Compute the event start and end times based on the detection functions.

        '''
        self.stop_crit = np.zeros(self.sta.shape)
        self.replace_limits = []
        event_marker = []
        self.lta_orig = self.lta.copy()

        # Find the event begins indicated by exceeding the threshold value.
        # Start after n_lta samples to avoid effects of the filter buildup.
        event_start, stop_value = self.compute_start_stop_values(self.valid_ind, stop_delay)
        self.logger.debug("First event_start: %d.", event_start)

        # Find the event end values.
        self.logger.debug("Computing the event limits.")

        while event_start < (len(self.sta) - 1):
            self.logger.debug("Processing the next event. event_start_ind: %d", event_start)
            if self.sta[event_start] <= stop_value:
                stop_value = self.sta[event_start]

            # Start the search for the event end one sample after the event
            # start to avoid eventual problems with identical event_start
            # and event end.
            cur_search_start = event_start + 1

            # TODO: Use a loop in a C function do compute the event stop.
            # Using the complete array is not efficient when processing
            # long arrays.
            clib_detect = lib_detect_sta_lta.clib_detect_sta_lta
            cur_sta = np.ascontiguousarray(self.sta[cur_search_start:], dtype = np.float64)
            cur_lta = np.ascontiguousarray(self.lta[cur_search_start:], dtype = np.float64)
            cur_lta = cur_lta * self.thr
            n_cur_sta = len(cur_sta)
            n_cur_lta = len(cur_lta)
            cur_stop_crit = np.empty(n_cur_sta, dtype = np.float64)
            next_end_ind = clib_detect.compute_event_end(n_cur_sta, cur_sta, n_cur_lta, cur_lta, stop_value, cur_stop_crit, self.stop_growth)
            self.logger.debug("next_end_ind: %d", next_end_ind)

            # Compute the event end.
            if next_end_ind == -1:
                cur_event_end = np.nan
                self.stop_crit[cur_search_start:] = cur_stop_crit
            else:
                cur_event_end = cur_search_start + next_end_ind

                # Copy the event stop criterium to the overall stop criterium array.
                self.stop_crit[cur_search_start:cur_event_end] = cur_stop_crit[:next_end_ind]

                # Remove the influence of the detected event from the LTA
                # timeseries.
                self.remove_event_influence(event_start, cur_event_end)

            # Add the event marker.
            # TODO: add the lta length to the event limits. Adapt the
            # tracedisplay view accordingly.
            event_marker.append((event_start, cur_event_end))

            # Recompute the next event start indices.
            if np.isnan(cur_event_end):
                # There is no event end before the end of the data. Stop the
                # loop.
                break
            else:
                event_start, stop_value = self.compute_start_stop_values(cur_event_end, stop_delay)

        self.logger.debug("Finished the event limits computation.")

        return event_marker


    def remove_event_influence(self, event_start, event_end):
        ''' Remove the influence of the detected event from the LTA.
        '''
        event_lta = self.compute_replace_lta(event_start, event_end)

        # Remove the event lta from the LTA timeseries.
        event_length = event_end - event_start
        lta_replace_start = event_start + self.n_sta
        lta_replace_end = lta_replace_start + event_length + self.n_lta
        if lta_replace_start < len(self.lta):
            if lta_replace_end > len(self.lta):
                lta_replace_end = len(self.lta)
                event_lta = event_lta[:lta_replace_end - lta_replace_start]
            self.lta[lta_replace_start:lta_replace_end] -= event_lta
            self.replace_limits.append((lta_replace_start, lta_replace_end))
        else:
            self.logger.warning("The LTA replacement start is after the trace length. Didn't change the LTA.")


    def compute_replace_lta(self, event_start, event_end):
        ''' Compute the moving average used to remove the event influence on the LTA.
        '''
        # Compute the LTA moving average of the event cf only.
        event_length = event_end - event_start
        event_cf = np.zeros(2*self.n_lta + event_length)
        event_cf[self.n_lta:self.n_lta + event_length] = self.cf[event_start:event_end]
        c_event_cf = np.ascontiguousarray(event_cf, dtype = np.float64)
        n_event_cf = len(event_cf)
        event_lta = np.empty(n_event_cf, dtype = np.float64)
        ret_val = lib_signal.clib_signal.moving_average(n_event_cf, self.n_lta, c_event_cf, event_lta)
        noise_cf = np.zeros(event_cf.shape)
        noise_cf[self.n_lta:self.n_lta + event_length] = self.lta[event_start]
        c_noise_cf = np.ascontiguousarray(noise_cf, dtype = np.float64)
        n_noise_cf = len(noise_cf)
        noise_lta = np.empty(n_event_cf, dtype = np.float64)
        ret_val = lib_signal.clib_signal.moving_average(n_noise_cf, self.n_lta, c_noise_cf, noise_lta)
        event_lta = event_lta[self.n_lta:] - noise_lta[self.n_lta:]

        return event_lta


    def compute_start_stop_values(self, crop_start, stop_delay):
        ''' Compute the event start indices and the stop values.
        '''
        clib_detect = lib_detect_sta_lta.clib_detect_sta_lta

        thrf = np.ascontiguousarray(self.sta[crop_start:]/self.lta[crop_start:], dtype = np.float64)
        event_start = clib_detect.compute_event_start(len(thrf), thrf, self.thr, self.fine_thr, self.turn_limit)

        event_start_ind = crop_start + event_start

        # Use a sta value stop_delay samples prior to the event start to take
        # the delayed reaction of the detector into account.
        stop_value = self.sta[event_start_ind - stop_delay]

        # Reset stop values larger than the STA value of the event start.
        if stop_value > self.sta[event_start_ind]:
            stop_value = self.sta[event_start_ind]

        return event_start_ind, stop_value



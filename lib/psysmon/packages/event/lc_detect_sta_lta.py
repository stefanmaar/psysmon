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

from __future__ import division
from builtins import str
from past.utils import old_div
import numpy as np
import obspy.core.utcdatetime as utcdatetime

import psysmon.core.packageNodes as package_nodes
import psysmon.core.preferences_manager as preferences_manager
import psysmon.core.gui_preference_dialog as gui_preference_dialog
import psysmon.packages.event.detect as detect


class StaLtaDetection(package_nodes.LooperCollectionChildNode):
    ''' Detect events using STA/LTA algorithm.

    '''
    name = 'STA/LTA detection'
    mode = 'looper child'
    category = 'Detection'
    tags = ['development', 'looper child', 'event', 'detect']

    def __init__(self, **args):
        ''' Initialize the instance.
        '''
        package_nodes.LooperCollectionChildNode.__init__(self, **args)

        # The available detection catalogs.
        self.catalogs = []

        # Override the lta_length preference.
        self._pre_stream_length = None

        # The start times of events with no end found before the trace end.
        self.open_end_start = {}

        self.create_preferences()

    @property
    def pre_stream_length(self):
        ''' The time-span needed for correct processing prior to the start time
        of the stream passed to the execute method [s].
        '''
        if self._pre_stream_length is not None:
            return self._pre_stream_length
        else:
            return self.pref_manager.get_value('lta_length')


    def create_preferences(self):
        ''' Create the collection node preferences.
        '''
        pref_page = self.pref_manager.add_page('Preferences')
        gen_group = pref_page.add_group('general')
        thr_group = pref_page.add_group('threshold')
        sc_group = pref_page.add_group('stop criterium')

        out_page = self.pref_manager.add_page('Output')
        cat_group = out_page.add_group('catalog')


        # The CF type.
        item = preferences_manager.SingleChoicePrefItem(name = 'cf_type',
                                                        label = 'cf type',
                                                        limit = ('abs', 'square', 'envelope', 'envelope^2'),
                                                        value = 'square',
                                                        tool_tip = 'The type of the characteristic function.'
                                                       )
        gen_group.add_item(item)


        # STA length
        item = preferences_manager.FloatSpinPrefItem(name = 'sta_length',
                                                     label = 'STA length [s]',
                                                     value = 1,
                                                     limit = (0, 3600))
        gen_group.add_item(item)


        # LTA length
        item = preferences_manager.FloatSpinPrefItem(name = 'lta_length',
                                                     label = 'LTA length [s]',
                                                     value = 5,
                                                     limit = (0, 3600))
        gen_group.add_item(item)


        # Threshold value
        item = preferences_manager.FloatSpinPrefItem(name = 'thr',
                                                     label = 'Threshold',
                                                     value = 3,
                                                     limit = (0, 100))
        thr_group.add_item(item)

        # Fine threshold value
        item = preferences_manager.FloatSpinPrefItem(name = 'fine_thr',
                                                     label = 'Fine threshold',
                                                     value = 2,
                                                     limit = (0, 100))
        thr_group.add_item(item)

        # Turn limit.
        item = preferences_manager.FloatSpinPrefItem(name = 'turn_limit',
                                                     label = 'turn limit',
                                                     value = 0.05,
                                                     limit = (0, 10))
        thr_group.add_item(item)


        # stop growth
        item = preferences_manager.FloatSpinPrefItem(name = 'stop_growth',
                                                     label = 'stop grow ratio',
                                                     value = 0.001,
                                                     digits = 5,
                                                     limit = (0, 0.1))
        sc_group.add_item(item)

        # Stop criterium delay.
        item = preferences_manager.FloatSpinPrefItem(name = 'stop_delay',
                                                     label = 'Stop delay [s]',
                                                     value = 0.1,
                                                     limit = (0, 100),
                                                     tool_tip = 'The time prepend to the triggered event start to set the initial value of the stop criterium.')
        sc_group.add_item(item)


        # The target detection catalog.
        item = preferences_manager.SingleChoicePrefItem(name = 'detection_catalog',
                                                        label = 'detection catalog',
                                                        limit = [],
                                                        value = None,
                                                        tool_tip = 'The detection catalog to which the detections are written.'
                                                       )
        cat_group.add_item(item)


    def edit(self):
        ''' Create the preferences edit dialog.
        '''
        # Initialize the detection_catalog preference item.
        self.load_catalogs()
        catalog_names = [x.name for x in self.catalogs]
        self.pref_manager.set_limit('detection_catalog', catalog_names)
        if catalog_names:
            if self.pref_manager.get_value('detection_catalog') not in catalog_names:
                self.pref_manager.set_value('detection_catalog', catalog_names[0])


        # Create the edit dialog.
        dlg = gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)

        # Enable/Disable the gui elements based on the pref_manager settings.
        #self.on_select_individual()

        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, stream, process_limits = None, origin_resource = None, **kwargs):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        self.logger.debug("stream: %s", str(stream))
        self.logger.debug("process_limits: %s", process_limits)

        # Get the detection parameters.
        sta_len = self.pref_manager.get_value('sta_length')
        lta_len = self.pref_manager.get_value('lta_length')
        thr = self.pref_manager.get_value('thr')
        fine_thr = self.pref_manager.get_value('fine_thr')
        turn_limit = self.pref_manager.get_value('turn_limit')
        cf_type = self.pref_manager.get_value('cf_type')
        stop_delay = self.pref_manager.get_value('stop_delay')
        stop_growth = self.pref_manager.get_value('stop_growth')

        # Get the selected catalog id.
        catalog_name = self.pref_manager.get_value('detection_catalog')
        self.load_catalogs()
        selected_catalog = [x for x in self.catalogs if x.name == catalog_name]
        if len(selected_catalog) == 0:
            raise RuntimeError("No detection catalog found with name %s in the database.", catalog_name)
        elif len(selected_catalog) > 1:
            raise RuntimeError("Multiple detection catalogs found with name %s: %s.", catalog_name, selected_catalog)
        else:
            selected_catalog = selected_catalog[0]

        # Initialize the detector.
        detector = detect.StaLtaDetector(thr = thr, cf_type = cf_type, fine_thr = fine_thr,
                                         turn_limit = turn_limit, stop_growth = stop_growth)

        # The list to store the data to be inserted into the database.
        db_data = []

        # Detect the events using the STA/LTA detector.
        for cur_trace in stream:
            # Check for open_end events and slice the data to the stored event
            # start. If no open_end event is found. slice the trace to the
            # original pre_stream_length.
            if cur_trace.id in iter(self.open_end_start.keys()):
                cur_oe_start = self.open_end_start.pop(cur_trace.id)
                cur_trace = cur_trace.slice(starttime = cur_oe_start)
                self.logger.debug("Sliced the cur_trace to the open_end start. cur_trace: %s.", cur_trace)
            else:
                cur_trace = cur_trace.slice(starttime = process_limits[0] - lta_len)
                self.logger.debug("Sliced the cur_trace to the original pre_stream_length. cur_trace: %s.", cur_trace)

            time_array = np.arange(0, cur_trace.stats.npts)
            time_array = old_div(time_array * 1,cur_trace.stats.sampling_rate)
            time_array = time_array + cur_trace.stats.starttime.timestamp

            # Check if the data is a ma.maskedarray
            if np.ma.count_masked(cur_trace.data):
                try:
                    time_array = np.ma.array(time_array, mask=cur_trace.data.mask)
                except:
                    time_array = np.ma.array(time_array[:-1], mask=cur_trace.data.mask)

            n_sta = int(sta_len * cur_trace.stats.sampling_rate)
            n_lta = int(lta_len * cur_trace.stats.sampling_rate)
            stop_delay_smp = int(stop_delay * cur_trace.stats.sampling_rate)

            detector.n_sta = n_sta
            detector.n_lta = n_lta
            detector.set_data(cur_trace.data)
            detector.compute_cf()
            detector.compute_sta_lta()
            detection_markers = detector.compute_event_limits(stop_delay = stop_delay_smp)
            self.logger.debug("detection_markers: %s", detection_markers)

            # Check if the last event has no end. Change the pre_stream_length
            # to request more data for the next time window loop.
            last_marker = []
            if len(detection_markers) > 0 and np.isnan(detection_markers[-1][1]):
                # Handle a detected event with no end.
                last_marker = detection_markers.pop(-1)
                slice_marker = last_marker[0] - detector.n_lta - detector.n_sta - 1
                if slice_marker < 0:
                    slice_marker = 0
                cur_pre_length = (len(detector.data) - slice_marker) * cur_trace.stats.delta

                self.open_end_start[cur_trace.id] = utcdatetime.UTCDateTime(time_array[slice_marker])

                if self._pre_stream_length is None:
                    self._pre_stream_length = cur_pre_length
                elif cur_pre_length > self._pre_stream_length:
                    self._pre_stream_length = cur_pre_length

            # Get the database recorder stream id.
            try:
                cur_channel = self.project.geometry_inventory.get_channel(station = cur_trace.stats.station,
                                                                          name = cur_trace.stats.channel,
                                                                          network = cur_trace.stats.network,
                                                                          location = cur_trace.stats.location)[0]
                cur_timebox = cur_channel.get_stream(start_time = process_limits[0], end_time = process_limits[0])[0]
                cur_stream_id = cur_timebox.item.id
            except:
                cur_stream_id = None

            # Write the detections to the database.
            detection_table = self.project.dbTables['detection']
            for det_start_ind, det_end_ind in detection_markers:
                det_start_time = time_array[det_start_ind]
                det_end_time = time_array[det_end_ind]
                cur_orm = detection_table(catalog_id = selected_catalog.id,
                                          rec_stream_id = cur_stream_id,
                                          start_time = det_start_time,
                                          end_time = det_end_time,
                                          method = self.name_slug,
                                          agency_uri = self.project.activeUser.agency_uri,
                                          author_uri = self.project.activeUser.author_uri,
                                          creation_time = utcdatetime.UTCDateTime().isoformat())
                db_data.append(cur_orm)

        if db_data:
            try:
                db_session = self.project.getDbSession()
                db_session.add_all(db_data)
                db_session.commit()
            finally:
                db_session.close()

        if len(self.open_end_start) == 0:
            self._pre_stream_length = None



    def load_catalogs(self):
        ''' Load the detection catalogs from the database.

        '''
        db_session = self.project.getDbSession()
        try:
            cat_table = self.project.dbTables['detection_catalog'];
            query = db_session.query(cat_table.id,
                                     cat_table.name,
                                     cat_table.description,
                                     cat_table.agency_uri,
                                     cat_table.author_uri,
                                     cat_table.creation_time)
            self.catalogs = query.all()
        finally:
            db_session.close()


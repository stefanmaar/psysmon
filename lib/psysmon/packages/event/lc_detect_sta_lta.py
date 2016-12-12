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

import numpy as np

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

        self.create_preferences()

    @property
    def pre_stream_length(self):
        ''' The time-span needed for correct processing prior to the start time
        of the stream passed to the execute method [s].
        '''
        return self.pref_manager.get_value('lta_length')


    def create_preferences(self):
        ''' Create the collection node preferences.
        '''
        # STA length
        item = preferences_manager.FloatSpinPrefItem(name = 'sta_length',
                                                     label = 'STA length [s]',
                                                     value = 1,
                                                     limit = (0, 3600))
        self.pref_manager.add_item(item = item)


        # LTA length
        item = preferences_manager.FloatSpinPrefItem(name = 'lta_length',
                                                     label = 'LTA length [s]',
                                                     value = 5,
                                                     limit = (0, 3600))
        self.pref_manager.add_item(item = item)

        # Threshold value
        item = preferences_manager.FloatSpinPrefItem(name = 'thr',
                                                     label = 'Threshold',
                                                     value = 3,
                                                     limit = (0, 100))
        self.pref_manager.add_item(item = item)

        # Stop criterium delay.
        item = preferences_manager.FloatSpinPrefItem(name = 'stop_delay',
                                                     label = 'Stop delay [s]',
                                                     value = 0.1,
                                                     limit = (0, 100),
                                                     tool_tip = 'The time prepend to the triggered event start to set the initial value of the stop criterium.')
        self.pref_manager.add_item(item = item)



        # The CF type.
        item = preferences_manager.SingleChoicePrefItem(name = 'cf_type',
                                                        label = 'cf type',
                                                        limit = ('abs', 'square', 'envelope', 'envelope^2'),
                                                        value = 'square',
                                                        tool_tip = 'The type of the characteristic function.'
                                                       )
        self.pref_manager.add_item(item = item)


        # The target detection catalog.
        item = preferences_manager.SingleChoicePrefItem(name = 'detection_catalog',
                                                        label = 'detection catalog',
                                                        limit = [],
                                                        value = None,
                                                        tool_tip = 'The detection catalog to which the detections are written.'
                                                       )
        self.pref_manager.add_item(item = item)



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


    def execute(self, stream, process_limits = None, origin_resource = None):
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
        cf_type = self.pref_manager.get_value('cf_type')
        stop_delay = self.pref_manager.get_value('stop_delay')

        # Initialize the detector.
        detector = detect.StaLtaDetector(thr = thr, cf_type = cf_type)

        # Detect the events using the STA/LTA detector.
        for cur_trace in stream:
            time_array = np.arange(0, cur_trace.stats.npts)
            time_array = time_array * 1/cur_trace.stats.sampling_rate
            time_array = time_array + cur_trace.stats.starttime.timestamp

            # Check if the data is a ma.maskedarray
            if np.ma.count_masked(cur_trace.data):
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

            # Write the detections to the database.

        # Store the current state of the detector in the node for the next time
        # window.
        # Most important store an eventually unfinished event in the node.


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


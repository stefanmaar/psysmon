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

import psysmon.core.gui_preference_dialog as gui_preference_dialog
import psysmon.core.packageNodes as package_nodes
import psysmon.core.preferences_manager as preferences_manager
import psysmon.packages.event.detect as detect
import psysmon.packages.event.detection_binding as detection_binding
import psysmon.packages.event.core as event_core


class DetectionBinder(package_nodes.LooperCollectionChildNode):
    ''' Detect events using STA/LTA algorithm.

    '''
    name = 'Detection binder'
    mode = 'looper child'
    category = 'Detection'
    tags = ['development', 'looper child', 'event', 'detect', 'bind']

    def __init__(self, **args):
        ''' Initialize the instance.
        '''
        package_nodes.LooperCollectionChildNode.__init__(self, **args)

        # No waveform data is needed.
        self.need_waveform_data = False

        # The detection catalog libarary
        self.detection_library = detect.Library('binder')

        # The working detection catalog.
        self.detection_catalog = None

        # The event catalog library
        self.event_library = event_core.Library('binder')

        # The working event catalog.
        self.event_catalog = None

        # Create the preference items.
        self.create_preferences()


    def create_preferences(self):
        ''' Create the collection node preferences.
        '''
        pref_page = self.pref_manager.add_page('Preferences')
        cat_group = pref_page.add_group('catalog')


        # The detection catalog to process.
        item = preferences_manager.SingleChoicePrefItem(name = 'detection_catalog',
                                                        label = 'detection catalog',
                                                        limit = [],
                                                        value = None,
                                                        tool_tip = 'The detection catalog to use for binding.'
                                                       )
        cat_group.add_item(item)

        # The event catalog to which to write the new events.
        item = preferences_manager.SingleChoicePrefItem(name = 'event_catalog',
                                                        label = 'event catalog',
                                                        limit = [],
                                                        value = None,
                                                        tool_tip = 'The event catalog for new events.'
                                                       )
        cat_group.add_item(item)



    def edit(self):
        ''' Create the preferences edit dialog.
        '''
        # Initialize the detection_catalog preference item.
        catalog_names = sorted(self.detection_library.get_catalogs_in_db(self.project))
        self.pref_manager.set_limit('detection_catalog', catalog_names)
        if catalog_names:
            if self.pref_manager.get_value('detection_catalog') not in catalog_names:
                self.pref_manager.set_value('detection_catalog', catalog_names[0])

        # Initialize the event catalog preference item.
        catalog_names = sorted(self.event_library.get_catalogs_in_db(self.project))
        self.pref_manager.set_limit('event_catalog', catalog_names)
        if catalog_names:
            if self.pref_manager.get_value('event_catalog') not in catalog_names:
                self.pref_manager.set_value('event_catalog', catalog_names[0])


        # Create the edit dialog.
        dlg = gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)

        # Enable/Disable the gui elements based on the pref_manager settings.
        #self.on_select_individual()

        dlg.ShowModal()
        dlg.Destroy()


    def initialize(self):
        ''' Initialize some insance persistent attributes.
        '''
        # Get the selected detection and event catalogs.
        catalog_name = self.pref_manager.get_value('detection_catalog')
        self.detection_library.load_catalog_from_db(project = self.project,
                                                    name = catalog_name)
        if catalog_name in self.detection_library.catalogs.keys():
            self.detection_catalog = self.detection_library.catalogs[catalog_name]
        else:
            raise RuntimeError("No detection catalog with name %s found in the database.", catalog_name)


        catalog_name = self.pref_manager.get_value('event_catalog')
        self.event_library.load_catalog_from_db(project = self.project,
                                                name = catalog_name)
        if catalog_name in self.event_library.catalogs.keys():
            self.event_catalog = self.event_library.catalogs[catalog_name]
        else:
            raise RuntimeError("No event catalog with name %s found in the database.", catalog_name)


    def execute(self, stream, process_limits = None, origin_resource = None, channels = None, **kwargs):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        # Load the detections for the processing timespan.
        # TODO: Make the minimum detection length a user preference.
        min_detection_length = None
        self.detection_catalog.load_detections(project = self.project,
                                               start_time = process_limits[0],
                                               end_time = process_limits[1],
                                               min_detection_length = min_detection_length)
        self.detection_catalog.assign_channel(inventory = self.project.geometry_inventory)


        # Initialize the binder.
        # TODO: This could be moved to the initialize method.
        stations = [x.parent_station for x in channels]
        stations = list(set(stations))
        binder = detection_binding.DetectionBinder(event_catalog = self.event_catalog,
                                                   stations = stations,
                                                   author_uri = self.project.activeUser.author_uri,
                                                   agency_uri = self.project.activeUser.agency_uri)
        binder.compute_search_windows(vel = 3000)

        # Get the detecions at the end of the processing window which can't be
        # processed becaused of potentially missing detections outside the
        # processing window.
        max_search_window = max([max(x.values()) for x in binder.search_windows.values()])
        keep_detections = self.detection_catalog.get_detections(start_time = process_limits[1] - max_search_window,
                                                                start_inside = True)
        self.detection_catalog.remove_detections(keep_detections)

        # Bind the detections
        binder.bind(catalog = self.detection_catalog,
                    channel_scnl = [x.scnl for x in channels])

        # Store the unprocessed detection in the catalog for the next step.
        self.detection_catalog.clear_detections()
        self.detection_catalog.add_detections(keep_detections)

        # Write the events of the binder to the database and clear the
        # binder event catalog.
        binder.event_catalog.write_to_database(self.project)
        binder.event_catalog.clear_events()





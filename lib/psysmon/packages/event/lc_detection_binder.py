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

import psysmon
import psysmon.core.packageNodes as package_nodes
import psysmon.core.preferences_manager as preferences_manager
import psysmon.packages.event.detect as detect
import psysmon.packages.event.detection_binding as detection_binding
import psysmon.packages.event.core as event_core

# Import GUI related modules only if wxPython is available.
if psysmon.wx_available:
    import psysmon.gui.dialog.pref_listbook as psy_lb

#from profilehooks import profile


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

        # The detection binder.
        self.binder = None

        # Create the preference items.
        self.create_preferences()


    def create_preferences(self):
        ''' Create the collection node preferences.
        '''
        pref_page = self.pref_manager.add_page('Preferences')
        cat_group = pref_page.add_group('catalog')
        bind_group = pref_page.add_group('binding')


        # The detection catalog to process.
        item = preferences_manager.SingleChoicePrefItem(name = 'detection_catalog',
                                                        label = 'detection catalog',
                                                        limit = [],
                                                        value = None,
                                                        tool_tip = 'The detection catalog to use for binding.')
        cat_group.add_item(item)

        # The event catalog to which to write the new events.
        item = preferences_manager.SingleChoicePrefItem(name = 'event_catalog',
                                                        label = 'event catalog',
                                                        limit = [],
                                                        value = None,
                                                        tool_tip = 'The event catalog for new events.')
        cat_group.add_item(item)

        # The minimum length of the detecions used for binding.
        item = preferences_manager.FloatSpinPrefItem(name = 'min_detection_length',
                                                     label = 'min. detection length [s]',
                                                     value = 0.1,
                                                     limit = (0, 1000000),
                                                     tool_tip = 'The minimum length of the detections used for the binding [s].')
        bind_group.add_item(item)

        # Use the maximum length limit.
        item = preferences_manager.CheckBoxPrefItem(name = 'limit_max_length',
                                                    label = 'limit max. length',
                                                    value = False,
                                                    tool_tip = 'Use the maximum detection length limit.',
                                                    hooks = {'on_value_change': self.on_limit_max_length})
        bind_group.add_item(item)

        # The maxmimum length of the detecions used for binding.
        item = preferences_manager.FloatSpinPrefItem(name = 'max_detection_length',
                                                     label = 'max. detection length [s]',
                                                     value = 100,
                                                     limit = (0, 1000000),
                                                     tool_tip = 'The maximum length of the detections used for the binding [s].')
        bind_group.add_item(item)

        # The number of nearest neighbors used for searching neighboring 
        # detections.
        item = preferences_manager.IntegerSpinPrefItem(name = 'n_neighbors',
                                                       label = 'neighbors to search',
                                                       value = 2,
                                                       limit = (0, 100),
                                                       tool_tip = 'The number of nearest neighbors used to search for corresponding detections.')
        bind_group.add_item(item)

        # The minimum number of matching neighbors needed to declare an event.
        item = preferences_manager.IntegerSpinPrefItem(name = 'min_match_neighbors',
                                                       label = 'match neighbors',
                                                       value = 2,
                                                       limit = (0, 100),
                                                       tool_tip = 'The minimum number of matching neighbors needed to declare an event.')
        bind_group.add_item(item)

        # The velocity used for search window computation.
        item = preferences_manager.IntegerSpinPrefItem(name = 'search_win_vel',
                                                       label = 'search window velocity',
                                                       value = 1000,
                                                       limit = (1, 100000),
                                                       tool_tip = 'The velocity used to compute the search window lengths [m/s].')
        bind_group.add_item(item)

        # The ratio used to compute the search window from the detection length..
        item = preferences_manager.FloatSpinPrefItem(name = 'extend_ratio',
                                                     label = 'search window extend ratio',
                                                     value = 0.01,
                                                     limit = (0, 1),
                                                     tool_tip = 'The detection length multiplied with the extend ratio is used for the search window extend value.')
        bind_group.add_item(item)
        
        # The minimum lenght of the search window extension.
        item = preferences_manager.FloatSpinPrefItem(name = 'min_search_win_extend',
                                                     label = 'min. search window extend [s]',
                                                     value = 0.1,
                                                     limit = (0, 100000),
                                                     tool_tip = 'The minimum length of the time window added to the search window.')
        bind_group.add_item(item)
        
        # The maximum length of the search window extension.
        item = preferences_manager.FloatSpinPrefItem(name = 'max_search_win_extend',
                                                     label = 'max. search window extend [s]',
                                                     value = 10,
                                                     limit = (0, 100000),
                                                     tool_tip = 'The maximum length of the time window added to the search window.')
        bind_group.add_item(item)


    def on_limit_max_length(self):
        ''' Handle a value change of the limit_max_length checkbox perference.
        '''
        if self.pref_manager.get_value('limit_max_length') is True:
            self.pref_manager.get_item('max_detection_length')[0].enable_gui_element()
        else:
            self.pref_manager.get_item('max_detection_length')[0].disable_gui_element()
                

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
        dlg = psy_lb.ListbookPrefDialog(preferences = self.pref_manager)

        # Enable/Disable the gui elements based on the pref_manager settings.
        self.on_limit_max_length()

        dlg.ShowModal()
        dlg.Destroy()


    def initialize(self,
                   process_limits = None,
                   origin_resource = None,
                   channels = None,
                   **kwargs):
        ''' Initialize some insance persistent attributes.
        '''
        super(DetectionBinder, self).initialize()
        # Get the selected detection and event catalogs.

        catalog_name = self.pref_manager.get_value('detection_catalog')
        self.logger.debug('Loading the detection catalog.')
        self.detection_library.load_catalog_from_db(project = self.project,
                                                    name = catalog_name)
        if catalog_name in iter(self.detection_library.catalogs.keys()):
            self.detection_catalog = self.detection_library.catalogs[catalog_name]
        else:
            raise RuntimeError("No detection catalog with name %s found in the database.", catalog_name)


        catalog_name = self.pref_manager.get_value('event_catalog')
        self.logger.debug('Loading the event catalog.')
        self.event_library.load_catalog_from_db(project = self.project,
                                                name = catalog_name)
        if catalog_name in iter(self.event_library.catalogs.keys()):
            self.event_catalog = self.event_library.catalogs[catalog_name]
        else:
            raise RuntimeError("No event catalog with name %s found in the database.", catalog_name)

        # Initialize the binder.
        stations = [x.parent_station for x in channels]
        stations = list(set(stations))
        self.logger.info('Initializing the Binder.')
        self.binder = detection_binding.DetectionBinder(event_catalog = self.event_catalog,
                                                        stations = stations,
                                                        author_uri = self.project.activeUser.author_uri,
                                                        agency_uri = self.project.activeUser.agency_uri)

        search_win_vel = self.pref_manager.get_value('search_win_vel')
        self.binder.compute_search_windows(vel = search_win_vel)
        self.logger.debug('Search windows: %s', self.binder.search_windows)
        self.logger.debug('Epi-distances: %s', self.binder.epi_dist)

    #@profile(immediate=True)
    def execute(self,
                stream,
                process_limits = None,
                origin_resource = None,
                channels = None,
                **kwargs):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        # Load the detections for the processing timespan.
        min_detection_length = self.pref_manager.get_value('min_detection_length')
        max_detection_length = None
        limit_max_length = self.pref_manager.get_value('limit_max_length')
        if limit_max_length is True:
            max_detection_length = self.pref_manager.get_value('max_detection_length')
            
        self.logger.info('Loading the detections.')
        self.detection_catalog.load_detections(project = self.project,
                                               start_time = process_limits[0],
                                               end_time = process_limits[1],
                                               min_detection_length = min_detection_length,
                                               max_detection_length = max_detection_length)
        self.detection_catalog.assign_channel(inventory = self.project.geometry_inventory)


        # Get the detecions at the end of the processing window which can't be
        # processed becaused of potentially missing detections outside the
        # processing window.
        max_search_window = max([max(x.values()) for x in list(self.binder.search_windows.values())])
        self.logger.debug('Fixing the catalog.')
        keep_detections = self.detection_catalog.get_detections(start_time = process_limits[1] - max_search_window,
                                                                start_inside = True)
        self.detection_catalog.remove_detections(keep_detections)

        # Bind the detections
        self.logger.info('Binding the detections.')
        n_neighbors = self.pref_manager.get_value('n_neighbors')
        min_match_neighbors = self.pref_manager.get_value('min_match_neighbors')
        extend_ratio = self.pref_manager.get_value('extend_ratio')
        min_extend = self.pref_manager.get_value('min_search_win_extend')
        max_extend = self.pref_manager.get_value('max_search_win_extend')
        
        self.binder.bind(catalog = self.detection_catalog,
                         channel_scnl = [x.scnl for x in channels],
                         n_neighbors = n_neighbors,
                         min_match_neighbors = min_match_neighbors,
                         extend_ratio = extend_ratio,
                         min_extend = min_extend,
                         max_extend = max_extend)

        # Store the unprocessed detection in the catalog for the next step.
        self.logger.info('Cleaning the detection catalog.')
        self.detection_catalog.clear_detections()
        self.detection_catalog.add_detections(keep_detections)

        # Write the events of the binder to the database and clear the
        # binder event catalog.
        self.logger.info('Writing the events to the database.')
        self.binder.event_catalog.write_to_database(self.project,
                                                    bulk_insert = True)
        self.binder.event_catalog.clear_events()

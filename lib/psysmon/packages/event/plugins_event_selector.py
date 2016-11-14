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
import wx
from obspy.core.utcdatetime import UTCDateTime
import wx.lib.mixins.listctrl as listmix
from wx.lib.stattext import GenStaticText as StaticText

import psysmon
from psysmon.core.plugins import OptionPlugin
from psysmon.core.guiBricks import PrefEditPanel
from psysmon.artwork.icons import iconsBlack16 as icons
import psysmon.core.preferences_manager as psy_pm


class SelectEvents(OptionPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' Initialize the instance.

        '''
        OptionPlugin.__init__(self,
                              name = 'show events',
                              category = 'view',
                              tags = ['show', 'events']
                             )

        # Create the logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.flag_icon_16

        # The currently selected event.
        self.selected_event = {}

        # The plot colors used by the plugin.
        self.colors = {}
        self.colors['event_vspan'] = '0.9'

        # Setup the pages of the preference manager.
        self.pref_manager.add_page('Select')
        self.pref_manager.add_page('Display')

        item = psy_pm.DateTimeEditPrefItem(name = 'start_time',
                                           label = 'start time',
                                           group = 'detection time span',
                                           value = UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The start time of the detection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).')
        self.pref_manager.add_item(pagename = 'Select',
                                   item = item)


        item = psy_pm.FloatSpinPrefItem(name = 'window_length',
                                        label = 'window length [s]',
                                        group = 'detection time span',
                                        value = 3600,
                                        limit = (0, 3153600000),
                                        digits = 1,
                                        tool_tip = 'The length of the time window for which events should be loaded.')
        self.pref_manager.add_item(pagename = 'Select',
                                   item = item)

        item = psy_pm.SingleChoicePrefItem(name = 'event_catalog',
                                          label = 'event catalog',
                                          group = 'event selection',
                                          value = '',
                                          limit = [],
                                          tool_tip = 'Select an event catalog for which to load the events.')
        self.pref_manager.add_item(pagename = 'Select',
                                   item = item)


#        item = psy_pm.CustomPrefItem(name = 'events',
#                                     label = 'events',
#                                     group = 'event selection',
#                                     value = [],
#                                     gui_class = EventListField,
#                                     tool_tip = 'The start time of the detection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).')
        column_labels = ['db_id', 'start_time', 'length', 'public_id',
                         'description', 'agency_uri', 'author_uri',
                         'comment']
        item = psy_pm.ListCtrlEditPrefItem(name = 'events',
                                           label = 'events',
                                           group = 'event selection',
                                           value = [],
                                           column_labels = column_labels,
                                           limit = [],
                                           hooks = {'on_value_change': self.on_event_selected},
                                           tool_tip = 'The available events.')
        self.pref_manager.add_item(pagename = 'Select',
                                   item = item)


        item = psy_pm.ActionItem(name = 'load_events',
                                 label = 'load events',
                                 group = 'detection time span',
                                 mode = 'button',
                                 action = self.on_load_events)
        self.pref_manager.add_item(pagename = 'Select',
                                   item = item)


        item = psy_pm.FloatSpinPrefItem(name = 'pre_et',
                                        label = 'pre event time [s]',
                                        group = 'display range',
                                        value = 5,
                                        limit = (0, 86400),
                                        digits = 1,
                                        tool_tip = 'The length of the time window to show before the event start.')
        self.pref_manager.add_item(pagename = 'Display',
                                   item = item)

        item = psy_pm.FloatSpinPrefItem(name = 'post_et',
                                        label = 'post event time [s]',
                                        group = 'display range',
                                        value = 10,
                                        limit = (0, 86400),
                                        digits = 1,
                                        tool_tip = 'The length of the time window to show after the event end.')
        self.pref_manager.add_item(pagename = 'Display',
                                   item = item)

        item = psy_pm.CheckBoxPrefItem(name = 'show_event_limits',
                                       label = 'show event limits',
                                       value = True,
                                       hooks = {'on_value_change': self.on_show_event_limits_changed},
                                       tool_tip = 'Show the limits of the selected event in the views.')
        self.pref_manager.add_item(pagename = 'Display',
                                   item = item)



    def buildFoldPanel(self, panelBar):
        ''' Create the foldpanel GUI.
        '''
        fold_panel = PrefEditPanel(pref = self.pref_manager,
                                  parent = panelBar)


        # Customize the events field.
        #pref_item = self.pref_manager.get_item('events')[0]
        #field = pref_item.gui_element[0]
        #fold_panel.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_event_selected, field.controlElement)

        #self.events_lb = field.controlElement

        return fold_panel


    def activate(self):
        ''' Extend the plugin activate method.
        '''
        OptionPlugin.activate(self)

        # Initialize the catalog names.
        catalog_names = self.parent.event_library.get_catalogs_in_db(self.parent.project)
        self.pref_manager.set_limit('event_catalog', catalog_names)
        if catalog_names:
            self.pref_manager.set_value('event_catalog', catalog_names[0])

        # If an event already was selected, share it again.
        # TODO: Think about not deleting the shared information if the plugin
        # is deactivated. Otherwise not many plugins can be opened at a time.
        if self.selected_event:
            self.parent.add_shared_info(origin_rid = self.rid,
                                        name = 'selected_event',
                                        value = self.selected_event)

            # Add the pre- and post event time.
            start_time = self.selected_event['start_time'] - self.pref_manager.get_value('pre_et')
            end_time = self.selected_event['end_time'] + self.pref_manager.get_value('post_et')

            self.parent.displayManager.setTimeLimits(startTime = start_time,
                                                     endTime = end_time)
            self.clear_annotation()
            self.parent.update_display()


    def deactivate(self):
        ''' Extend the plugin deactivate method.
        '''
        OptionPlugin.deactivate(self)
        self.clear_annotation()
        # TODO: Think about not deleting the shared information if the plugin
        # is deactivated. Otherwise not many plugins can be opened at a time.
        self.parent.plugins_information_bag.remove_info(origin_rid = self.rid)


    def on_show_event_limits_changed(self):
        ''' The on_value_changed callback of the show_event_limits item.
        '''
        if not self.pref_manager.get_value('show_event_limits'):
            self.clear_annotation()
        else:
            self.on_after_plot()


    def getHooks(self):
        ''' The callback hooks.
        '''
        hooks = {}

        hooks['after_plot'] = self.on_after_plot
        hooks['after_plot_station'] = self.on_after_plot_station
        hooks['shared_information_updated'] = self.on_shared_information_updated

        return hooks


    def on_after_plot(self):
        ''' The hook called after the plotting in tracedisplay.
        '''
        if self.pref_manager.get_value('show_event_limits'):
            self.add_event_marker_to_station(station = self.parent.displayManager.showStations)


    def on_after_plot_station(self, station):
        ''' The hook called after the plotting of a station in tracedisplay.
        '''
        if self.pref_manager.get_value('show_event_limits'):
            self.add_event_marker_to_station(station = station)


    def on_shared_information_updated(self, updated_info):
        ''' The hook called after a shared information has been updated.
        '''
        if updated_info.origin_rid == self.rid and updated_info.name == 'selected_event':
            # Reload the events or update the selected event only.
            # It might be saver, to reload the catalog to ensure consistency.
            self.selected_event = updated_info.value
            self.update_events_list()
            self.clear_annotation()
            self.add_event_marker_to_station(self.parent.displayManager.showStations)



    def add_event_marker_to_station(self, station = None):
        ''' Add the event markers to station plots.
        '''
        if station:
            for cur_station in station:
                self.add_event_marker_to_channel(cur_station.channels)


    def add_event_marker_to_channel(self, channel = None):
        ''' Add the event markers to channel plots.
        '''
        for cur_channel in channel:
            scnl = cur_channel.getSCNL()
            channel_nodes = self.parent.viewport.get_node(station = scnl[0],
                                                          channel = scnl[1],
                                                          network = scnl[2],
                                                          location = scnl[3],
                                                          node_type = 'container')
            for cur_node in channel_nodes:
                cur_node.plot_annotation_vspan(x_start = self.selected_event['start_time'],
                                                                 x_end = self.selected_event['end_time'],
                                                                 label = self.selected_event['id'],
                                                                 parent_rid = self.rid,
                                                                 key = self.selected_event['id'],
                                                                 color = self.colors['event_vspan'])


    def on_load_events(self, event):
        '''
        '''
        self.update_events_list()


    def update_events_list(self):
        ''' Update the events list control.
        '''
        event_library = self.parent.event_library
        catalog_name = self.pref_manager.get_value('event_catalog')
        start_time = self.pref_manager.get_value('start_time')
        duration = self.pref_manager.get_value('window_length')

        if catalog_name not in event_library.catalogs.keys():
            event_library.load_catalog_from_db(project = self.parent.project,
                                               name = catalog_name)

        cur_catalog = event_library.catalogs[catalog_name]
        cur_catalog.clear_events()
        cur_catalog.load_events(project = self.parent.project,
                                start_time = start_time,
                                end_time = start_time + duration)

        event_list = self.convert_events_to_list(cur_catalog.events)
        self.pref_manager.set_limit('events', event_list)


    def convert_events_to_list(self, events):
        ''' Convert a list of event objects to a list suitable for the GUI element.
        '''
        list_fields = []
        list_fields.append(('db_id', 'id', int))
        list_fields.append(('start_time_string', 'start time', str))
        list_fields.append(('length', 'length', float))
        list_fields.append(('public_id', 'public id', str))
        list_fields.append(('description', 'description', str))
        list_fields.append(('agency_uri', 'agency', str))
        list_fields.append(('author_uri', 'author', str))
        list_fields.append(('comment', 'comment', str))

        event_list = []
        for cur_event in events:
            cur_row = []
            for cur_field in list_fields:
                cur_name = cur_field[0]
                cur_row.append(str(getattr(cur_event, cur_name)))
            event_list.append(cur_row)

        return event_list


    def on_event_selected(self):
        '''
        '''
        selected_event = self.pref_manager.get_value('events')

        if selected_event:
            selected_event = selected_event[0]
            event_id = float(selected_event[0])
            start_time = UTCDateTime(selected_event[1])
            end_time = start_time + float(selected_event[2])
            self.selected_event = {'start_time':start_time,
                                   'end_time':end_time,
                                   'id':event_id,
                                   'catalog_name': self.pref_manager.get_value('event_catalog')}
            self.parent.add_shared_info(origin_rid = self.rid,
                                        name = 'selected_event',
                                        value = self.selected_event)

            # Add the pre- and post event time.
            start_time -= self.pref_manager.get_value('pre_et')
            end_time += self.pref_manager.get_value('post_et')

            self.parent.displayManager.setTimeLimits(startTime = start_time,
                                                     endTime = end_time)
            self.clear_annotation()
            self.parent.update_display()


    def clear_annotation(self):
        ''' Clear the annotation elements in the tracedisplay views.
        '''
        node_list = self.parent.viewport.get_node(node_type = 'container')
        for cur_node in node_list:
            cur_node.clear_annotation_artist(mode = 'vspan',
                                             parent_rid = self.rid)
            cur_node.draw()




class EventListField(wx.Panel, listmix.ColumnSorterMixin):

    def __init__(self, name, pref_item, size, parent = None):
        '''
        '''
        wx.Panel.__init__(self, parent = parent, size = size, id = wx.ID_ANY)

        self.name = name

        self.pref_item = pref_item

        self.size = size

        self.label = name + ":"

        self.labelElement = None

        self.controlElement = None

        self.sizer = wx.GridBagSizer(5,5)

        # Create the field label.
        self.labelElement = StaticText(parent=self,
                                       ID=wx.ID_ANY,
                                       label=self.label,
                                       style=wx.ALIGN_LEFT)

        self.sizer.Add(self.labelElement, pos = (0,0), flag = wx.EXPAND|wx.ALL, border = 0)

        self.controlElement = EventListCtrl(parent = self, size = (200, 300),
                                            style = wx.LC_REPORT
                                            | wx.BORDER_NONE
                                            | wx.LC_SINGLE_SEL
                                            | wx.LC_SORT_ASCENDING)

        # The columns to show as a list to keep it in the correct order.
        self.columns = ['db_id', 'start_time', 'length', 'public_id',
                        'description', 'agency_uri', 'author_uri',
                        'comment']

        # The labels of the columns.
        self.column_labels = {'db_id': 'id',
                       'start_time': 'start time',
                       'length': 'length',
                       'public_id': 'public id',
                       'description': 'description',
                       'agency_uri': 'agency',
                       'author_uri': 'author',
                       'comment': 'comment'}

        # Methods for derived values.
        self.get_method = {'length': self.get_length}

        # Methods for values which should not be converted using the default
        # str function.
        self.convert_method = {'start_time': self.convert_to_isoformat}

        for k, name in enumerate(self.columns):
            self.controlElement.InsertColumn(k, self.column_labels[name])

        self.sizer.Add(self.controlElement, pos = (1,0), flag = wx.EXPAND|wx.ALL, border = 0)
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(1)

        self.SetSizer(self.sizer)

    def __del__(self):
        self.pref_item.remove_gui_element(self)


    def set_events(self, events):
        '''
        '''
        self.controlElement.DeleteAllItems()
        for k, cur_event in enumerate(events):
            for n_col, cur_name in enumerate(self.columns):
                if cur_name in self.get_method.keys():
                    val = self.get_method[cur_name](cur_event)
                elif cur_name in self.convert_method.keys():
                    val = self.convert_method[cur_name](getattr(cur_event, cur_name))
                else:
                    val = str(getattr(cur_event, cur_name))

                if n_col == 0:
                    self.controlElement.InsertStringItem(k, val)
                else:
                    self.controlElement.SetStringItem(k, n_col, val)


    def convert_to_isoformat(self, val):
        return UTCDateTime(val).isoformat()

    def get_length(self, event):
        return str(event.end_time - event.start_time)






class EventListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    '''
    '''
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        ''' Initialize the instance.
        '''
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

        # Create the icons for column sorting.
        self.il = wx.ImageList(16, 16)
        self.sm_up = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_OTHER, (16,16)))
        self.sm_dn = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_OTHER, (16,16)))
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)


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

from builtins import str
import psysmon
import logging
import wx
from psysmon.core.plugins import InteractivePlugin
from psysmon.core.guiBricks import PrefEditPanel
from psysmon.artwork.icons import psysmon_iconset_16 as icons
import psysmon.packages.event.detect as detect
import psysmon.core.preferences_manager as psy_pm
import psysmon.packages.pick.core as pick_core
from obspy.core.utcdatetime import UTCDateTime
import numpy as np


class DetectionAdd(InteractivePlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''
        InteractivePlugin.__init__(self,
                                   name = 'detection',
                                   category = 'edit',
                                   tags = None
                                  )
        # Create the logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.detection_new_16
        self.cursor = wx.CURSOR_CROSS

        # The detection library.
        self.library = detect.Library(self.rid)

        # The selected catalog.
        self.selected_catalog = None

        # A flag indicating if the detection catalog was loaded for a selected
        # event.
        self.catalog_loaded_for_selected_event = False

        # Add the pages to the preferences manager.
        to_page = self.pref_manager.add_page('tool options')
        cat_group = to_page.add_group('catalog')
        #po_group = to_page.add_group('pick options')

        # Add the plugin preferences.
        item = psy_pm.SingleChoicePrefItem(name = 'detection_catalog',
                                           label = 'detection catalog',
                                           value = '',
                                           limit = [],
                                           tool_tip = 'Select a detection catalog to work on.',
                                           hooks = {'on_value_change': self.on_select_catalog})
        cat_group.add_item(item)

        item = psy_pm.ActionItem(name = 'create_new_catalog',
                                 label = 'create new catalog',
                                 mode = 'button',
                                 action = self.on_create_new_catalog)
        cat_group.add_item(item)



        #item = psy_pm.TextEditPrefItem(name = 'label',
        #                               label = 'label',
        #                               value = 'P',
        #                               tool_tip = 'The label of the pick.')
        #po_group.add_item(item)

        #item = psy_pm.FloatSpinPrefItem(name = 'delete_snap_length',
        #                               label = 'delete snap [s]',
        #                               value = 0.1,
        #                               limit = (0, 1000),
        #                               tool_tip = 'The snap length used when deleting picks.')
        #po_group.add_item(item)


    def buildFoldPanel(self, panelBar):
        ''' Create the foldpanel GUI.
        '''
        # Set the limits of the event_catalog field.
        catalog_names = self.library.get_catalogs_in_db(project = self.parent.project)
        self.pref_manager.set_limit('detection_catalog', catalog_names)
        #if catalog_names:
        #    self.pref_manager.set_value('pick_catalog', catalog_names[0])

        fold_panel = PrefEditPanel(pref = self.pref_manager,
                                   parent = panelBar)

        return fold_panel


    def activate(self):
        ''' Extend the Plugin activate method.
        '''
        if self.selected_catalog_name is None:
            self.logger.info('You have to select a pick catalog first.')
        else:
            InteractivePlugin.activate(self)
            #self.load_picks()
            #self.add_pick_lines()


    def deactivate(self):
        ''' Extend the Plugin deactivate method.
        '''
        #self.clear_pick_lines()
        InteractivePlugin.deactivate(self)


    def getHooks(self):
        ''' The callback hooks.
        '''
        hooks = {}

        # The view hooks. These are matplotlib events called from the views.
        hooks['button_press_event'] = self.on_button_press

        # The hooks called from general tracedisplay.
        #hooks['after_plot'] = self.add_pick_lines
        #hooks['after_plot_station'] = self.add_pick_lines_station
        #hooks['after_plot_channel'] = self.add_pick_lines_channel
        #hooks['time_limit_changed'] = self.load_picks
        #hooks['plugin_deactivated'] = self.on_other_plugin_deactivated
        #hooks['shared_information_added'] = self.on_shared_information_added

        return hooks


    def on_button_press(self, event, dataManager = None, displayManager = None):
        ''' Handle a mouse button press in a view.
        '''
        cur_view = event.canvas.GetGrandParent()
        self.view = cur_view

        if event.button == 2:
            # Skip the middle mouse button.
            return
        elif event.button == 3:
            self.logger.info('Delete a detection.')
            #self.delete_pick(event)
        else:
            if self.selected_catalog_name is None:
                self.logger.info('You have to select a pick catalog first.')
            elif cur_view.name.endswith('plot_seismogram'):
                self.logger.info('Adding a new detection.')
                #self.pick_seismogram(event, dataManager, displayManager)
            else:
                self.logger.info('Picking in a %s view is not supported.', cur_view.name)


    def on_shared_information_added(self, origin_rid, name):
        ''' Hook that is called when a shared information was added by a plugin.
        '''
        if origin_rid == self.parent.collection_node.rid + '/plugin/show_events' and name == 'selected_event':
            self.logger.info('Handling a new shared information added by the show_events plugin.')
            #self.load_picks()
            #self.clear_pick_lines()
            #self.add_pick_lines()


    def on_other_plugin_deactivated(self, plugin_rid):
        ''' Hook that is called when a plugin is deactivated in the tracedisplay.
        '''
        if plugin_rid == self.parent.collection_node.rid + '/plugin/show_events':
            self.logger.info('Handling a deactivated show_events plugin.')
            #self.load_picks()
            #self.clear_pick_lines()
            #self.add_pick_lines()


    def add_pick_lines(self):
        ''' Add the pick lines to the views.
        '''
        self.add_pick_lines_station(station = self.parent.displayManager.showStations)


    def add_pick_lines_station(self, station = None):
        ''' Add the pick lines to the views of the station.
        '''
        if station is None:
            return

        for cur_station in station:
            self.add_pick_lines_channel(cur_station.channels)


    def add_pick_lines_channel(self, channel = None):
        ''' Add the pick lines to the views of the channel.
        '''
        if channel is None:
            return

        for cur_plot_channel in channel:
            scnl = cur_plot_channel.getSCNL()
            cur_channel = self.parent.project.geometry_inventory.get_channel(station = scnl[0],
                                                                             name = scnl[1],
                                                                             network = scnl[2],
                                                                             location = scnl[3])
            if not cur_channel:
                self.logger.error('No channel for SCNL %s found in the inventory.', scnl)
            elif len(cur_channel) > 1:
                self.logger.error("More than one channel returned from the inventory for SCNL %s. This shouldn't happen.", scnl)
            else:
                # Get the pick from the database and create the pick lines.
                cur_catalog = self.library.catalogs[self.selected_catalog_name]
                search_win_start = self.parent.displayManager.startTime
                search_win_end = self.parent.displayManager.endTime
                picks = cur_catalog.get_pick(start_time = search_win_start,
                                             end_time = search_win_end,
                                             station = scnl[0],
                                             location = scnl[3])

                for cur_pick in picks:
                    # Create the pick line in all channels of the station.
                    cur_node_list = self.parent.viewport.get_node(station = scnl[0],
                                                                  name = scnl[1],
                                                                  network = scnl[2],
                                                                  location = scnl[3],
                                                                  node_type = 'container')
                    # TODO: Change the plot_pick_line method to accept a list
                    # of nodes.
                    for cur_node in cur_node_list:
                        self.plot_pick_line(cur_pick, cur_node)


    def pick_seismogram(self, event, data_manager, display_manager):
        ''' Create a pick in a seismogram view.
        '''
        if event.inaxes is None:
            return

        cur_axes = self.view.axes

        # Find the seismogram line.
        seismo_line = [x for x in cur_axes.lines if x.get_label() == 'seismogram']
        if len(seismo_line) > 0:
            seismo_line = seismo_line[0]
        else:
            raise RuntimeError('No seismogram line found.')

        # Get the picked sample.
        xdata = seismo_line.get_xdata()
        ydata = seismo_line.get_ydata()
        ind_x = np.searchsorted(xdata, [event.xdata])[0]
        snap_x = xdata[ind_x]
        snap_y = ydata[ind_x]

        # Check if it is inside the event limits.
        selected_event_info = self.parent.get_shared_info(origin_rid = self.parent.collection_node.rid + '/plugin/show_events',
                                                          name = 'selected_event')
        if selected_event_info:
            if len(selected_event_info) > 1:
                raise RuntimeError("More than one event info was returned. This shouldn't happen.")
            selected_event_info = selected_event_info[0]
            event_start = selected_event_info.value['start_time']
            event_end = selected_event_info.value['end_time']
            event_id = selected_event_info.value['id']
            if not (snap_x >= event_start.timestamp and snap_x <= event_end.timestamp):
                self.logger.info("The pick is outside the selected event limits. Setting the pick is not allowed.")
                return
        else:
            event_id = None


        # Get the channel of the pick.
        props = self.view.props
        cur_channel = self.parent.project.geometry_inventory.get_channel(station = props.station,
                                                                         name = props.channel,
                                                                         network = props.network,
                                                                         location = props.location)
        if not cur_channel:
            scnl = (props.station, props.channel, props.network, props.location)
            self.logger.error('No channel for SCNL %s found in the inventory.', ':'.join(scnl))
        elif len(cur_channel) > 1:
            self.logger.error("More than one channel returned from the inventory for SCNL %s. This shouldn't happen.", ':'.join(scnl))
        else:
            # Create the pick and write it to the database.
            cur_catalog = self.library.catalogs[self.selected_catalog_name]

            # Check if a pick already exists in the displayed time span, or, if
            # an event is selected in the selected event limits.
            if selected_event_info:
                search_win_start = selected_event_info.value['start_time']
                search_win_end = selected_event_info.value['end_time']
            else:
                search_win_start = self.parent.displayManager.startTime
                search_win_end = self.parent.displayManager.endTime

            if event_id is not None:
                picks = cur_catalog.get_pick(start_time = search_win_start,
                                             end_time = search_win_end,
                                             label = self.pref_manager.get_value('label'),
                                             station = props.station,
                                             location = props.location,
                                             event_id = event_id)
            else:
                picks = cur_catalog.get_pick(start_time = search_win_start,
                                             end_time = search_win_end,
                                             label = self.pref_manager.get_value('label'),
                                             station = props.station,
                                             location = props.location)

            if len(picks) == 0:
                cur_channel = cur_channel[0]
                cur_pick = pick_core.Pick(label = self.pref_manager.get_value('label'),
                                          time = UTCDateTime(snap_x),
                                          amp1 = snap_y,
                                          channel = cur_channel,
                                          event_id = event_id)
                cur_catalog.add_picks([cur_pick,])
                cur_pick.write_to_database(self.parent.project)
            else:
                pick_time = UTCDateTime(snap_x)
                nearest_pick = picks[0]
                dist = np.abs(pick_time - nearest_pick.time)
                for cur_pick in picks[1:]:
                    cur_dist = np.abs(pick_time - cur_pick.time)
                    if cur_dist < dist:
                        dist = cur_dist
                        nearest_pick = cur_pick
                nearest_pick.time = pick_time
                nearest_pick.amp1 = snap_y
                if event_id:
                    nearest_pick.event_id = event_id
                nearest_pick.write_to_database(self.parent.project)
                cur_pick = nearest_pick

            # Create the pick line in all channels of the station.
            self.plot_pick_line(cur_pick, self.view.GetGrandParent())

            # Make the pick lines visible.
            self.view.GetGrandParent().draw()


    def plot_pick_line(self, pick, container):
        ''' Plot a pick line in the container.
        '''
        if pick.event_id:
            line_color = 'firebrick'
        else:
            line_color = 'darkgrey'

        container.plot_annotation_vline(pick.time.timestamp,
                                        label = pick.label,
                                        parent_rid = self.rid,
                                        key = pick.rid,
                                        color = line_color)
        container.draw()



    def delete_pick(self, event):
        ''' Delete a pick from the database.
        '''
        if event.inaxes is None:
            return

        cur_axes = self.view.axes

        # Find the seismogram line.
        seismo_line = [x for x in cur_axes.lines if x.get_label() == 'seismogram']
        if len(seismo_line) > 0:
            seismo_line = seismo_line[0]
        else:
            raise RuntimeError('No seismogram line found.')

        # Get the picked sample.
        xdata = seismo_line.get_xdata()
        ind_x = np.searchsorted(xdata, [event.xdata])[0]
        snap_x = xdata[ind_x]

        # Get the channel of the pick.
        props = self.view.props
        cur_channel = self.parent.project.geometry_inventory.get_channel(station = props.station,
                                                                         name = props.channel,
                                                                         network = props.network,
                                                                         location = props.location)
        if not cur_channel:
            scnl = (props.station, props.channel, props.network, props.location)
            self.logger.error('No channel for SCNL %s found in the inventory.', ':'.join(scnl))
        elif len(cur_channel) > 1:
            self.logger.error("More than one channel returned from the inventory for SCNL %s. This shouldn't happen.", ':'.join(scnl))
        else:
            # Get the nearest pick and delete it.
            cur_catalog = self.library.catalogs[self.selected_catalog_name]
            pick = cur_catalog.get_nearest_pick(pick_time = UTCDateTime(snap_x),
                                                start_time = UTCDateTime(snap_x) - self.pref_manager.get_value('delete_snap_length'),
                                                end_time = UTCDateTime(snap_x) + self.pref_manager.get_value('delete_snap_length'),
                                                label = self.pref_manager.get_value('label'),
                                                station = props.station)

            if pick:
                cur_catalog.delete_picks_from_db(project = self.parent.project,
                                                 picks = [pick, ])
                self.view.GetGrandParent().clear_annotation_artist(mode = 'vline',
                                                                   parent_rid = self.rid,
                                                                   key = pick.rid)

                self.view.GetGrandParent().draw()



    def on_select_catalog(self):
        ''' Handle the catalog selection.
        '''
        catalog_name = self.pref_manager.get_value('detection_catalog')
        start_time = self.parent.displayManager.startTime
        end_time = self.parent.displayManager.endTime

        if catalog_name not in iter(self.library.catalogs.keys()):
            self.library.load_catalog_from_db(project = self.parent.project,
                                              name = catalog_name)

        cur_catalog = self.library.catalogs[catalog_name]
        #cur_catalog.clear_detections()
        #cur_catalog.load_detections(project = self.parent.project,
        #                            start_time = start_time,
        #                            end_time = end_time)

        self.selected_catalog = cur_catalog


    def load_picks(self):
        ''' Load the picks for the current timespan of the tracedisplay.
        '''
        cur_catalog = self.library.catalogs[self.selected_catalog_name]
        cur_catalog.clear_picks()

        # Check if an event is selected. If one is selected, use the event
        # limits to load the picks.
        selected_event_info = self.parent.plugins_information_bag.get_info(origin_rid = self.parent.collection_node.rid + '/plugin/show_events',
                                                                           name = 'selected_event')
        if selected_event_info:
            if len(selected_event_info) > 1:
                raise RuntimeError("More than one event info was returned. This shouldn't happen.")
            selected_event_info = selected_event_info[0]
            time_win_start = selected_event_info.value['start_time']
            time_win_end = selected_event_info.value['end_time']
            self.catalog_loaded_for_selected_event = True
        else:
            time_win_start = self.parent.displayManager.startTime
            time_win_end = self.parent.displayManager.endTime
            self.catalog_loaded_for_selected_event = False

        cur_catalog.load_picks(project = self.parent.project,
                               start_time = time_win_start,
                               end_time = time_win_end)


    def clear_pick_lines(self):
        ''' Remove the pick lines from the views.
        '''
        node_list = self.parent.viewport.get_node(node_type = 'container')
        for cur_node in node_list:
            cur_node.clear_annotation_artist(mode = 'vline',
                                             parent_rid = self.rid)
            cur_node.draw()





    def on_create_new_catalog(self, event):
        ''' Handle the create new catalog button click.
        '''
        dialog_fields = (("name:", "name", wx.TE_RIGHT, 'not_empty'),
                         ("description:", "description", wx.TE_RIGHT, None))

        dlg = EditDlg(parent = self.parent,
                      title = 'Create a new pick catalog.',
                      dialog_fields = dialog_fields)
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            self.create_catalog(mode = self.pref_manager.get_value('catalog_mode'), **dlg.data)
        dlg.Destroy()


    def create_catalog(self, mode, name, description):
        ''' Create a new catalog in the database.
        '''
        catalog = pick_core.Catalog(name = name,
                                    mode = mode,
                                    description = description,
                                    agency_uri = self.parent.project.activeUser.agency_uri,
                                    author_uri = self.parent.project.activeUser.author_uri,
                                    creation_time = UTCDateTime().isoformat())
        catalog.write_to_database(self.parent.project)
        cur_limit = self.pref_manager.get_limit('pick_catalog')
        cur_limit.append(catalog.name)
        self.pref_manager.set_limit('pick_catalog', cur_limit)



class EditDlg(wx.Dialog):

    def __init__(self, dialog_fields, title = None,
                 data = None, parent=None, size=(300, 200)):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title, size=size)


        # Use standard button IDs.
        ok_button = wx.Button(self, wx.ID_OK)
        ok_button.SetDefault()
        cancel_button = wx.Button(self, wx.ID_CANCEL)

        self.dialog_fields = dialog_fields

        if data is None:
            self.data = {}
        else:
            self.data = data

        # Layout using sizers.
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.label = {};
        self.edit = {};

        sizer.Add(self.create_dialog_fields(), 0, wx.EXPAND|wx.ALL, 5)

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(ok_button)
        btnSizer.AddButton(cancel_button)
        btnSizer.Realize()
        sizer.Add(btnSizer, 0, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

        # Bind the events.
        self.Bind(wx.EVT_BUTTON, self.on_ok, ok_button)


    def on_ok(self, event):
        is_valid = self.Validate()

        if(is_valid):
            for _, cur_key, _, _ in self.dialog_fields:
                self.data[cur_key] = self.edit[cur_key].GetValue()

            self.EndModal(wx.ID_OK)


    def create_dialog_fields(self):
        fgSizer = wx.FlexGridSizer(len(self.dialog_fields), 2, 5, 5)

        for curLabel, curKey, curStyle, curValidator in self.dialog_fields:
            self.label[curKey] = wx.StaticText(self, wx.ID_ANY, curLabel)
            self.edit[curKey] = wx.TextCtrl(self, size=(200, -1),
                                            style=curStyle)

            if curKey in iter(self.data.keys()):
                self.edit[curKey].SetValue(str(self.data[curKey]))

            if curValidator == 'not_empty':
                self.edit[curKey].SetValidator(NotEmptyValidator())

            fgSizer.Add(self.label[curKey], 0, wx.ALIGN_RIGHT)
            fgSizer.Add(self.edit[curKey], 0, wx.EXPAND)

        fgSizer.AddGrowableCol(1)
        return fgSizer


class NotEmptyValidator(wx.PyValidator):
    ## The constructor
    #
    # @param self The object pointer.
    def __init__(self):
        wx.PyValidator.__init__(self)


    ## The default clone method.    
    def Clone(self):
        return NotEmptyValidator()


    ## The method run when validating the field.
    #
    # This method checks if the control has a value. If not, it returns False.
    # @param self The object pointer.
    def Validate(self, win):
        ctrl = self.GetWindow()
        value = ctrl.GetValue()

        if len(value) == 0:
            wx.MessageBox("This field must contain some text!", "Error")
            ctrl.SetBackgroundColour("pink")
            ctrl.SetFocus()
            ctrl.Refresh()
            return False
        else:
            ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            ctrl.Refresh()
            return True

    ## The method called when entering the dialog.      
    def TransferToWindow(self):
        return True

    ## The method called when leaving the dialog.  
    def TransferFromWindow(self):
        return True

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
import logging
import wx
from psysmon.core.plugins import InteractivePlugin
from psysmon.core.guiBricks import PrefEditPanel
from psysmon.artwork.icons import iconsBlack16 as icons
import psysmon.core.preferences_manager as psy_pm
import psysmon.packages.pick.core as pick_core
from obspy.core.utcdatetime import UTCDateTime
import numpy as np

class PickTool(InteractivePlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''
        InteractivePlugin.__init__(self,
                                   name = 'pick',
                                   category = 'edit',
                                   tags = None
                                  )
        # Create the logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.hand_2_icon_16
        self.cursor = wx.CURSOR_CROSS

        # The pick catalog library used to manage the catalogs.
        self.library = pick_core.Library('pick library')

        # The name of the selected catalog.
        self.selected_catalog_name = None

        # The lines of the picks.
        self.pick_lines = {}

        # Add the pages to the preferences manager.
        self.pref_manager.add_page('tool options')

        # Add the plugin preferences.
        item = psy_pm.SingleChoicePrefItem(name = 'catalog_mode',
                                          label = 'mode',
                                          group = 'catalog',
                                          value = 'time',
                                          limit = ['time',],
                                          tool_tip = 'Select a pick catalog to work on.')
        self.pref_manager.add_item(pagename = 'tool options',
                                   item = item)

        item = psy_pm.SingleChoicePrefItem(name = 'pick_catalog',
                                          label = 'pick catalog',
                                          group = 'catalog',
                                          value = '',
                                          limit = [],
                                          tool_tip = 'Select a pick catalog to work on.',
                                          hooks = {'on_value_change': self.on_select_catalog})
        self.pref_manager.add_item(pagename = 'tool options',
                                   item = item)

        item = psy_pm.ActionItem(name = 'create_new_catalog',
                                 label = 'create new catalog',
                                 group = 'catalog',
                                 mode = 'button',
                                 action = self.on_create_new_catalog)
        self.pref_manager.add_item(pagename = 'tool options',
                                   item = item)


        item = psy_pm.TextEditPrefItem(name = 'label',
                                       label = 'label',
                                       group = 'pick options',
                                       value = 'P',
                                       tool_tip = 'The label of the pick.')
        self.pref_manager.add_item(pagename = 'tool options',
                                   item = item)



    def buildFoldPanel(self, panelBar):
        ''' Create the foldpanel GUI.
        '''
        # Set the limits of the event_catalog field.
        catalog_names = self.library.get_catalogs_in_db(project = self.parent.project)
        self.pref_manager.set_limit('pick_catalog', catalog_names)
        if catalog_names:
            self.pref_manager.set_value('pick_catalog', catalog_names[0])

        fold_panel = PrefEditPanel(pref = self.pref_manager,
                                  parent = panelBar)

        # Customize the catalog field.
        #pref_item = self.pref_manager.get_item('pick_catalog')[0]
        #field = pref_item.gui_element[0]
        #fold_panel.Bind(wx.EVT_CHOICE, self.on_catalog_selected, field.controlElement)

        return fold_panel


    def getHooks(self):
        ''' The callback hooks.
        '''
        hooks = {}

        hooks['button_press_event'] = self.on_button_press
        hooks['after_plot_data'] = self.on_add_pick_lines

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
            # Skipt the right mouse button.
            return
        else:
            if self.selected_catalog_name is None:
                self.logger.info('You have to select a pick catalog first.')
            elif cur_view.name == 'plot seismogram':
                self.pick_seismogram(event, dataManager, displayManager)
            else:
                self.logger.info('Picking in a %s view is not supported.', cur_view.name)


    def on_add_pick_lines(self):
        ''' Add the pick lines to the views.
        '''
        pass


    def pick_seismogram(self, event, data_manager, display_manager):
        ''' Create a pick in a seismogram view.
        '''
        if event.inaxes is None:
            return

        cur_axes = self.view.dataAxes

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

        # Get the channel of the pick.
        scnl = self.view.GetParent().scnl
        cur_channel = self.parent.project.geometry_inventory.get_channel(station = scnl[0],
                                                                         name = scnl[1],
                                                                         network = scnl[2],
                                                                         location = scnl[3])
        if not cur_channel:
            self.logger.error('No channel for SCNL %s found in the inventory.', scnl)
        elif len(cur_channel) > 1:
            self.logger.error("More than one channel returned from the inventory for SCNL %s. This shouldn't happen.", scnl)
        else:
            # Create the pick and write it to the database.
            cur_catalog = self.library.catalogs[self.selected_catalog_name]
            search_win_start = self.parent.displayManager.startTime
            search_win_end = self.parent.displayManager.endTime
            cur_pick = cur_catalog.get_pick(start_time = search_win_start,
                                            end_time = search_win_end,
                                            label = self.pref_manager.get_value('label'),
                                            station = scnl[0])

            if len(cur_pick) == 1:
                cur_pick = cur_pick[0]
                cur_pick.time = UTCDateTime(snap_x)
                cur_pick.amp1 = snap_y
                cur_pick.write_to_database(self.parent.project)
            elif len(cur_pick) == 0:
                cur_channel = cur_channel[0]
                cur_pick = pick_core.Pick(label = self.pref_manager.get_value('label'),
                                          time = UTCDateTime(snap_x),
                                          amp1 = snap_y,
                                          channel = cur_channel)
                cur_catalog.add_picks([cur_pick,])
                cur_pick.write_to_database(self.parent.project)
            else:
                self.logger.error("More than one pick returned for label %s. Don't know what to do.", self.pref_manager.get_value('label'))
                return

            # Create the pick line in all channels of the station.
            self.view.GetGrandParent().plot_annotation_vline(x = snap_x,
                                                             label = cur_pick.label,
                                                             key = cur_pick.rid,
                                                             color = 'r')

            # Make the pick lines visible.
            self.view.GetGrandParent().draw()



    def on_select_catalog(self):
        ''' Handle the catalog selection.
        '''
        self.selected_catalog_name = self.pref_manager.get_value('pick_catalog')
        # Load the catalog from the database.
        self.library.clear()
        self.library.load_catalog_from_db(project = self.parent.project,
                                          name = self.selected_catalog_name)

        # TODO: When the pick catalog selector plugin is available, load the
        # picks using this plugin.
        # Load the picks for the selected timespan.
        cur_catalog = self.library.catalogs[self.selected_catalog_name]
        cur_catalog.clear_picks()
        cur_catalog.load_picks(project = self.parent.project,
                               start_time = self.parent.displayManager.startTime,
                               end_time = self.parent.displayManager.endTime)


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

            if curKey in self.data.keys():
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
            ctrl.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            ctrl.Refresh()
            return True

    ## The method called when entering the dialog.      
    def TransferToWindow(self):
        return True

    ## The method called when leaving the dialog.  
    def TransferFromWindow(self):
        return True

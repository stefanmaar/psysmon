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

class MeasurePoint(InteractivePlugin):
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

        self.library = pick_core.Library('pick library')

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
                                          tool_tip = 'Select a pick catalog to work on.')
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

        return fold_panel


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

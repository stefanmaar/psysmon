# LICENSE
#
# This file is part of pSysmon.
#
# If you use pSysmon in any program or publication, please inform and
# acknowledge its author Stefan Mertl (info@stefanmertl.com).
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
'''
The pSysmon GUI module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)

This module contains the graphical user interface (GUI) of the pSysmon 
main program.
'''

import wx
import logging

class EditProjectPreferencesDlg(wx.Dialog):

    def __init__(self, parent = None, preferences = None, size = (400, 600)):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Project Preferences", style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, size = size)

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.pref = preferences

        # Create the dialog buttons.
        okButton = wx.Button(self, wx.ID_OK)
        cancelButton = wx.Button(self, wx.ID_CANCEL)
        okButton.SetDefault()

        # Create the client's options pane.
        #(curLabel, curPanel) = self.clientOptionPanels[client.mode]
        #self.optionsPanel = curPanel(parent=self, client=client, project=self.psyBase.project)

        # The main dialog sizer.
        sizer = wx.GridBagSizer(5,5)

        #sizer.Add(self.optionsPanel, pos=(0,0), flag=wx.EXPAND|wx.ALL, border = 5)
        self.listbook = wx.Listbook(parent = self,
                                    id = wx.ID_ANY,
                                    style = wx.BK_LEFT)
        self.build_pref_listbook()
        sizer.Add(self.listbook, pos = (0,0),
                  flag = wx.ALL|wx.EXPAND, border = 5)

        # The button sizer.
        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        sizer.Add(btnSizer, pos=(1,0), flag=wx.ALIGN_RIGHT|wx.ALL, border=5)

        sizer.AddGrowableRow(0)
        sizer.AddGrowableCol(0)

        self.SetSizer(sizer)


    def build_pref_listbook(self):
        ''' Build the listbook based on the project preferences.

        '''
        pagenames = sorted(self.pref.pages.keys())

        for cur_pagename in pagenames:
            panel = PrefPagePanel(parent = self, 
                                  id = wx.ID_ANY,
                                  page = self.pref.pages[cur_pagename]
                                 )
            self.listbook.AddPage(panel, cur_pagename)



class PrefPagePanel(wx.Panel):
    ''' A panel representing a page of the preference manager.

    '''
    def __init__(self, parent = None, id = wx.ID_ANY, page = None):
        wx.Panel.__init__(self, parent = parent, id = id)

        self.page = page

        self.init_ui()


    def init_ui(self):
        ''' Build the gui elements required by the preference items.

        '''
        sizer = wx.BoxSizer(wx.VERTICAL)
        # Find all groups.
        groups = list(set([x.group for x in self.page]))

        for cur_group in groups:
            groupitems = [x for x in self.page if x.group == cur_group]
            for cur_item in groupitems:
                guiclass = cur_item.guiclass
                if guiclass is not None:
                    gui_element = guiclass(name = cur_item.name,
                                           pref_item = cur_item,
                                           size = (100, 10),
                                           parent = self
                                          )
                    sizer.Add(gui_element, 1)
                else:
                    self.logger.warning('Item %s of mode %s has no guiclass.', 
                            cur_item.name, cur_item.mode)

        self.SetSizer(sizer)








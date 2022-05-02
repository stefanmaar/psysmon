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

from psysmon.core.guiBricks import PrefPagePanel


class ListbookPrefDialog(wx.Dialog):

    def __init__(self, parent = None, preferences = None,
                 size = (400, 600), title = 'preferences'):
        ''' Initialize the instance.
        '''
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title = title,
                           style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
                           size = size)

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.pref = preferences

        # Create the dialog buttons.
        okButton = wx.Button(self, wx.ID_OK)
        cancelButton = wx.Button(self, wx.ID_CANCEL)
        okButton.SetDefault()

        # The main dialog sizer.
        sizer = wx.GridBagSizer(5, 5)

        self.listbook = wx.Listbook(parent = self,
                                    id = wx.ID_ANY,
                                    style = wx.BK_LEFT)
        self.build_pref_listbook()
        sizer.Add(self.listbook, pos = (0, 0),
                  flag = wx.ALL | wx.EXPAND, border = 5)

        # The button sizer.
        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        sizer.Add(btnSizer, pos=(1, 0), flag=wx.ALIGN_RIGHT | wx.ALL, border=5)

        sizer.AddGrowableRow(0)
        sizer.AddGrowableCol(0)

        self.SetSizerAndFit(sizer)


    def build_pref_listbook(self):
        ''' Build the listbook based on the project preferences.

        '''
        # Create pages only for pages with groups
        pages = [x for x in self.pref.pages if len(x) > 0]

        for cur_page in pages:
            panel = PrefPagePanel(parent = self,
                                  id = wx.ID_ANY,
                                  page = cur_page)
            self.listbook.AddPage(panel, cur_page.name)

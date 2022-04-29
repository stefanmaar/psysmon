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

import wx

import psysmon.gui.validator as psy_val


class ProjectLoginDlg(wx.Dialog):
    
    def __init__(self, size=(300, 200)):
        ''' Initialize the instance.
        '''
        wx.Dialog.__init__(self, None, wx.ID_ANY, "Project login", size=size)

        # Use standard button IDs.
        okButton = wx.Button(self, wx.ID_OK)
        okButton.SetDefault()
        cancelButton = wx.Button(self, wx.ID_CANCEL)

        # Layout using sizers.
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.label = {}
        self.edit = {}

        sizer.Add(self.createDialogFields(), 0, wx.EXPAND|wx.ALL, 5)

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        sizer.Add(btnSizer, 0, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

        self.edit['user'].SetFocus()

        # Add the validators.
        self.edit['user'].SetValidator(psy_val.NotEmptyValidator())

        # Bind the events.
        self.Bind(wx.EVT_BUTTON, self.onOk, okButton)


    def onOk(self, event):  
        isValid = self.Validate()

        if(isValid):
            self.userData = {}
            for _, curKey, _ in self.dialogData():
                self.userData[curKey] = self.edit[curKey].GetValue()
                self.Destroy()


    def dialogData(self):
        return(("user:", "user", wx.TE_RIGHT),
               ("password:", "pwd", wx.TE_PASSWORD|wx.TE_RIGHT))
    

    def createDialogFields(self):
        dialogData = self.dialogData()
        fgSizer = wx.FlexGridSizer(len(dialogData), 2, 5, 5)

        for curLabel, curKey, curStyle in dialogData:
            self.label[curKey] = wx.StaticText(self, wx.ID_ANY, curLabel)
            self.edit[curKey] = wx.TextCtrl(self, size=(200, -1), 
                                            style=curStyle)

            fgSizer.Add(self.label[curKey], 0, wx.ALIGN_RIGHT)
            fgSizer.Add(self.edit[curKey], 0, wx.EXPAND)

        fgSizer.AddGrowableCol(1)
        return fgSizer

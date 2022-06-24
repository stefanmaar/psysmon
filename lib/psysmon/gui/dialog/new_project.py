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
import os

import wx

import psysmon
import psysmon.gui.validator as psy_val


class CreateNewProjectDlg(wx.Dialog):
    ''' The create a new project dialog window.

    This window is used to get the parameters needed to create a new pSysmon 
    project.
    ''' 

    def __init__(self, psyBase, parent, size=(500, 200)):
        ''' Initialize the instance.
        '''
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Create a new project", 
                           size=size, 
                           style=wx.DEFAULT_DIALOG_STYLE)

        # The logger.
        self.logger = psysmon.get_logger(self)
        
        self.psyBase = psyBase

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

        # Add some default values.
        self.edit['db_host'].SetValue('localhost')

        # Add the validators.
        self.edit['name'].SetValidator(psy_val.NotEmptyValidator())
        self.edit['base_dir'].SetValidator(psy_val.NotEmptyValidator())
        self.edit['db_host'].SetValidator(psy_val.NotEmptyValidator())
        self.edit['user_name'].SetValidator(psy_val.NotEmptyValidator())
        self.edit['agency_uri'].SetValidator(psy_val.NotEmptyValidator())
        self.edit['author_uri'].SetValidator(psy_val.NotEmptyValidator())
        #self.edit['userPwd'].SetValidator(psy_val.NotEmptyValidator())

        # Show the example URI.
        self.edit['resource_id'].SetValue('smi:AGENCY_URI.AUTHOR_URI/psysmon/NAME')

        # Bind the events.
        self.Bind(wx.EVT_BUTTON, self.onOk, okButton)
        self.Bind(wx.EVT_TEXT, self.onUpdateRid, self.edit['name'])
        self.Bind(wx.EVT_TEXT, self.onUpdateRid, self.edit['author_uri'])
        self.Bind(wx.EVT_TEXT, self.onUpdateRid, self.edit['agency_uri'])

    def onUpdateRid(self, event):
        agency_uri = self.edit['agency_uri'].GetValue()
        author_uri = self.edit['author_uri'].GetValue()
        project_uri = self.edit['name'].GetValue()
        project_uri = project_uri.lower().replace(' ', '_')

        rid = 'smi:' + agency_uri + '.' + author_uri + '/psysmon/' + project_uri
        self.edit['resource_id'].SetValue(rid)

    def onBaseDirBrowse(self, event):

        # Create the directory dialog.
        dlg = wx.DirDialog(self, message="Choose a directory:",
                           defaultPath=self.edit['base_dir'].GetValue(),
                           style=wx.DD_DEFAULT_STYLE
                           #| wx.DD_DIR_MUST_EXIST
                           #| wx.DD_CHANGE_DIR
                           )

        # Get the selected directory
        if dlg.ShowModal() == wx.ID_OK:
            self.edit['base_dir'].SetValue(dlg.GetPath())

        # Only destroy a dialog after you're done with it.
        dlg.Destroy()

    def onOk(self, event):  
        isValid = self.Validate()

        if(isValid):
            keys_2_pass = ['name', 'base_dir', 'db_host', 'user_name', 'user_pwd',
                           'author_name', 'author_uri', 'agency_name', 'agency_uri']
            projectData = {}
            for _, curKey, _, _, _, _ in self.dialogData():
                if curKey in keys_2_pass:
                    projectData[curKey] = self.edit[curKey].GetValue()

            try:
                self.createProject(projectData)
                self.GetParent().enableGuiElements(mode = 'project')
                self.Destroy()
            except Exception:
                raise


    def dialogData(self):
        return(("name:", "name", wx.TE_RIGHT, False, "", 'edit'),
               ("base directory:", "base_dir", wx.TE_LEFT, True, self.onBaseDirBrowse, 'edit'),
               ("database host:", "db_host", wx.TE_RIGHT, False, "", 'edit'),
               ("username:", "user_name", wx.TE_RIGHT, False, "", 'edit'),
               ("user pwd:", "user_pwd", wx.TE_PASSWORD|wx.TE_RIGHT, False, "", 'edit'),
               ("author name:", "author_name", wx.TE_RIGHT, False, "", 'edit'),
               ("author URI:", "author_uri", wx.TE_RIGHT, False, "", 'edit'),
               ("agency name:", "agency_name", wx.TE_RIGHT, False, "", 'edit'),
               ("agency URI:", "agency_uri", wx.TE_RIGHT, False, "", 'edit'),
               ("resource ID:", "resource_id", wx.TE_RIGHT, False, "", 'static')
               )

    def createDialogFields(self):
        dialogData = self.dialogData()
        gbSizer = wx.GridBagSizer(5, 5)
        rowCount = 0

        for curLabel, curKey, curStyle, hasBrowseBtn, curBtnHandler, curType in dialogData:
            self.label[curKey] = wx.StaticText(self, wx.ID_ANY, curLabel)
            self.edit[curKey] = wx.TextCtrl(self, size=(300, -1), 
                                            style=curStyle)

            if curType == 'static':
                self.edit[curKey].SetEditable(False)
                self.edit[curKey].Disable()

            if(hasBrowseBtn):
                browseButton = wx.Button(self, wx.ID_ANY, "browse", (50,-1))
                gbSizer.Add(self.label[curKey], pos=(rowCount, 0),
                            flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL)
                gbSizer.Add(self.edit[curKey], pos=(rowCount, 1),
                            flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.EXPAND|wx.ALL)
                gbSizer.Add(browseButton, pos=(rowCount, 2),
                            flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.EXPAND|wx.ALL)

                self.Bind(wx.EVT_BUTTON, curBtnHandler, browseButton)
            elif(curStyle == 'static'):
                gbSizer.Add(self.label[curKey], pos=(rowCount, 0),
                            flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
                gbSizer.Add(self.edit[curKey], pos=(rowCount, 1),
                            flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
            else:
                gbSizer.Add(self.label[curKey], pos=(rowCount, 0),
                            flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
                gbSizer.Add(self.edit[curKey], pos=(rowCount, 1),
                            flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

            rowCount += 1

        return gbSizer


    def createProject(self, projectData):
        ''' Create a new psysmon project.
        '''
        try:
            self.psyBase.createPsysmonProject(**projectData)

            # Add the project path to the filehistory.
            project_dir = self.psyBase.project.projectDir
            project_file = self.psyBase.project.projectFile
            filepath = os.path.join(project_dir,
                                    project_file)
            self.Parent.filehistory.AddFileToHistory(filepath)
            # Update the collection panel display.
            self.Parent.collectionPanel.refreshCollection()

            # Activate the user interfaces.
            self.Parent.enableGuiElements(mode = 'project')

            # Set the loaded project name as the title.
            self.Parent.SetTitle(self.psyBase.project.name)

        except Exception as e:
            self.logger.error("Error while creating the project: %s", e)
            raise

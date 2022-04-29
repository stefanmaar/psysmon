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

from sqlalchemy.exc import SQLAlchemyError
import wx

import psysmon.gui.validator as psy_val


class CreateNewDbUserDlg(wx.Dialog):

    def __init__(self, psyBase, parent=None, size=(300, 200)):
        ''' Initialize the instance.
        '''
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Create a new DB user",
                           size=size)

        self.psyBase = psyBase

        # Use standard button IDs.
        okButton = wx.Button(self, wx.ID_OK)
        okButton.SetDefault()
        cancelButton = wx.Button(self, wx.ID_CANCEL)

        # Layout using sizers.
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.label = {}
        self.edit = {}

        sizer.Add(self.createDialogFields(), 0, wx.EXPAND | wx.ALL, 5)

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        sizer.Add(btnSizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

        # Add the validators.
        self.edit['rootUser'].SetValidator(psy_val.NotEmptyValidator())
        self.edit['mysqlHost'].SetValidator(psy_val.NotEmptyValidator())
        self.edit['userName'].SetValidator(psy_val.NotEmptyValidator())
        self.edit['retypeUserPwd'].SetValidator(psy_val.IsEqualValidator(self.edit['userPwd']))


        # Bind the events.
        self.Bind(wx.EVT_BUTTON, self.onOk, okButton)


    def onOk(self, event):
        isValid = self.Validate()

        if(isValid):
            userData = {}
            for _, curKey, _ in self.dialogData():
                userData[curKey] = self.edit[curKey].GetValue()

            userCreated = self.createUser(userData)
            #pub.sendMessage("createNewDbUserDlg.createUser", userData)
            if(userCreated):
                # Set the status message.
                statusString = "Created the user %s successfully." % userData['userName']
                self.GetParent().logger.info(statusString)

                # Close the dialog.
                self.Destroy()

            else:
                # Set the status message.
                statusString = "Error while creating the user %s." % userData['userName']
                if not self.GetParent():
                    self.GetParent().logger.debug("NO PARENT")
                else:
                    self.GetParent().logger.error(statusString)



    def dialogData(self):
        return(("root user:", "rootUser", wx.TE_RIGHT),
               ("root pwd:", "rootPwd", wx.TE_PASSWORD | wx.TE_RIGHT),
               ("mysql host:", "mysqlHost", wx.TE_RIGHT),
               ("username:", "userName", wx.TE_RIGHT),
               ("user pwd:", "userPwd", wx.TE_PASSWORD | wx.TE_RIGHT),
               ("retype user pwd:", "retypeUserPwd", wx.TE_PASSWORD | wx.TE_RIGHT)
               )

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



    def createUser(self, userData):

        try:
            self.psyBase.createPsysmonDbUser(userData['rootUser'],
                                             userData['rootPwd'],
                                             userData['mysqlHost'],
                                             userData['userName'],
                                             userData['userPwd'])
            return True
        except SQLAlchemyError as e:
            msg = "An error occured when trying to create the pSysmon " \
                  "database user:\n%s" % str(e)
            user_db = "psysmon_" + userData['userName']
            query_db = "CREATE DATABASE IF NOT EXISTS %s;" % user_db
            query_user = "CREATE USER %s@'%s' IDENTIFIED BY 'YOUR_PASSWORD';" % (userData['userName'], userData['mysqlHost'])
            query_grant = "GRANT ALL ON %s.* TO '%s'@'localhost';" % (user_db,
                                                                      userData['userName'])

            msg = "With new mariaDB installations, there is a restricted " \
                  "root access to the database.\nYou have to create the " \
                  "database user manually.\nPlease execute the following " \
                  "commands as root in the mariaDB command prompt. Replace " \
                  "YOUR_PASSWORD with your desired password or an empty " \
                  "string ('') if no password is required.:\n\n\n"
            msg += query_db + '\n' + query_user + '\n' + query_grant
            ScrolledMessageDialog = wx.lib.dialogs.ScrolledMessageDialog
            dlg = ScrolledMessageDialog(self,
                                        msg,
                                        'Error when creating the user.')
            #dlg = wx.MessageDialog(None, msg,
            #                       "MySQL database error.",
            #                       wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            return False

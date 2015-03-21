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
from psysmon.core.guiBricks import PrefPagePanel

class ListbookPrefDialog(wx.Dialog):

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
        # Create pages only for pages with preference items.
        pagenames = sorted([x[0] for x in self.pref.pages.iteritems() if x[1]])

        for cur_pagename in pagenames:
            panel = PrefPagePanel(parent = self,
                                  id = wx.ID_ANY,
                                  items = self.pref.pages[cur_pagename]
                                 )
            self.listbook.AddPage(panel, cur_pagename)



## The EditDialog class.
#
# This class provides an easy to use edit dialog for pSysmon collection nodes.
# One can choose from a set of fields which can be used to change the values 
# of the collection node properties.        
class NotebookPrefDialog(wx.Frame):

    ## The constructor
    #
    # @param self The object pointer.
    # @param options The CollectionNode options being edited with the EditDialog.
    # @param parent The parent wxPython window.
    # @param id The wxPython id.
    # @param title The dialog's title.
    # @param size The dialog's size.
    def __init__(self, options, parent=None, id=wx.ID_ANY, title='edit node', 
                 size=(400,600)):
        wx.Frame.__init__(self, parent=parent, 
                          id=id, 
                          title=title, 
                          pos=wx.DefaultPosition,
                          style=wx.DEFAULT_FRAME_STYLE)
        self.SetMinSize(size)  

        ## The node options being edited with the dialog.
        #
        self.options = options


        ## A dictionary of pages created in the notebook.
        #
        self.pages = {}

        ## A dictionary of page sizers associated with the pages.
        #
        self.pageSizers = {}

        ## The list of container panels holding the fields.
        #
        self.fieldContainer = {}

        # Create the UI elements.
        self.initUI()


    ## Create the dialog's user interface.  
    #
    def initUI(self):
        # The dialog's sizer.
        self.sizer = wx.GridBagSizer(5,10)
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(0)
        self.notebook = wx.Notebook(parent=self, id=wx.ID_ANY, style=wx.BK_DEFAULT)
        self.sizer.Add(self.notebook, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=2)  

        # Create the dialog buttons.
        okButton = wx.Button(self, wx.ID_OK)
        okButton.SetDefault()
        cancelButton = wx.Button(self, wx.ID_CANCEL)
        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        self.sizer.Add(btnSizer, pos=(1,0), flag=wx.EXPAND|wx.ALL, border=4)

        self.SetSizerAndFit(self.sizer)

        # Bind the button events.
        self.Bind(wx.EVT_BUTTON, self.onOk, okButton)
        self.Bind(wx.EVT_BUTTON, self.onCancel, cancelButton)

        #self.Bind(wx.EVT_SIZE, self.onResize)



    ## Handle the ok button click.
    #
    # Update all options values and close the dialog.  
    def onOk(self, event):
        for curContainer in self.fieldContainer.values():
            curContainer.setOptionsValue()

        self.Destroy()

    ## Handle the cancel button click.
    # 
    # Close the dialog.
    def onCancel(self, event):
        self.Destroy()


    def onResize(self, event):
        self.refit()


    def addPage(self, name):
        # All fields are children of the fieldPanel.
        # The field elements should be parents of the same panel to ensure a 
        # consistent tab traversal. 
        self.pages[name] = wx.Panel(self.notebook, wx.ID_ANY)
        self.pageSizers[name] = wx.GridBagSizer(5,10)
        self.pageSizers[name].AddGrowableCol(0)
        self.pages[name].SetSizer(self.pageSizers[name])
        #self.sizer.Add(self.fieldPanel, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=0)

        self.notebook.AddPage(self.pages[name], name) 


    def addContainer(self, container, pageName):
        if not self.pages:
            print "No dialog pages found. Create one first."
            return

        if not pageName in self.pages.keys():
            print "The specified page is not in the container list."
            return

        container.Reparent(self.pages[pageName])
        row = len(self.fieldContainer)

        print "Adding container at row %d" % row
        self.pageSizers[pageName].Add(container, pos=(row, 0), flag=wx.EXPAND|wx.ALL, border=4)

        container.options = self.options

        print "Adding container with name %s to the dictionary" % container.GetName()
        self.fieldContainer[container.GetName()] = container

        self.notebook.Fit()
        self.Fit()

    ## Add a field to the dialog.
    #
    # The field is added to the dialog fieldlist and the field elements are 
    # initialized with the options values.
    def addField(self, field, container):

        if not self.fieldContainer:
            print "No field container found. Create one first."
            return

        if not container in self.fieldContainer.values():
            print "The specified container is not in the container list."
            return

        container.addField(field)
        container.Fit()
        self.notebook.Fit()
        self.Fit()
        #field.SetSize(field.GetBestSize())


    def refit(self):
        self.notebook.Fit()
        for curContainer in self.fieldContainer.values():
            curContainer.SetSize(curContainer.GetBestSize())

            for curField in curContainer.fieldList:
                curField.SetSize(curField.GetBestSize())

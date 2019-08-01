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
from psysmon.core.plugins import OptionPlugin
from psysmon.artwork.icons import iconsBlack16 as icons
import wx.lib.mixins.listctrl as listmix
from psysmon.core.gui import psyContextMenu
from wx.lib.stattext import GenStaticText as StaticText
import copy

import psysmon.core.preferences_manager as preferences_manager


class ProcessingStack(OptionPlugin):
    '''

    '''
    nodeClass = 'common'

    def __init__(self, with_run_button = True):
        ''' The constructor

        '''
        OptionPlugin.__init__(self,
                              name = 'processing stack',
                              category = 'proc',
                              tags = ['process', 'data']
                             )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.layers_1_icon_16

        self.with_run_button = with_run_button



    def buildFoldPanel(self, parent):
        foldPanel = wx.Panel(parent = parent, id = wx.ID_ANY)

        self.processingStack = self.parent.processing_stack

        # Layout using sizers.
        sizer = wx.GridBagSizer(5,5)
        buttonSizer = wx.BoxSizer(wx.VERTICAL)

        # Create the buttons to control the stack.
        addButton = wx.Button(foldPanel, wx.ID_ANY, "add")
        removeButton = wx.Button(foldPanel, wx.ID_ANY, "remove")


        # Fill the button sizer.
        buttonSizer.Add(addButton, 0, wx.ALL)
        buttonSizer.Add(removeButton, 0, wx.ALL)

        if self.with_run_button is True:
            runButton = wx.Button(foldPanel, wx.ID_ANY, "run")
            buttonSizer.Add(runButton, 0, wx.ALL)

        # Fill the nodes list with the nodes in the processing stack.
        nodeNames = [x.name for x in self.processingStack.nodes]
        isActive = [m for m,x in enumerate(self.processingStack) if x.isEnabled() == True]

        self.nodeListBox = wx.CheckListBox(parent = foldPanel,
                                           id = wx.ID_ANY,
                                           choices = nodeNames,
                                           size = (100, -1))
        self.nodeListBox.SetChecked(isActive)

        # By default select the first processing node.
        self.nodeListBox.SetSelection(0)
        self.nodeOptions = self.processingStack[0].getEditPanel(foldPanel)

        # Add the elements to the main sizer.
        sizer.Add(self.nodeListBox, pos=(0,0), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)
        sizer.Add(buttonSizer, pos=(0,1), flag=wx.TOP|wx.BOTTOM, border=1)
        sizer.Add(self.nodeOptions, pos=(1,0), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)

        sizer.AddGrowableRow(0)
        sizer.AddGrowableRow(1)
        sizer.AddGrowableCol(0)

        # Bind the events.
        foldPanel.Bind(wx.EVT_BUTTON, self.onAdd, addButton)
        foldPanel.Bind(wx.EVT_LISTBOX, self.onNodeSelected, self.nodeListBox)
        foldPanel.Bind(wx.EVT_CHECKLISTBOX, self.onBoxChecked, self.nodeListBox)
        if self.with_run_button is True:
            foldPanel.Bind(wx.EVT_BUTTON, self.onRun, runButton)

        foldPanel.SetSizer(sizer)

        self.foldPanel = foldPanel

        return foldPanel


    def updateNodeList(self):
        self.nodeListBox.Clear()
        nodeNames = [x.name for x in self.processingStack.nodes]
        isActive = [m for m,x in enumerate(self.processingStack) if x.isEnabled() == True]
        self.nodeListBox.AppendItems(nodeNames)
        self.nodeListBox.SetChecked(isActive)



    def onRun(self, event):
        ''' Re-run the processing stack.
        '''
        self.parent.update_display()


    def onAdd(self, event):
        ''' Add a processing node to the stack.

        Open a dialog field to select from the available processing nodes.
        '''
        dlg = PStackAddNodeDialog(parent = self.foldPanel, availableNodes = self.parent.processingNodes)
        val = dlg.ShowModal()

        if val == wx.ID_OK:
            node2Add = dlg.getSelection()
            self.processingStack.addNode(node2Add, self.nodeListBox.GetSelection()+1) 
            self.updateNodeList()

        dlg.Destroy()


    def onNodeSelected(self, event):
        index = event.GetSelection()
        #selectedNode = event.GetString()
        sizer = self.foldPanel.GetSizer()
        sizer.Detach(self.nodeOptions)
        self.nodeOptions.Destroy()
        self.nodeOptions = self.processingStack[index].getEditPanel(self.foldPanel)
        sizer.Add(self.nodeOptions, pos=(1,0), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)
        sizer.Layout() 



    def onBoxChecked(self, event):
        index = event.GetSelection()
        label = self.nodeListBox.GetString(index)
        self.logger.debug('Checked item %d, label %s.', index, label)

        self.processingStack[index].toggleEnabled()




class ProcessingStackPrefItem(preferences_manager.PreferenceItem):
    '''
    '''
    def __init__(self, name, value, **kwargs):
        preferences_manager.PreferenceItem.__init__(self, name = name, value = value,
                                                    mode = 'processing_stack', **kwargs)

        self.gui_class = PStackEditField


    @property
    def settings(self):
        '''
        '''
        settings = []
        if self.value:
            for cur_node in self.value:
                settings.append(cur_node.settings)

        return settings



class PStackEditField(wx.Panel):

    def __init__(self, name, pref_item, size, parent = None):
        ''' Initialize the instance.
        '''
        wx.Panel.__init__(self, parent = parent, size = size, id = wx.ID_ANY)

        self.name = name

        self.pref_item = pref_item

        self.size = size

        self.label = name + ":"

        self.labelElement = None

        self.controlElement = None

        self.sizer = wx.GridBagSizer(5, 5)


        # Create the field label.
        self.labelElement = StaticText(parent=self,
                                       ID=wx.ID_ANY,
                                       label=self.label,
                                       style=wx.ALIGN_LEFT)

        self.sizer.Add(self.labelElement, pos = (0,0), flag = wx.EXPAND|wx.ALL, border = 0)

        self.controlElement = PStackEditPanel(parent = self,
                                              size = (-1, 300))

        self.sizer.Add(self.controlElement, pos = (1,0), flag = wx.EXPAND|wx.ALL, border = 0)
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(1)

        self.SetSizer(self.sizer)


    def __del__(self):
        self.pref_item.remove_gui_element(self)





class PStackEditPanel(wx.Panel):
    '''
    '''
    def __init__(self, parent, size, id = wx.ID_ANY):
        wx.Panel.__init__(self, parent = parent, id = id, size = size)

        # Layout using sizers.
        sizer = wx.GridBagSizer(5,5)
        buttonSizer = wx.BoxSizer(wx.VERTICAL)

        # Create the buttons to control the stack.
        addButton = wx.Button(self, wx.ID_ANY, "add")
        removeButton = wx.Button(self, wx.ID_ANY, "remove")

        # Fill the button sizer.
        buttonSizer.Add(addButton, 0, wx.ALL)
        buttonSizer.Add(removeButton, 0, wx.ALL)

        # Fill the nodes list with the nodes in the processing stack.
        self.selected_nodes = self.GetParent().pref_item.value
        node_names = [x.name for x in self.selected_nodes]
        is_active = [m for m,x in enumerate(self.selected_nodes) if x.isEnabled() == True]

        self.nodeListBox = wx.CheckListBox(parent = self,
                                           id = wx.ID_ANY,
                                           choices = node_names,
                                           size = (100, -1))
        self.nodeListBox.SetChecked(is_active)

        # By default select the first processing node.
        self.nodeListBox.SetSelection(0)
        self.nodeOptions = self.selected_nodes[0].getEditPanel(self)


        # Add the elements to the main sizer.
        sizer.Add(self.nodeListBox, pos=(0,0), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)
        sizer.Add(buttonSizer, pos=(0,1), flag=wx.TOP|wx.BOTTOM, border=1)
        sizer.Add(self.nodeOptions, pos=(1,0), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)

        sizer.AddGrowableRow(0)
        sizer.AddGrowableRow(1)
        sizer.AddGrowableCol(0)

        self.SetSizer(sizer)

        # Bind the events.
        self.Bind(wx.EVT_BUTTON, self.on_add_button_clicked, addButton)
        self.Bind(wx.EVT_LISTBOX, self.on_node_selected, self.nodeListBox)
        self.Bind(wx.EVT_CHECKLISTBOX, self.on_node_checked, self.nodeListBox)



    def on_add_button_clicked(self, event):
        ''' Add a processing node to the stack.

        Open a dialog field to select from the available processing nodes.
        '''
        dlg = PStackAddNodeDialog(parent = self,
                                  availableNodes = self.GetParent().pref_item.limit)
        val = dlg.ShowModal()

        if val == wx.ID_OK:
            node2Add = dlg.getSelection()
            position = self.nodeListBox.GetSelection() + 1
            node = copy.deepcopy(node2Add)
            if position == -1:
                self.selected_nodes.append(node)
            else:
                self.selected_nodes.insert(position, node)
            self.update_node_list()

        dlg.Destroy()


    def on_node_selected(self, event):
        index = event.GetSelection()
        sizer = self.GetSizer()
        sizer.Detach(self.nodeOptions)
        self.nodeOptions.Destroy()
        self.nodeOptions = self.selected_nodes[index].getEditPanel(self)
        sizer.Add(self.nodeOptions, pos=(1,0), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)
        sizer.Layout()


    def update_node_list(self):
        self.nodeListBox.Clear()
        node_names = [x.name for x in self.selected_nodes]
        is_active = [m for m,x in enumerate(self.selected_nodes) if x.isEnabled() == True]
        self.nodeListBox.AppendItems(node_names)
        self.nodeListBox.SetChecked(is_active)


    def on_node_checked(self, event):
        index = event.GetSelection()
        self.selected_nodes[index].toggleEnabled()


class PStackAddNodeDialog(wx.Dialog):
    ''' Dialog to add a processing node to the stack.

    '''
    def __init__(self, parent=None, availableNodes = None, size = (200,400)):
        ''' The constructor.
        '''
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Add a processing node", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER, size=size)

        # Use standard button IDs.
        okButton = wx.Button(self, wx.ID_OK)
        okButton.SetDefault()
        cancelButton = wx.Button(self, wx.ID_CANCEL)

        # Sizer to layout the gui elements.
        sizer = wx.GridBagSizer(5,5)
        btnSizer = wx.StdDialogButtonSizer()

        self.nodeInventoryPanel = PStackNodeInventoryPanel(parent = self, availableNodes = availableNodes)

        # Add the buttons to the button sizer. 
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()

        # Add the elements to the base sizer.        
        sizer.Add(self.nodeInventoryPanel, pos=(0,0), flag = wx.EXPAND|wx.ALL, border= 2)
        sizer.Add(btnSizer, pos=(1,0), span=(1,2), flag=wx.ALIGN_RIGHT|wx.ALL, border=5)
        sizer.AddGrowableRow(0)
        sizer.AddGrowableCol(0)

        self.SetSizerAndFit(sizer)


    def getSelection(self):
        return self.nodeInventoryPanel.selectedNode 




class PStackNodeInventoryPanel(wx.Panel, listmix.ColumnSorterMixin):

    def __init__(self, parent, availableNodes, id=wx.ID_ANY):
        wx.Panel.__init__(self, parent = parent, id = id)

        self.availableNodes = availableNodes

        self.selectedNode = None

        self.itemDataMap = {}

        # Create the icons for column sorting.
        self.il = wx.ImageList(16, 16)
        self.sm_up = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_OTHER, (16,16)))
        self.sm_dn = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_OTHER, (16,16)))

        # The sizer used for the panel layout.
        sizer = wx.GridBagSizer(5, 5)

        # The search field to do search while typing.
        self.searchButton = wx.SearchCtrl(self, size=(200, 30), style=wx.TE_PROCESS_ENTER)
        self.searchButton.SetDescriptiveText('Search processing nodes')
        self.searchButton.ShowCancelButton(True)
        self.Bind(wx.EVT_TEXT, self.onDoSearch, self.searchButton)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.onDoSearch, self.searchButton)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.onCancelSearch, self.searchButton)
        self.Bind(wx.EVT_TEXT_ENTER, self.onDoSearch, self.searchButton)

        sizer.Add(self.searchButton, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=2)

        # The processing node listbox.
        self.nodeListCtrl = NodeListCtrl(self, id=wx.ID_ANY,
                                 style=wx.LC_REPORT 
                                 | wx.BORDER_NONE
                                 | wx.LC_SINGLE_SEL
                                 | wx.LC_SORT_ASCENDING
                                 )

        self.nodeListCtrl.SetImageList(self.il, wx.IMAGE_LIST_SMALL)


        columns = {1: 'name', 2: 'mode', 3: 'category', 4: 'tags'}

        for colNum, name in columns.items():
            self.nodeListCtrl.InsertColumn(colNum, name)

        self.fillNodeList(self.availableNodes)

        sizer.Add(self.nodeListCtrl, pos=(1, 0), flag=wx.EXPAND|wx.ALL, border=0)

        sizer.AddGrowableCol(0)
        sizer.AddGrowableRow(1)

        self.SetSizerAndFit(sizer)

        # Bind the select item event to track the selected processing
        # node.
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onNodeItemSelected, self.nodeListCtrl)



    def onDoSearch(self, evt):
        foundNodes = self.searchNodes(self.searchButton.GetValue())
        self.updateNodeInvenotryList(foundNodes)


    def onCancelSearch(self, evt):
        self.fillNodeList(self.availableNodes)
        self.searchButton.SetValue(self.searchButton.GetDescriptiveText())


    def onNodeItemSelected(self, evt):
        nodeName = evt.GetItem().GetText()
        for curNode in self.availableNodes:
            if nodeName == curNode.name:
                self.selectedNode = curNode


    def searchNodes(self, searchString):
        ''' Find the processing nodes containing the *searchString* in their 
        name or their tags.


        Parameters
        ----------
        searchString : String
            The string to search for.


        Returns
        -------
        nodesFound : List of :class:`~psysmon.core.packageNodes.CollectionNode` instances.
            The nodes found matching the *searchString*.
        '''
        nodesFound = {}
        for curNode in self.availableNodes:
            if searchString in ','.join([curNode.name]+curNode.tags):
                nodesFound[curNode.name] = curNode

        return nodesFound



    def fillNodeList(self, nodeTemplates):
        index = 0
        self.nodeListCtrl.DeleteAllItems()

        for curNode in nodeTemplates:
            self.nodeListCtrl.InsertStringItem(index, curNode.name)
            self.nodeListCtrl.SetStringItem(index, 1, curNode.mode)
            self.nodeListCtrl.SetStringItem(index, 2, curNode.category)
            self.nodeListCtrl.SetStringItem(index, 3, ', '.join(curNode.tags))
            self.itemDataMap[index] = (curNode.name, curNode.mode, curNode.category, ', '.join(curNode.tags))
            self.nodeListCtrl.SetItemData(index, index)
            index += 1


    def updateNodeInvenotryList(self, nodeTemplates):
        index = 0
        self.nodeListCtrl.DeleteAllItems()

        for curNode in nodeTemplates.values():
            self.nodeListCtrl.InsertStringItem(index, curNode.name)
            self.nodeListCtrl.SetStringItem(index, 1, curNode.mode)
            self.nodeListCtrl.SetStringItem(index, 2, curNode.category)
            self.nodeListCtrl.SetStringItem(index, 3, ', '.join(curNode.tags))
            self.itemDataMap[index] = (curNode.name, curNode.mode, curNode.category, ', '.join(curNode.tags))
            self.nodeListCtrl.SetItemData(index, index)
            index += 1

    def onCollectionNodeHelp(self, event):
        pass



class NodeListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

        cmData = (("help", parent.onCollectionNodeHelp),)

        # create the context menu.
        self.contextMenu = psyContextMenu(cmData)

        self.Bind(wx.EVT_CONTEXT_MENU, self.onShowContextMenu)

    def onShowContextMenu(self, event):
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(self.contextMenu, pos)

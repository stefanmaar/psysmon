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

import copy
import logging

import wx
import wx.lib.mixins.listctrl as listmix
from wx.lib.stattext import GenStaticText as StaticText

import psysmon
from psysmon.artwork.icons import iconsBlack16 as icons
from psysmon.core.plugins import OptionPlugin
import psysmon.gui.context_menu as psy_cm


class ProcessingStack(OptionPlugin):
    '''

    '''
    nodeClass = 'common'

    def __init__(self, with_run_button = True):
        ''' The constructor

        '''
        OptionPlugin.__init__(self,
                              name = 'processing stack',
                              category = 'processing',
                              tags = ['process', 'data'])

        # Create the logging logger instance.
        #loggerName = __name__ + "." + self.__class__.__name__
        #self.logger = logging.getLogger(loggerName)
        self.logger = psysmon.get_logger(self)

        self.icons['active'] = icons.layers_1_icon_16

        self.with_run_button = with_run_button

        # Set the shortcut string.
        self.accelerator_string = 'CTRL+P'


    def buildFoldPanel(self, parent):
        foldPanel = wx.Panel(parent = parent, id = wx.ID_ANY)

        self.processingStack = self.parent.processing_stack

        # Layout using sizers.
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer = wx.BoxSizer(wx.VERTICAL)

        # Create the buttons to control the stack.
        addButton = wx.Button(foldPanel, wx.ID_ANY, "add")
        removeButton = wx.Button(foldPanel, wx.ID_ANY, "remove")
        upButton = wx.Button(foldPanel, wx.ID_ANY, "up")
        downButton = wx.Button(foldPanel, wx.ID_ANY, "down")

        # Fill the button sizer.
        buttonSizer.Add(addButton, 0, wx.ALL)
        buttonSizer.Add(removeButton, 0, wx.ALL)
        buttonSizer.Add(upButton, 0, wx.ALL)
        buttonSizer.Add(downButton, 0, wx.ALL)

        if self.with_run_button is True:
            runButton = wx.Button(foldPanel, wx.ID_ANY, "run")
            buttonSizer.Add(runButton, 0, wx.ALL)

        # Fill the nodes list with the nodes in the processing stack.
        nodeNames = [x.name for x in self.processingStack.nodes]
        isActive = [m for m, x in enumerate(self.processingStack) if x.isEnabled() == True]

        self.nodeListBox = wx.CheckListBox(parent = foldPanel,
                                           id = wx.ID_ANY,
                                           choices = nodeNames,
                                           size = (100, -1))
        self.nodeListBox.SetCheckedItems(isActive)

        # By default select the first processing node.
        self.nodeListBox.SetSelection(0)
        self.nodeOptions = self.processingStack[0].getEditPanel(foldPanel)

        # Add the elements to the main sizer.
        topSizer.Add(self.nodeListBox, 1, wx.EXPAND | wx.RIGHT, 5)
        topSizer.Add(buttonSizer, 0, wx.ALIGN_TOP)

        mainSizer.Add(topSizer, 0, wx.EXPAND | wx.ALL, 1)
        mainSizer.Add(self.nodeOptions, 1, wx.EXPAND | wx.TOP | wx.BOTTOM, 1)

        # Bind the events.
        foldPanel.Bind(wx.EVT_BUTTON, self.onAdd, addButton)
        foldPanel.Bind(wx.EVT_BUTTON, self.onRemove, removeButton)
        foldPanel.Bind(wx.EVT_BUTTON, self.onUp, upButton)
        foldPanel.Bind(wx.EVT_BUTTON, self.onDown, downButton)
        foldPanel.Bind(wx.EVT_LISTBOX, self.onNodeSelected, self.nodeListBox)
        foldPanel.Bind(wx.EVT_CHECKLISTBOX,
                       self.onBoxChecked,
                       self.nodeListBox)
        if self.with_run_button is True:
            foldPanel.Bind(wx.EVT_BUTTON, self.onRun, runButton)

        foldPanel.SetSizer(mainSizer)

        self.foldPanel = foldPanel

        return foldPanel


    def updateNodeList(self):
        self.nodeListBox.Clear()
        self.processingStack.nodes = [x for x in self.processingStack.nodes if x is not None]
        nodeNames = [x.name for x in self.processingStack.nodes]
        isActive = [m for m, x in enumerate(self.processingStack) if x.isEnabled() == True]
        self.nodeListBox.AppendItems(nodeNames)
        self.nodeListBox.SetCheckedItems(isActive)



    def onRun(self, event):
        ''' Re-run the processing stack.
        '''
        self.parent.update_display()


    def onAdd(self, event):
        ''' Add a processing node to the stack.

        Open a dialog field to select from the available processing nodes.
        '''
        dlg = PStackAddNodeDialog(parent = self.foldPanel,
                                  availableNodes = self.parent.processingNodes)
        val = dlg.ShowModal()

        if val == wx.ID_OK:
            node2Add = dlg.getSelection()
            if node2Add is not None:
                self.processingStack.addNode(node2Add,
                                             self.nodeListBox.GetSelection() + 1)
                self.updateNodeList()

        dlg.Destroy()


    def onRemove(self, event):
        ''' Remove the selected node from the stack.
        '''
        sel = self.nodeListBox.GetSelection()
        if sel == wx.NOT_FOUND or sel < 0 or sel >= len(self.processingStack.nodes):
            return

        self.processingStack.popNode(sel)
        self.updateNodeList()

        sizer = self.foldPanel.GetSizer()
        sizer.Detach(self.nodeOptions)
        self.nodeOptions.Destroy()

        if len(self.processingStack.nodes) > 0:
            new_sel = min(sel, len(self.processingStack.nodes) - 1)
            self.nodeListBox.SetSelection(new_sel)
            self.nodeOptions = self.processingStack[new_sel].getEditPanel(self.foldPanel)
        else:
            self.nodeOptions = wx.Panel(self.foldPanel)

        sizer.Add(self.nodeOptions, 1,
                  flag = wx.EXPAND | wx.TOP | wx.BOTTOM,
                  border=1)
        sizer.Layout()


    def onUp(self, event):
        ''' Move the selected node up in the stack.
        '''
        sel = self.nodeListBox.GetSelection()
        if sel == wx.NOT_FOUND or sel <= 0 or sel >= len(self.processingStack.nodes):
            return

        self.processingStack.nodes[sel - 1], self.processingStack.nodes[sel] = (
            self.processingStack.nodes[sel],
            self.processingStack.nodes[sel - 1]
        )
        self.updateNodeList()
        self.nodeListBox.SetSelection(sel - 1)


    def onDown(self, event):
        ''' Move the selected node down in the stack.
        '''
        sel = self.nodeListBox.GetSelection()
        if sel == wx.NOT_FOUND or sel < 0 or sel >= len(self.processingStack.nodes) - 1:
            return

        self.processingStack.nodes[sel + 1], self.processingStack.nodes[sel] = (
            self.processingStack.nodes[sel],
            self.processingStack.nodes[sel + 1]
        )
        self.updateNodeList()
        self.nodeListBox.SetSelection(sel + 1)


    def onNodeSelected(self, event):
        index = event.GetSelection()
        #selectedNode = event.GetString()
        sizer = self.foldPanel.GetSizer()
        sizer.Detach(self.nodeOptions)
        self.nodeOptions.Destroy()
        self.nodeOptions = self.processingStack[index].getEditPanel(self.foldPanel)
        sizer.Add(self.nodeOptions, 1,
                  flag = wx.EXPAND | wx.TOP | wx.BOTTOM,
                  border=1)
        sizer.Layout() 



    def onBoxChecked(self, event):
        index = event.GetSelection()
        label = self.nodeListBox.GetString(index)
        self.logger.debug('Checked item %d, label %s.', index, label)

        self.processingStack[index].toggleEnabled()


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

        self.sizer.Add(self.labelElement, pos = (0, 0),
                       flag = wx.EXPAND | wx.ALL,
                       border = 0)

        self.controlElement = PStackEditPanel(parent = self,
                                              size = (-1, 570))
        self.controlElement.SetMinSize((450, 560))
        self.SetMinSize((450, 580))

        self.sizer.Add(self.controlElement, pos = (1, 0),
                       flag = wx.EXPAND | wx.ALL,
                       border = 0)
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(1)

        self.SetSizer(self.sizer)


    def __del__(self):
        if hasattr(self, 'pref_item') and self.pref_item and hasattr(self.pref_item, 'gui_element'):
            if self in self.pref_item.gui_element:
                self.pref_item.remove_gui_element(self)

    def GetValue(self):
        ''' Return the selected nodes from the control panel.
        '''
        if self.controlElement is not None:
            return self.controlElement.GetValue()
        return self.pref_item.value

    def SetValue(self, value):
        ''' Set the processing stack nodes on the field and control element.
        '''
        self.pref_item.value = value
        if self.controlElement is not None:
            self.controlElement.SetValue(value)

    def setPrefValue(self):
        ''' Synchronize the preference item with the control element value.
        '''
        if self.controlElement is not None:
            self.pref_item.value = self.controlElement.GetValue()

    def setControlElementValue(self):
        ''' Synchronize the control element with the preference item value.
        '''
        if self.controlElement is not None:
            self.controlElement.SetValue(self.pref_item.value)

    def call_hook(self, hook_name):
        ''' Trigger registered hooks on the preference item.
        '''
        if hasattr(self, 'pref_item') and self.pref_item and hasattr(self.pref_item, 'hooks'):
            if hook_name in iter(self.pref_item.hooks.keys()):
                self.pref_item.hooks[hook_name]()


class PStackEditPanel(wx.Panel):
    '''
    '''
    def __init__(self, parent, size, id = wx.ID_ANY):
        wx.Panel.__init__(self, parent = parent, id = id, size = size)

        # Layout using sizers.
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer = wx.BoxSizer(wx.VERTICAL)

        # Create the buttons to control the stack.
        addButton = wx.Button(self, wx.ID_ANY, "add")
        removeButton = wx.Button(self, wx.ID_ANY, "remove")
        upButton = wx.Button(self, wx.ID_ANY, "up")
        downButton = wx.Button(self, wx.ID_ANY, "down")

        # Fill the button sizer.
        buttonSizer.Add(addButton, 0, wx.ALL)
        buttonSizer.Add(removeButton, 0, wx.ALL)
        buttonSizer.Add(upButton, 0, wx.ALL)
        buttonSizer.Add(downButton, 0, wx.ALL)

        # Fill the nodes list with the nodes in the processing stack.
        parent_pref = getattr(self.GetParent(), 'pref_item', None)
        if parent_pref is not None and parent_pref.value is not None:
            self.selected_nodes = [x for x in parent_pref.value if x is not None]
        else:
            self.selected_nodes = []
        self.sync_pref_item()

        node_names = [x.name for x in self.selected_nodes]
        is_active = [m for m, x in enumerate(self.selected_nodes) if x.isEnabled() == True]

        self.nodeListBox = wx.CheckListBox(parent = self,
                                           id = wx.ID_ANY,
                                           choices = node_names,
                                           size = (100, -1),
                                           style = wx.LB_NEEDED_SB | wx.LB_HSCROLL)
        self.nodeListBox.SetMinSize((-1, 145))
        self.nodeListBox.SetMaxSize((-1, 150))
        self.nodeListBox.SetCheckedItems(is_active)

        # By default select the first processing node if available.
        if len(self.selected_nodes) > 0:
            self.nodeListBox.SetSelection(0)
            self.nodeOptions = self.selected_nodes[0].getEditPanel(self)
        else:
            self.nodeOptions = wx.Panel(self)

        topSizer.Add(self.nodeListBox, 1, wx.EXPAND | wx.RIGHT, 5)
        topSizer.Add(buttonSizer, 0, wx.ALIGN_TOP)

        mainSizer.Add(topSizer, 0, wx.EXPAND | wx.ALL, 1)
        mainSizer.Add(self.nodeOptions, 1, wx.EXPAND | wx.TOP | wx.BOTTOM, 1)

        self.SetSizer(mainSizer)

        # Bind the events.
        self.Bind(wx.EVT_BUTTON, self.on_add_button_clicked, addButton)
        self.Bind(wx.EVT_BUTTON, self.on_remove_button_clicked, removeButton)
        self.Bind(wx.EVT_BUTTON, self.on_up_button_clicked, upButton)
        self.Bind(wx.EVT_BUTTON, self.on_down_button_clicked, downButton)
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
            if node2Add is None:
                dlg.Destroy()
                return
            cur_sel = self.nodeListBox.GetSelection()
            position = cur_sel + 1 if cur_sel != wx.NOT_FOUND else len(self.selected_nodes)
            node = copy.deepcopy(node2Add)
            if position == -1 or position >= len(self.selected_nodes):
                self.selected_nodes.append(node)
                new_sel = len(self.selected_nodes) - 1
            else:
                self.selected_nodes.insert(position, node)
                new_sel = position
            self.update_node_list()
            self.nodeListBox.SetSelection(new_sel)

            sizer = self.GetSizer()
            sizer.Detach(self.nodeOptions)
            self.nodeOptions.Destroy()
            self.nodeOptions = self.selected_nodes[new_sel].getEditPanel(self)
            sizer.Add(self.nodeOptions, 1, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)
            sizer.Layout()

        dlg.Destroy()


    def on_remove_button_clicked(self, event):
        ''' Remove the selected processing node from the stack.
        '''
        sel = self.nodeListBox.GetSelection()
        if sel == wx.NOT_FOUND or sel < 0 or sel >= len(self.selected_nodes):
            return

        del self.selected_nodes[sel]
        self.update_node_list()

        sizer = self.GetSizer()
        sizer.Detach(self.nodeOptions)
        self.nodeOptions.Destroy()

        if len(self.selected_nodes) > 0:
            new_sel = min(sel, len(self.selected_nodes) - 1)
            self.nodeListBox.SetSelection(new_sel)
            self.nodeOptions = self.selected_nodes[new_sel].getEditPanel(self)
        else:
            self.nodeOptions = wx.Panel(self)

        sizer.Add(self.nodeOptions, 1, flag=wx.EXPAND | wx.TOP | wx.BOTTOM, border=1)
        sizer.Layout()


    def on_up_button_clicked(self, event):
        ''' Move the selected processing node up in the stack.
        '''
        sel = self.nodeListBox.GetSelection()
        if sel == wx.NOT_FOUND or sel <= 0 or sel >= len(self.selected_nodes):
            return

        self.selected_nodes[sel - 1], self.selected_nodes[sel] = (
            self.selected_nodes[sel],
            self.selected_nodes[sel - 1]
        )
        self.update_node_list()
        self.nodeListBox.SetSelection(sel - 1)


    def on_down_button_clicked(self, event):
        ''' Move the selected processing node down in the stack.
        '''
        sel = self.nodeListBox.GetSelection()
        if sel == wx.NOT_FOUND or sel < 0 or sel >= len(self.selected_nodes) - 1:
            return

        self.selected_nodes[sel + 1], self.selected_nodes[sel] = (
            self.selected_nodes[sel],
            self.selected_nodes[sel + 1]
        )
        self.update_node_list()
        self.nodeListBox.SetSelection(sel + 1)


    def on_node_selected(self, event):
        index = event.GetSelection()
        sizer = self.GetSizer()
        sizer.Detach(self.nodeOptions)
        self.nodeOptions.Destroy()
        self.nodeOptions = self.selected_nodes[index].getEditPanel(self)
        sizer.Add(self.nodeOptions, 1, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)
        sizer.Layout()


    def update_node_list(self):
        self.nodeListBox.Clear()
        self.selected_nodes = [x for x in self.selected_nodes if x is not None]
        node_names = [x.name for x in self.selected_nodes]
        is_active = [m for m,x in enumerate(self.selected_nodes) if x.isEnabled() == True]
        self.nodeListBox.AppendItems(node_names)
        self.nodeListBox.SetCheckedItems(is_active)
        self.sync_pref_item()


    def on_node_checked(self, event):
        index = event.GetSelection()
        self.selected_nodes[index].toggleEnabled()
        self.sync_pref_item()


    def sync_pref_item(self):
        ''' Synchronize the edited stack nodes back to the parent preference item.
        '''
        parent = self.GetParent()
        if hasattr(parent, 'pref_item') and parent.pref_item is not None:
            parent.pref_item.value = self.selected_nodes
            if hasattr(parent, 'call_hook'):
                parent.call_hook('on_value_change')


    def GetValue(self):
        ''' Return the currently selected processing nodes.
        '''
        return self.selected_nodes


    def SetValue(self, value):
        ''' Set the processing nodes and update display.
        '''
        if value is None:
            self.selected_nodes = []
        else:
            self.selected_nodes = [x for x in value if x is not None]
        self.update_node_list()


class PStackAddNodeDialog(wx.Dialog):
    ''' Dialog to add a processing node to the stack.

    '''
    def __init__(self, parent=None, availableNodes = None, size = (880, 520)):
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

        self.SetSizer(sizer)
        self.SetMinSize((860, 480))
        self.SetSize(size)
        self.Layout()


    def getSelection(self):
        if self.nodeInventoryPanel.selectedNode is not None:
            return self.nodeInventoryPanel.selectedNode

        sel = self.nodeInventoryPanel.nodeListCtrl.GetFirstSelected()
        if sel != -1 and self.nodeInventoryPanel.availableNodes:
            name = self.nodeInventoryPanel.nodeListCtrl.GetItemText(sel)
            for node in self.nodeInventoryPanel.availableNodes:
                if node.name == name:
                    return node
            if sel < len(self.nodeInventoryPanel.availableNodes):
                return self.nodeInventoryPanel.availableNodes[sel]
        return None 




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
        self.nodeListCtrl.SetMinSize((840, 360))

        columns = [
            ('name', 190),
            ('mode', 95),
            ('category', 160),
            ('tags', 380)
        ]

        for colNum, (name, width) in enumerate(columns):
            self.nodeListCtrl.InsertColumn(colNum, name, width=width)

        self.fillNodeList(self.availableNodes)

        sizer.Add(self.nodeListCtrl, pos=(1, 0), flag=wx.EXPAND|wx.ALL, border=0)

        sizer.AddGrowableCol(0)
        sizer.AddGrowableRow(1)

        self.SetSizer(sizer)

        # Bind the select item event to track the selected processing
        # node.
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onNodeItemSelected, self.nodeListCtrl)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onNodeItemActivated, self.nodeListCtrl)



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


    def onNodeItemActivated(self, evt):
        self.onNodeItemSelected(evt)
        parent = self.GetParent()
        while parent and not isinstance(parent, wx.Dialog):
            parent = parent.GetParent()
        if parent:
            parent.EndModal(wx.ID_OK)


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

        if nodeTemplates:
            for curNode in nodeTemplates:
                self.nodeListCtrl.InsertItem(index, curNode.name)
                self.nodeListCtrl.SetItem(index, 1, curNode.mode)
                self.nodeListCtrl.SetItem(index, 2, curNode.category)
                self.nodeListCtrl.SetItem(index, 3, ', '.join(curNode.tags))
                self.itemDataMap[index] = (curNode.name, curNode.mode, curNode.category, ', '.join(curNode.tags))
                self.nodeListCtrl.SetItemData(index, index)
                index += 1

        if self.nodeListCtrl.GetItemCount() > 0:
            self.nodeListCtrl.Select(0)
            self.nodeListCtrl.Focus(0)
            if isinstance(nodeTemplates, dict):
                self.selectedNode = list(nodeTemplates.values())[0]
            elif isinstance(nodeTemplates, (list, tuple)) and len(nodeTemplates) > 0:
                self.selectedNode = nodeTemplates[0]
        else:
            self.selectedNode = None


    def updateNodeInvenotryList(self, nodeTemplates):
        index = 0
        self.nodeListCtrl.DeleteAllItems()

        if nodeTemplates:
            nodes_iter = nodeTemplates.values() if isinstance(nodeTemplates, dict) else nodeTemplates
            for curNode in nodes_iter:
                self.nodeListCtrl.InsertItem(index, curNode.name)
                self.nodeListCtrl.SetItem(index, 1, curNode.mode)
                self.nodeListCtrl.SetItem(index, 2, curNode.category)
                self.nodeListCtrl.SetItem(index, 3, ', '.join(curNode.tags))
                self.itemDataMap[index] = (curNode.name, curNode.mode, curNode.category, ', '.join(curNode.tags))
                self.nodeListCtrl.SetItemData(index, index)
                index += 1

        if self.nodeListCtrl.GetItemCount() > 0:
            self.nodeListCtrl.Select(0)
            self.nodeListCtrl.Focus(0)
            if isinstance(nodeTemplates, dict) and len(nodeTemplates) > 0:
                self.selectedNode = list(nodeTemplates.values())[0]
            elif isinstance(nodeTemplates, (list, tuple)) and len(nodeTemplates) > 0:
                self.selectedNode = nodeTemplates[0]
        else:
            self.selectedNode = None

    def onCollectionNodeHelp(self, event):
        pass



class NodeListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

        cmData = (("help", parent.onCollectionNodeHelp),)

        # create the context menu.
        self.contextMenu = psy_cm.psyContextMenu(cmData)

        self.Bind(wx.EVT_CONTEXT_MENU, self.onShowContextMenu)

    def onShowContextMenu(self, event):
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(self.contextMenu, pos)


# Register PStackEditField into bricks gui_elements
try:
    import psysmon.gui.bricks as psy_bricks
    psy_bricks.gui_elements['processing_stack'] = PStackEditField
except Exception:
    pass

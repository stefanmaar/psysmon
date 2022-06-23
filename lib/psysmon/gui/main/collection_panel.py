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
import wx.lib.mixins.listctrl as listmix

import psysmon
import psysmon.artwork.icons as psy_icon
import psysmon.core.error as psy_error
import psysmon.core.packageNodes as psy_pn
import psysmon.gui.context_menu as psy_cm




class CollectionPanel(wx.Panel):

    ## The constructor.
    #
    # @param self The object pointer.
    # @param parent The parent object holding the panel.
    def __init__(self, parent, psyBase, size):
        wx.Panel.__init__(self, parent=parent, size=size, id=wx.ID_ANY)

        # The logger.
        self.logger = psysmon.get_logger(self)

        self.psyBase = psyBase

        self.SetBackgroundColour((255, 255, 255))

        if False:
            self.collectionListCtrl = CollectionListCtrl(self, id=wx.ID_ANY,
                                     size=(200, -1),
                                     style=wx.LC_REPORT 
                                     | wx.BORDER_NONE
                                     | wx.LC_SORT_ASCENDING
                                     | wx.LC_SINGLE_SEL
                                     | wx.LC_NO_HEADER
                                     )
            self.collectionListCtrl.SetMinSize((200, -1))

            columns = {1: 'node'}

            for colNum, name in columns.items():
                self.collectionListCtrl.InsertColumn(colNum, name)

            sizer = wx.GridBagSizer(5, 5)
            sizer.Add(self.collectionListCtrl, pos=(0, 0), flag=wx.EXPAND|wx.ALL, border=0)
        else:
            self.collectionTreeCtrl = CollectionTreeCtrl(self, id = wx.ID_ANY,
                                                         pos = wx.DefaultPosition,
                                                         size = (200, -1),
                                                         style = wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT)
            sizer = wx.GridBagSizer(5, 5)
            sizer.Add(self.collectionTreeCtrl, pos=(0, 0), flag=wx.EXPAND|wx.ALL, border=0)

        self.executeButton = wx.Button(self, 10, "execute", (20, 20))
        sizer.Add(self.executeButton, pos=(1,0), flag=wx.EXPAND|wx.ALL, border=2)

        sizer.AddGrowableCol(0)
        sizer.AddGrowableRow(0)
        #sizer.AddGrowableCol(1)
        self.SetSizerAndFit(sizer)

        # create the context menu.
        cmData = (("load collection", self.onCollectionLoad),
                  ("new collection", self.onCollectionNew),
                  ("delete collection", self.onCollectionDelete))
        self.contextMenu = psy_cm.psyContextMenu(cmData)

        # Bind the events
        self.Bind(wx.EVT_BUTTON, self.onExecuteCollection)
        #self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onCollectionNodeItemSelected)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onCollectionNodeItemSelected)
        self.Bind(wx.EVT_CONTEXT_MENU, self.onShowContextMenu)

        self.selectedCollectionNodeIndex = -1
        self.selectedLooperChildNodeIndex = -1
        self.selectedNodeType = None




    def onShowContextMenu(self, event):
        self.PopupMenu(self.contextMenu)


    # Execute collection button callback.
    #
    # @param self The object pointer.
    # @param event The event object.  
    def onExecuteCollection(self, event): 
        self.psyBase.project.executeCollection()

    # Remove node context menu callback.
    #
    # @param self The object pointer.
    # @param event The event object. 
    def onRemoveNode(self, event):
        try:
            if self.selectedNodeType in ['node', 'looper']:
                self.logger.debug("Removing node at index %d.", self.selectedCollectionNodeIndex)
                self.psyBase.project.removeNodeFromCollection(self.selectedCollectionNodeIndex)
                self.selectedCollectionNodeIndex -= 1
                if self.selectedCollectionNodeIndex < 0 and len(self.psyBase.project.activeUser.activeCollection) > 0:
                    self.selectedCollectionNodeIndex = 0
                if self.selectedNodeType == 'looper':
                    self.selectedLooperChildNodeIndex = -1
            elif self.selectedNodeType == 'looper_child':
                selectedNode = self.Parent.psyBase.project.getNodeFromCollection(self.selectedCollectionNodeIndex)
                selectedNode.children.pop(self.selectedLooperChildNodeIndex)
                self.selectedLooperChildNodeIndex -= 1
                if self.selectedLooperChildNodeIndex < 0 and len(selectedNode.children) > 0:
                    self.selectedLooperChildNodeIndex = 0
            self.refreshCollection()
        except psy_error.PsysmonError as e:
            msg = "Cannot remove the collection node:\n %s" % e
            dlg = wx.MessageDialog(None, msg, 
                                   "pSysmon runtime error.",
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal() 


    ## Edit node context menu callback.
    #
    # @param self The object pointer.
    # @param event The event object. 
    def onEditNode(self, event):
        try:
            if self.selectedNodeType in ['node', 'looper']:
                selectedNode = self.Parent.psyBase.project.getNodeFromCollection(self.selectedCollectionNodeIndex)
            elif self.selectedNodeType == 'looper_child':
                selectedLooper = self.Parent.psyBase.project.getNodeFromCollection(self.selectedCollectionNodeIndex)
                selectedNode = selectedLooper.children[self.selectedLooperChildNodeIndex]

            if(selectedNode.mode == 'standalone'):
                self.logger.debug("in standalone")
                selectedNode.execute()
            else:
                selectedNode.edit()
        except psy_error.PsysmonError as e:
            msg = "Cannot edit the node:\n %s" % e
            dlg = wx.MessageDialog(None, msg, 
                                   "pSysmon runtime error.",
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal() 

    def onMoveUp(self, event):
        ''' Move a node up in the collection.
        '''
        collection = self.psyBase.project.getActiveCollection()

        if self.selectedNodeType in ['node', 'looper']:
            # Move the node in the collection.
            selected_node = self.Parent.psyBase.project.getNodeFromCollection(self.selectedCollectionNodeIndex)
            collection.moveNodeUp(selected_node)
        elif self.selectedNodeType == 'looper_child':
            # Move the node in the looper.
            selected_looper = self.Parent.psyBase.project.getNodeFromCollection(self.selectedCollectionNodeIndex)
            selected_node = selected_looper.children[self.selectedLooperChildNodeIndex]
            selected_looper.move_node_up(selected_node)
        self.refreshCollection()

    def onMoveDown(self, event):
        ''' Move a node up in the collection.
        '''
        collection = self.psyBase.project.getActiveCollection()
        if self.selectedNodeType in ['node', 'looper']:
            # Move the node in the collection.
            selected_node = self.Parent.psyBase.project.getNodeFromCollection(self.selectedCollectionNodeIndex)
            collection.moveNodeDown(selected_node)
        elif self.selectedNodeType == 'looper_child':
            # Move the node in the looper.
            selected_looper = self.Parent.psyBase.project.getNodeFromCollection(self.selectedCollectionNodeIndex)
            selected_node = selected_looper.children[self.selectedLooperChildNodeIndex]
            selected_looper.move_node_down(selected_node)
        self.refreshCollection()


    def onToggleNodeEnable(self, event):
        if self.selectedNodeType in ['node', 'looper']:
            selectedNode = self.Parent.psyBase.project.getNodeFromCollection(self.selectedCollectionNodeIndex)
        elif self.selectedNodeType == 'looper_child':
            selectedLooper = self.Parent.psyBase.project.getNodeFromCollection(self.selectedCollectionNodeIndex)
            selectedNode = selectedLooper.children[self.selectedLooperChildNodeIndex]

        if selectedNode.mode != 'standalone':
            selectedNode.enabled = not selectedNode.enabled
            if selectedNode.enabled:
                self.collectionTreeCtrl.SetItemTextColour(self.collectionTreeCtrl.GetSelection(), wx.BLACK)
            else:
                self.collectionTreeCtrl.SetItemTextColour(self.collectionTreeCtrl.GetSelection(), wx.TheColourDatabase.Find('GREY70'))

    ## Select node item callback.
    #
    # This method responds to events raised by selecting a collection node in 
    # the collectionPanel.collectionListCtrl.
    #
    # @param self The object pointer.
    # @param event The event object.    
    def onCollectionNodeItemSelected(self, evt):
        if not evt.GetItem():
            return
        item_data = self.collectionTreeCtrl.GetItemPyData(evt.GetItem())
        node_type = item_data['node_type']
        node_pos = item_data['node_pos']
        self.logger.debug("Selected node %s at position %d in collection.", node_type, node_pos)
        self.selectedNodeType = node_type
        self.selectedCollectionNodeIndex = node_pos
        if node_type == 'looper_child':
            self.selectedLooperChildNodeIndex = item_data['child_pos']
        else:
            self.selectedLooperChildNodeIndex = -1


    # Load a collection context menu callback.
    #
    # @param self The object pointer.
    # @param event The event object. 
    def onCollectionLoad(self, event):
        collections = self.psyBase.project.getCollection()
        choices = [x.name for x in collections.values()]
        dlg = wx.SingleChoiceDialog(None, "Select a collection",
                                    "Load collection",
                                    choices)
        if dlg.ShowModal() == wx.ID_OK:
            self.psyBase.project.setActiveCollection(dlg.GetStringSelection())
            self.refreshCollection()
        dlg.Destroy()


    # Add new collection context menu callback.
    #
    # @param self The object pointer.
    # @param event The event object. 
    def onCollectionNew(self, event):
        colName = wx.GetTextFromUser('collection name', caption='New collection',
                                     default_value="", parent=None)

        if not colName:
            return
        else:
            self.psyBase.project.addCollection(colName)
            self.refreshCollection()


    # Delete a collection context menu callback.
    #
    # @param self The object pointer.
    # @param event The event object.
    def onCollectionDelete(self, event):
        self.logger.warning("Deleting a collection is not yet implemented.")
        # TODO: Implement the removal of a collection. Take care of the saved
        # collection file. Think about removing the currently active collection
        # or showing a dialog from which to select the collection to delete.

    def refreshCollection(self):
        '''
        Refresh the collection nodes displayed in the collection listbox.

        :param self: The object pointer.
        :type self: :class:`~psysmon.core.gui.CollectionPanel`
        '''
        if not self.psyBase.project:
            self.collectionTreeCtrl.DeleteChildren(self.collectionTreeCtrl.root)
            return

        activeCollection = self.psyBase.project.getActiveCollection()
        if activeCollection is not None:
            auiPane = self.GetParent().mgr.GetPane('collection')
            auiPane.Caption(activeCollection.name)
            self.GetParent().mgr.Update()

            self.collectionTreeCtrl.DeleteChildren(self.collectionTreeCtrl.root)
            for k, curNode in enumerate(activeCollection.nodes):
                if isinstance(curNode, psy_pn.LooperCollectionNode):
                    node_string = curNode.name + ' (looper)'
                    looper_node_item = self.collectionTreeCtrl.AppendItem(self.collectionTreeCtrl.root, node_string)
                    item_data = {'node_pos': k,
                                 'node_type': 'looper'}
                    self.collectionTreeCtrl.SetItemPyData(looper_node_item, item_data)
                    self.collectionTreeCtrl.SetItemImage(looper_node_item, self.collectionTreeCtrl.icons['looper_node'], wx.TreeItemIcon_Normal)
                    if k == self.selectedCollectionNodeIndex:
                        self.collectionTreeCtrl.SelectItem(looper_node_item)
                    if not curNode.enabled:
                        self.collectionTreeCtrl.SetItemTextColour(looper_node_item, wx.TheColourDatabase.Find('GREY70'))

                    for child_pos, cur_child in enumerate(curNode.children):
                        node_string = cur_child.name + '(child)'
                        node_item = self.collectionTreeCtrl.AppendItem(looper_node_item, node_string)
                        item_data = {'node_pos': k,
                                     'child_pos': child_pos,
                                     'node_type': 'looper_child'}
                        self.collectionTreeCtrl.SetItemPyData(node_item, item_data)
                        self.collectionTreeCtrl.SetItemImage(node_item, self.collectionTreeCtrl.icons['looper_node_child'], wx.TreeItemIcon_Normal)
                        if not curNode.enabled:
                            self.collectionTreeCtrl.SetItemTextColour(node_item, wx.TheColourDatabase.Find('GREY70'))
                else:
                    node_string = curNode.name
                    node_item = self.collectionTreeCtrl.AppendItem(self.collectionTreeCtrl.root, node_string)
                    item_data = {'node_pos': k,
                                 'node_type': 'node'}
                    self.collectionTreeCtrl.SetItemPyData(node_item, item_data)
                    self.collectionTreeCtrl.SetItemImage(node_item, self.collectionTreeCtrl.icons['node'], wx.TreeItemIcon_Normal)
                    if k == self.selectedCollectionNodeIndex:
                        self.collectionTreeCtrl.SelectItem(node_item)
                    if not curNode.enabled:
                        self.collectionTreeCtrl.SetItemTextColour(node_item, wx.TheColourDatabase.Find('GREY70'))

        self.collectionTreeCtrl.ExpandAll()


class CollectionListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

        # create the context menu.
        cmData = (("edit node", parent.onEditNode),
                  ("disable node", parent.onDisableNode),
                  ("enable node", parent.onEnableNode),
                  ("remove node", parent.onRemoveNode),
                  ("separator", None),
                  ("load collection", parent.onCollectionLoad),
                  ("new collection", parent.onCollectionNew),
                  ("delete collection", parent.onCollectionDelete))
        self.contextMenu = psy_cm.psyContextMenu(cmData)

        self.Bind(wx.EVT_CONTEXT_MENU, self.onShowContextMenu)


    def onShowContextMenu(self, event):
        try:
            selectedNode = self.Parent.Parent.psyBase.project.getNodeFromCollection(self.Parent.selectedCollectionNodeIndex)
            if(selectedNode.mode == 'standalone'):
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), True)
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), True)
            elif(selectedNode.mode == 'uneditable'):
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), False)
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), True)
            else:
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), True)
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), True)
        except Exception:
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), False)
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), False)

        self.PopupMenu(self.contextMenu)
        

class CollectionTreeCtrl(wx.TreeCtrl):
    def __init__(self, parent, id, pos, size, style):
        wx.TreeCtrl.__init__(self, parent, id, pos, size, style)

        il = wx.ImageList(16, 16)
        self.icons = {}
        self.icons['node'] = il.Add(psy_icon.iconsBlack16.arrow_r_icon_16.GetBitmap())
        self.icons['looper_node'] = il.Add(psy_icon.iconsBlack16.playback_reload_icon_16.GetBitmap())
        self.icons['looper_node_child'] = il.Add(psy_icon.iconsBlack16.arrow_l_icon_16.GetBitmap())

        self.AssignImageList(il)

        self.root = self.AddRoot("collection")

        self.SetMinSize(size)

        # create the context menu.
        cmData = (("edit node", parent.onEditNode),
                  ("enable node", parent.onToggleNodeEnable),
                  ("remove node", parent.onRemoveNode),
                  ("separator", None),
                  ("move up", parent.onMoveUp),
                  ("move down", parent.onMoveDown),
                  ("separator", None),
                  ("load collection", parent.onCollectionLoad),
                  ("new collection", parent.onCollectionNew),
                  ("delete collection", parent.onCollectionDelete))
        self.contextMenu = psy_cm.psyContextMenu(cmData)
        # Disable the delete collection menu item. It's not yet implemented.
        self.contextMenu.Enable(self.contextMenu.FindItemByPosition(6).GetId(), False)

        self.Bind(wx.EVT_CONTEXT_MENU, self.onShowContextMenu)
        self.Bind(wx.EVT_RIGHT_DOWN, self.onShowContextMenu)


    def onShowContextMenu(self, event):
        try:
            # Enable all node relevant context menu items.
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), True)
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), True)
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(2).GetId(), True)

            if self.Parent.selectedNodeType in ['node', 'looper']:
                selectedNode = self.GrandParent.psyBase.project.getNodeFromCollection(self.Parent.selectedCollectionNodeIndex)
            elif self.Parent.selectedNodeType == 'looper_child':
                selectedLooper = self.GrandParent.psyBase.project.getNodeFromCollection(self.Parent.selectedCollectionNodeIndex)
                selectedNode = selectedLooper.children[self.Parent.selectedLooperChildNodeIndex]
            else:
                selectedNode = None

            if selectedNode:
                if(selectedNode.mode == 'execute only'):
                    self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), False)
                else:
                    self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), True)

                if selectedNode.enabled:
                    self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(1).GetId(), 'disable node')
                    self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), True)
                else:
                    self.contextMenu.SetLabel(self.contextMenu.FindItemByPosition(1).GetId(), 'enable node')
                    self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), True)
            else:
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), False)
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), False)
                self.contextMenu.Enable(self.contextMenu.FindItemByPosition(2).GetId(), False)

        except Exception:
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(0).GetId(), False)
            self.contextMenu.Enable(self.contextMenu.FindItemByPosition(1).GetId(), False)
            self.logger.exception("Problems setting the context menu labels.")
        finally:
            self.PopupMenu(self.contextMenu)

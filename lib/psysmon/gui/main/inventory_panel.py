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
import webbrowser

import wx
import wx.lib.mixins.listctrl as listmix

import psysmon
import psysmon.core.error as psy_error
import psysmon.core.packageNodes as psy_pn
import psysmon.gui.context_menu as psy_cm




class CollectionNodeInventoryPanel(wx.Panel, listmix.ColumnSorterMixin):
    def __init__(self, parent, psyBase):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.itemDataMap = {}

        self.il = wx.ImageList(16, 16)
        self.sm_up = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_OTHER, (16,16)))
        self.sm_dn = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_OTHER, (16,16)))

        self.psyBase = psyBase
        self.collectionPanel = parent.collectionPanel

        self.SetBackgroundColour((255, 255, 255))

        sizer = wx.GridBagSizer(5, 5)

        self.searchButton = wx.SearchCtrl(self, size=(200,30), style=wx.TE_PROCESS_ENTER)
        self.searchButton.SetMinSize((-1, 30))
        #self.searchButton.SetDescriptiveText('Search collection nodes')
        self.searchButton.ShowCancelButton(True)
        self.Bind(wx.EVT_TEXT, self.onDoSearch, self.searchButton)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.onDoSearch, self.searchButton)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.onCancelSearch, self.searchButton)
        self.Bind(wx.EVT_TEXT_ENTER, self.onDoSearch, self.searchButton)
        sizer.Add(self.searchButton, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=2)

        self.nodeListCtrl = NodeListCtrl(self, id=wx.ID_ANY,
                                 size = (400, -1),
                                 style=wx.LC_REPORT 
                                 | wx.BORDER_NONE
                                 | wx.LC_SINGLE_SEL
                                 | wx.LC_SORT_ASCENDING
                                 )
        self.nodeListCtrl.SetMinSize((400, 100))

        self.nodeListCtrl.SetImageList(self.il, wx.IMAGE_LIST_SMALL)


        columns = {1: 'name', 2: 'mode', 3: 'category', 4: 'tags'}

        for colNum, name in columns.items():
            self.nodeListCtrl.InsertColumn(colNum, name)

        sizer.Add(self.nodeListCtrl, pos=(1, 0), flag=wx.EXPAND|wx.ALL, border=0)

        sizer.AddGrowableCol(0)
        #sizer.AddGrowableCol(1)
        sizer.AddGrowableRow(1)

        self.SetSizerAndFit(sizer)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onCollectionNodeItemSelected)



    ## Select node item callback.
    #
    # This method responds to events raised by selecting a collection node in 
    # the collectionNodeInventoryPanel.nodeListCtrl .
    #
    # @param self The object pointer.
    # @param event The event object.    
    def onCollectionNodeItemSelected(self, evt):
        item = evt.GetItem()
        self.logger.debug("Selected item: %s", item.GetText())
        self.selectedCollectionNodeTemplate = self.psyBase.packageMgr.getCollectionNodeTemplate(item.GetText())


    def onDoSearch(self, evt):
        foundNodes = self.psyBase.packageMgr.searchCollectionNodeTemplates(self.searchButton.GetValue())
        self.updateNodeInvenotryList(foundNodes)
        self.logger.debug('%s', foundNodes)

    def onCancelSearch(self, evt):
        self.initNodeInventoryList()
        self.searchButton.SetValue(self.searchButton.GetDescriptiveText())



    def onCollectionNodeAdd(self, event):
        msg =  "Adding node template to collection: " + self.selectedCollectionNodeTemplate.name
        #pub.sendMessage("log.general.status", msg = msg)
        self.logger.info(msg)

        if psy_pn.LooperCollectionChildNode in self.selectedCollectionNodeTemplate.__bases__:
            # Check if a collection exists.

            # Check if the selected node is a looper node.
            #selected_node = self.Parent.psyBase.project.getNodeFromCollection(self.collectionPanel.selectedCollectionNodeIndex)
            #if psysmon.core.packageNodes.LooperCollectionNode in selected_node:

            # Add the currend looper child node to the looper node.
            pos = self.collectionPanel.selectedCollectionNodeIndex
            child_pos = self.collectionPanel.selectedLooperChildNodeIndex
            self.psyBase.project.addNode2Looper(self.selectedCollectionNodeTemplate, pos,
                                                looper_pos = child_pos)
            self.collectionPanel.refreshCollection()
        else:
            try:
                pos = self.collectionPanel.selectedCollectionNodeIndex
                if pos != -1:
                    pos += 1    # Add after the selected node in the collection.
                self.psyBase.project.addNode2Collection(self.selectedCollectionNodeTemplate, pos)
                self.collectionPanel.refreshCollection()
            except psy_error.PsysmonError:
                msg = "No collection found. Create one first."
                dlg = wx.MessageDialog(None, msg, 
                                       "pSysmon runtime error.",
                                       wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()

    ## Show the node's online help file.
    # 
    # Each collection node should provide a html formatted help file. This 
    # file can be shown using the collection node inventory context menu.
    def onCollectionNodeHelp(self, event):
        doc_dir = psysmon.doc_entry_point

        package_name = self.selectedCollectionNodeTemplate.parentPackage.name
        node_name = self.selectedCollectionNodeTemplate.name.replace(' ', '_')

        filename = os.path.join(doc_dir, 'packages', package_name, node_name + '.html')

        if os.path.isfile(filename):
            webbrowser.open_new(filename)
        else:
            msg =  "Couldn't find the documentation file %s." % filename
            self.logger.warning(msg)



    def initNodeInventoryList(self):
        nodeTemplates = {}
        for curPkg in self.psyBase.packageMgr.packages.values():
            nodeTemplates.update(curPkg.collectionNodeTemplates)

        self.updateNodeInvenotryList(nodeTemplates)
        listmix.ColumnSorterMixin.__init__(self, 4)
        self.nodeListCtrl.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.nodeListCtrl.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.nodeListCtrl.SetColumnWidth(2, wx.LIST_AUTOSIZE)


    def updateNodeInvenotryList(self, nodeTemplates):
        index = 0
        self.nodeListCtrl.DeleteAllItems()

        for curNode in nodeTemplates.values():
            self.nodeListCtrl.InsertItem(index, curNode.name)
            self.nodeListCtrl.SetItem(index, 1, curNode.mode)
            self.nodeListCtrl.SetItem(index, 2, curNode.category)
            self.nodeListCtrl.SetItem(index, 3, ', '.join(curNode.tags))
            self.itemDataMap[index] = (curNode.name,
                                       curNode.mode,
                                       curNode.category,
                                       ', '.join(curNode.tags))
            self.nodeListCtrl.SetItemData(index, index)
            index += 1

    def GetListCtrl(self):
        return self.nodeListCtrl

    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)


class NodeListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

        cmData = (("add", parent.onCollectionNodeAdd),
                  ("help", parent.onCollectionNodeHelp))

        # create the context menu.
        self.contextMenu = psy_cm.psyContextMenu(cmData)

        self.Bind(wx.EVT_CONTEXT_MENU, self.onShowContextMenu)

    def onShowContextMenu(self, event):
        self.PopupMenu(self.contextMenu)

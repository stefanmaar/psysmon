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
# along with this program.  If not, see <http://www.gnu.org/licenses/>
'''
The editGeometry module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    http://www.gnu.org/licenses/gpl-3.0.html

This module contains the classes of the editGeometry dialog window.
'''

import logging
import psysmon.core.gui
import psysmon.core.packageNodes as psy_packageNodes
import psysmon.core.preferences_manager as psy_preferences_manager
import wx
import obspy.core.utcdatetime as udt

class DataInventoryStatistics(psy_packageNodes.CollectionNode):
    ''' Display statistics of the available data inventory.

    '''
    name = 'data inventory statistics'
    mode = 'execute only'
    category = 'Data inventory'
    tags = ['stable']

    def __init__(self, **args):
        psy_packageNodes.CollectionNode.__init__(self, **args)


    def edit(self):
        ''' The edit method.

        The DataInventoryStatistics node is a standalone node. Ignore the edit method.
        '''
        pass


    def execute(self, prevNodeOutput={}):
        ''' Execute the collection node.

        '''
        app = psysmon.core.gui.PSysmonApp()
        dlg = DataInventoryStatisticsDlg(self, self.project)
        dlg.Show()
        app.MainLoop()




class DataInventoryStatisticsDlg(wx.Frame):

    def __init__(self, collection_node, project, parent=None, id=wx.ID_ANY,
            title='data inventory statistics', size=(1000,600)):
        wx.Frame.__init__(self, parent=parent, id=id,
                           title=title,
                           pos=wx.DefaultPosition,
                           style=wx.DEFAULT_FRAME_STYLE)
        self.SetMinSize(size)

        # The collection node calling this dialog.
        self.collection_node = collection_node


        # The logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The current pSysmon project.
        self.project = project

        # The statistics of the data inventory.
        self.stats = {}
        self.stats['overview'] = {}
        self.stats['stations'] = {}

        # initialize the user interface
        self.initUI()

        self.load_data_inventory()
        self.inventory_view_notebook.overview_panel.textctrl.SetLabel(self.overview_text)


    @property
    def overview_text(self):
        text = ''
        text += 'First data in database: %s' % self.stats['overview']['first_data'] + '\n'
        text += 'Last data in database: %s' % self.stats['overview']['last_data'] + '\n'
        return text



    def initUI(self):
        ''' Build the graphical user interface (GUI).

        '''
        self.mgr = wx.aui.AuiManager(self)

        self.inventory_view_notebook = InventoryViewNotebook(self, wx.ID_ANY)

        self.mgr.AddPane(self.inventory_view_notebook,
                wx.aui.AuiPaneInfo().Name('view').CenterPane().
                BestSize(wx.Size(300,300)).MinSize(wx.Size(100, 20)))

        self.mgr.Update()


    def load_data_inventory(self):
        ''' Load inventory data.

        '''
        import sqlalchemy

        db_session = self.project.getDbSession()

        overview_stats = self.stats['overview']
        min_begin = db_session.query(sqlalchemy.func.min(self.project.dbTables['traceheader'].begin_time)).scalar()
        max_begin = db_session.query(sqlalchemy.func.max(self.project.dbTables['traceheader'].begin_time)).scalar()

        if min_begin is None or max_begin is None:
            overview_stats['first_data'] = None
            overview_stats['last_data'] = None
        else:
            overview_stats['first_data'] = udt.UTCDateTime(min_begin)
            last_begin_time = udt.UTCDateTime(max_begin)
            tmp = db_session.query(self.project.dbTables['traceheader']).filter_by(begin_time = last_begin_time.timestamp).all()
            end_time = [x.begin_time + (x.numsamp-1)/float(x.sps) for x in tmp]
            overview_stats['last_data'] = udt.UTCDateTime(max(end_time))

        db_session.close()






class InventoryViewNotebook(wx.Notebook):

    def __init__(self, parent, id):
        wx.Notebook.__init__(self, parent, id, size=(21,21), style=
                             wx.BK_DEFAULT)

        self.logger = self.GetParent().logger

        # The text view panel.
        self.overview_panel = TextViewPanel(self)
        self.AddPage(self.overview_panel, 'text view')

        self.graphic_view_panel = GraphicViewPanel(self)
        self.AddPage(self.graphic_view_panel, 'graphic view')



class TextViewPanel(wx.Panel):

    def __init__(self, parent, id=wx.ID_ANY):
        wx.Panel.__init__(self, parent, id)

        self.logger = self.GetParent().logger

        self.sizer = wx.GridBagSizer(5, 5)

        self.textctrl = wx.StaticText(self, wx.ID_ANY,
                            "This is an example of static text", (20, 10))

        self.sizer.Add(self.textctrl, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=20)
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(0)
        self.SetSizerAndFit(self.sizer)


class GraphicViewPanel(wx.Panel):

    def __init__(self, parent, id=wx.ID_ANY):
        wx.Panel.__init__(self, parent, id)

        self.logger = self.GetParent().logger

        self.sizer = wx.GridBagSizer(5, 5)

        self.textctrl = wx.StaticText(self, wx.ID_ANY,
                            "The graphical view is not yet implemented.", (20, 10))

        self.sizer.Add(self.textctrl, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=5)
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(0)
        self.SetSizerAndFit(self.sizer)

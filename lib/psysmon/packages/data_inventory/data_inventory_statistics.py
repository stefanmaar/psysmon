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

import pprint
import logging

import obspy.core.utcdatetime as udt
import psysmon.core.packageNodes as psy_packageNodes
import sqlalchemy as sqa
import wx

import psysmon
import psysmon.gui.main.app as psy_app


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
        app = psy_app.PsysmonApp()
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
        self.logger = psysmon.get_logger(self)

        # The current pSysmon project.
        self.project = project

        # The statistics of the data inventory.
        self.stats = {}

        # initialize the user interface
        self.initUI()

        self.load_data_inventory()
        self.inventory_view_notebook.overview_panel.textctrl.AppendText(self.overview_text)


    @property
    def overview_text(self):
        #text = ''
        #text += 'First data in database: %s' % self.stats['overview']['first_data'] + '\n'
        #text += 'Last data in database: %s' % self.stats['overview']['last_data'] + '\n'
        text = pprint.pformat(self.stats, indent = 4)
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
        db_session = self.project.getDbSession()

        try:
            # The the waveform directories.
            wf_dir_list = self.project.waveclient['db client'].waveformDirList

            # The database tables.
            t_datafile = self.project.dbTables['datafile']
            t_traceheader = self.project.dbTables['traceheader']

            for cur_wf_dir in wf_dir_list:
                # Compute the statistics for each waveform directory.
                cur_stats = {}
                # The number of data files.
                n_files = db_session.query(t_datafile).filter(t_datafile.wf_id == cur_wf_dir[0]).count()
                cur_stats['n_files'] = n_files

                # The total file size.
                tot_filesize = db_session.query(sqa.func.sum(t_datafile.filesize)).filter(t_datafile.wf_id == cur_wf_dir[0]).scalar()
                if tot_filesize:
                    cur_stats['tot_filesize'] = tot_filesize / 1024. / 1024.
                else:
                    cur_stats['tot_filesize'] = 0

                # The minimum and maximum time of the available data.
                min_begin = db_session.query(sqa.func.min(t_traceheader.begin_time)).\
                                             filter(t_datafile.wf_id == cur_wf_dir[0]).\
                                             filter(t_traceheader.datafile_id == t_datafile.id).scalar()
                max_begin = db_session.query(sqa.func.max(t_traceheader.begin_time)).\
                                             filter(t_datafile.wf_id == cur_wf_dir[0]).\
                                             filter(t_traceheader.datafile_id == t_datafile.id).scalar()
                if min_begin is None or max_begin is None:
                    cur_stats['first_data'] = None
                    cur_stats['last_data'] = None
                else:
                    cur_stats['first_data'] = udt.UTCDateTime(min_begin)
                    last_begin_time = udt.UTCDateTime(max_begin)
                    tmp = db_session.query(self.project.dbTables['traceheader']).filter_by(begin_time = last_begin_time.timestamp).all()
                    end_time = [x.begin_time + (x.numsamp-1)/float(x.sps) for x in tmp]
                    cur_stats['last_data'] = udt.UTCDateTime(max(end_time))

                # The unique serial numbers.
                unique_streams = db_session.query(t_traceheader.recorder_serial, t_traceheader.stream).\
                                                 filter(t_datafile.wf_id == cur_wf_dir[0]).\
                                                 filter(t_traceheader.datafile_id == t_datafile.id).\
                                                 distinct().all()
                cur_stats['unique_streams'] = [' '.join(x) for x in unique_streams]

                # The datafiles per recorder serial.
                files_per_recorder = db_session.query(t_traceheader.recorder_serial, sqa.func.count()).\
                                                      filter(t_datafile.wf_id == cur_wf_dir[0]).\
                                                      filter(t_traceheader.datafile_id == t_datafile.id).\
                                                      group_by(t_traceheader.recorder_serial).all()
                cur_stats['files_per_recorder'] = files_per_recorder

                self.stats[(cur_wf_dir[0], cur_wf_dir[2])] = cur_stats

            #overview_stats = self.stats['overview']

        finally:
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

        self.textctrl = wx.TextCtrl(self, wx.ID_ANY,
                            "", (20, 10),
                            style = wx.TE_MULTILINE | wx.TE_READONLY)

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

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
from psysmon.core.guiBricks import PrefEditPanel
from psysmon.artwork.icons import iconsBlack16 as icons
import psysmon.core.preferences_manager as psy_pm
from obspy.core.utcdatetime import UTCDateTime
import wx.lib.mixins.listctrl as listmix
from wx.lib.stattext import GenStaticText as StaticText


class SelectEvents(OptionPlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' Initialize the instance.

        '''
        OptionPlugin.__init__(self,
                              name = 'show events',
                              category = 'view',
                              tags = ['show', 'events']
                             )

        # Create the logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.pin_map_icon_16

        # Setup the pages of the preference manager.
        self.pref_manager.add_page('Select')
        self.pref_manager.add_page('Display')

        item = psy_pm.DateTimeEditPrefItem(name = 'start_time',
                                           label = 'start time',
                                           group = 'detection time span',
                                           value = UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The start time of the detection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).')
        self.pref_manager.add_item(pagename = 'Select',
                                   item = item)


        item = psy_pm.FloatSpinPrefItem(name = 'window_length',
                                        label = 'window length [s]',
                                        group = 'detection time span',
                                        value = 3600,
                                        limit = (0, 86400),
                                        digits = 1,
                                        tool_tip = 'The length of the time window for which events should be loaded.')
        self.pref_manager.add_item(pagename = 'Select',
                                   item = item)


        item = psy_pm.CustomPrefItem(name = 'events',
                                     label = 'events',
                                     group = 'AVAILABLE EVENTS',
                                     value = [],
                                     gui_class = EventListField,
                                     tool_tip = 'The start time of the detection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).')
        self.pref_manager.add_item(pagename = 'Select',
                                   item = item)

        item = psy_pm.ActionItem(name = 'load_events',
                                 label = 'load events',
                                 group = 'detection time span',
                                 mode = 'button',
                                 action = self.on_load_events)
        self.pref_manager.add_item(pagename = 'Select',
                                   item = item)


        item = psy_pm.FloatSpinPrefItem(name = 'pre_et',
                                        label = 'pre event time [s]',
                                        group = 'display range',
                                        value = 5,
                                        limit = (0, 86400),
                                        digits = 1,
                                        tool_tip = 'The length of the time window to show before the event start.')
        self.pref_manager.add_item(pagename = 'Display',
                                   item = item)

        item = psy_pm.FloatSpinPrefItem(name = 'post_et',
                                        label = 'post event time [s]',
                                        group = 'display range',
                                        value = 10,
                                        limit = (0, 86400),
                                        digits = 1,
                                        tool_tip = 'The length of the time window to show after the event end.')
        self.pref_manager.add_item(pagename = 'Display',
                                   item = item)



    def buildFoldPanel(self, panelBar):
        ''' Create the foldpanel GUI.
        '''
        fold_panel = PrefEditPanel(pref = self.pref_manager,
                                  parent = panelBar)

        pref_item = self.pref_manager.get_item('events')[0]
        field = pref_item.gui_element[0]
        fold_panel.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_event_selected, field.controlElement)

        self.events_lb = field.controlElement

        return fold_panel


    def on_load_events(self, event):
        '''
        '''
        self.logger.debug('Loading events.')
        event_table = self.parent.project.dbTables['event']
        db_session = self.parent.project.getDbSession()
        try:
            start_time = self.pref_manager.get_value('start_time')
            duration = self.pref_manager.get_value('window_length')
            query = db_session.query(event_table.id,
                                     event_table.start_time,
                                     event_table.end_time).\
                                     filter(event_table.start_time >= start_time.timestamp).\
                                     filter(event_table.start_time <= (start_time + duration).timestamp)

            events = query.all()
            pref_item = self.pref_manager.get_item('events')[0]
            field = pref_item.gui_element[0]
            field.set_events(events)


        finally:
            db_session.close()


    def on_event_selected(self, event):
        '''
        '''
        selected_row = event.m_itemIndex
        event_id = self.events_lb.GetItemText(selected_row)
        start_time = UTCDateTime(self.events_lb.GetItem(selected_row, 1).GetText())
        end_time = start_time + float(self.events_lb.GetItem(selected_row, 2).GetText())

        # Add the pre- and post event time.
        start_time -= self.pref_manager.get_value('pre_et')
        end_time += self.pref_manager.get_value('post_et')

        self.parent.displayManager.setTimeLimits(startTime = start_time,
                                                 endTime = end_time)
        self.parent.updateDisplay()



class EventListField(wx.Panel):

    def __init__(self, name, pref_item, size, parent = None):
        '''
        '''
        wx.Panel.__init__(self, parent = parent, size = size, id = wx.ID_ANY)

        self.name = name

        self.pref_item = pref_item

        self.size = size

        self.label = name + ":"

        self.labelElement = None

        self.controlElement = None

        self.sizer = wx.GridBagSizer(5,5)

        # Create the field label.
        self.labelElement = StaticText(parent=self,
                                       ID=wx.ID_ANY,
                                       label=self.label,
                                       style=wx.ALIGN_LEFT)

        self.sizer.Add(self.labelElement, pos = (0,0), flag = wx.EXPAND|wx.ALL, border = 0)

        self.controlElement = NodeListCtrl(parent = self, size = (-1, 300),
                                           style = wx.LC_REPORT
                                           | wx.BORDER_NONE
                                           | wx.LC_SINGLE_SEL
                                           | wx.LC_SORT_ASCENDING)

        columns = {1: 'id', 2: 'start time', 3: 'length [s]'}

        for colNum, name in columns.iteritems():
            self.controlElement.InsertColumn(colNum, name)

        self.sizer.Add(self.controlElement, pos = (1,0), flag = wx.EXPAND|wx.ALL, border = 0)
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(1)


        self.SetSizer(self.sizer)

    def __del__(self):
        self.pref_item.remove_gui_element(self)


    def set_events(self, events):
        '''
        '''
        self.controlElement.DeleteAllItems()
        for k, cur_event in enumerate(events):
            self.controlElement.InsertStringItem(k, str(cur_event[0]))
            self.controlElement.SetStringItem(k, 1, UTCDateTime(cur_event[1]).isoformat())
            self.controlElement.SetStringItem(k, 2, str(cur_event[2] - cur_event[1]))







class NodeListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)


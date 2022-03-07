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

import sqlalchemy.orm

import psysmon
import psysmon.core.packageNodes as package_nodes
import psysmon.core.preferences_manager as psy_pm

# Import GUI related modules only if wxPython is available.
if psysmon.wx_available:
    import psysmon.core.gui_preference_dialog as gui_preference_dialog


class TypeFilter(package_nodes.LooperCollectionChildNode):
    ''' Filter events based on their event type.

    '''
    name = 'event type filter'
    mode = 'looper child'
    category = 'filter'
    tags = ['event', 'type']

    def __init__(self, **args):
        ''' Initialize the instance.
        '''
        package_nodes.LooperCollectionChildNode.__init__(self, **args)

        # No waveform data is needed.
        self.need_waveform_data = False

        self.create_filter_preferences()


    def create_filter_preferences(self):
        ''' Create the filter preferences.
        '''
        pref_page = self.pref_manager.add_page('Filter')
        event_group = pref_page.add_group('event')

        # The event type to pass.
        item = psy_pm.SingleChoicePrefItem(name = 'event_type',
                                           label = 'event type',
                                           limit = [],
                                           value = None,
                                           tool_tip = 'The event type to pass to the next nodes.')
        event_group.add_item(item)


    def edit(self):
        ''' Create the preferences edit dialog.
        '''
        # TODO: Visualize the event types in a tree structure.
        # TODO: In the database table: Make the combination of parent_id and name unique, not only the
        # name.
        event_types = self.load_event_types()
        self.pref_manager.set_limit('event_type', [x.name for x in event_types])

        # Create the edit dialog.
        dlg = gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)

        dlg.ShowModal()
        dlg.Destroy()


    def initialize(self):
        ''' Initialize the node.
        '''
        super(TypeFilter, self).initialize()
        # Get the event type to filter.
        self.event_types = self.load_event_types()



    def execute(self, stream, process_limits = None, origin_resource = None, channels = None, **kwargs):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        # Check for needed keyword arguments.
        if not self.kwargs_exists(['event'], **kwargs):
            raise RuntimeError("The needed event argument was not passed to the execute method.")

        event = kwargs['event']
        selected_event_type = self.pref_manager.get_value('event_type')

        if not event.event_type:
            return 'abort'
        elif event.event_type.name != selected_event_type:
            return 'abort'
        else:
            return None


    def load_event_types(self):
        ''' Load the available event types from the database.
        '''
        db_session = self.project.getDbSession()
        event_types = []
        try:
            event_type_table = self.project.dbTables['event_type']
            query = db_session.query(event_type_table)
            query = query.options(sqlalchemy.orm.immediateload(event_type_table.children))
            query = query.options(sqlalchemy.orm.immediateload(event_type_table.parent))
            event_types = query.all()
        finally:
            db_session.close()

        return event_types

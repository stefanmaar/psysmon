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

import obspy.geodetics as geodetics
import sqlalchemy.orm

import psysmon.core.packageNodes as package_nodes
import psysmon.core.preferences_manager as psy_pm
import psysmon.core.gui_preference_dialog as gui_preference_dialog


class QuarryBlastClassification(package_nodes.LooperCollectionChildNode):
    ''' Classification of quarry blast events.

    '''
    name = 'quarry blast classification'
    mode = 'looper child'
    category = 'classification'
    tags = ['mss', 'macroseismic', 'quarry', 'blast']


    def __init__(self, **args):
        ''' Initialize the instance.
        '''
        package_nodes.LooperCollectionChildNode.__init__(self, **args)

        self.create_general_prefs()
        self.create_classification_prefs()

        # The nearest station to the quarry site.
        self.nearest_station = None

        # The neighbors of the nearest station.
        self.neighbor_stations = []


    def create_general_prefs(self):
        ''' Create the general preference items.

        '''
        general_page = self.pref_manager.add_page('General')
        id_group = general_page.add_group('identification')

        # The station nearest to the quarry site.
        item = psy_pm.MultiChoicePrefItem(name = 'nearest_station',
                                          label = 'nearest station',
                                          limit = (),
                                          value = [],
                                          tool_tip = 'The stations nearest to the quarry.')
        id_group.add_item(item)

        # The minimum number of stations with detections.
        item = psy_pm.IntegerSpinPrefItem(name = 'n_stations',
                                          label = 'num. stations',
                                          value = 3,
                                          limit = (1, 1000000),
                                          tool_tip = 'The minimum number of stations with detections.')
        id_group.add_item(item)

        # The ground velocity threshold.
        item = psy_pm.FloatSpinPrefItem(name = 'vel_threshold',
                                        label = 'vel. threshold',
                                        value = 0.1,
                                        limit = (0, 1000000),
                                        digits = 2,
                                        tool_tip = 'The minimum velocity amplitude in mm/s.')
        id_group.add_item(item)


    def create_classification_prefs(self):
        ''' Create the classification preference items.
        '''
        classify_page = self.pref_manager.add_page('classification')
        event_group = classify_page.add_group('event')

        # The type of the classified events.
        item = psy_pm.MultiChoicePrefItem(name = 'event_type',
                                          label = 'type',
                                          limit = (),
                                          value = [],
                                          tool_tip = 'The type of the classified events.')
        event_group.add_item(item)



    def edit(self):
        if self.project.geometry_inventory:
            stations = sorted([x.name for x in self.project.geometry_inventory.get_station()])
            self.pref_manager.set_limit('nearest_station', stations)

        event_types = self.load_event_types()
        quarry_event = [x for x in event_types if x.name == 'quarry'][0]
        self.pref_manager.set_limit('event_type', [x.name for x in quarry_event.children])

        dlg = gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)
        dlg.ShowModal()
        dlg.Destroy()


    def initialize(self):
        ''' Initialize the node.

        '''
        super(QuarryBlastClassification, self).initialize()
        # Compute the neighbor stations.
        nearest_station_name = self.pref_manager.get_value('nearest_station')[0]
        nearest_station = self.project.geometry_inventory.get_station(name = nearest_station_name)[0]
        stations = self.project.geometry_inventory.get_station()
        stations = [x for x in stations if x.name != nearest_station.name]

        station_dist = []
        src_lonlat = nearest_station.get_lon_lat()
        for cur_station in stations:
            dst_lonlat = cur_station.get_lon_lat()
            dist, az1, az2 = geodetics.gps2dist_azimuth(lon1 = src_lonlat[0], lat1 = src_lonlat[1],
                                                        lon2 = dst_lonlat[0], lat2 = dst_lonlat[1])
            station_dist.append((cur_station, dist))

        self.nearest_station = nearest_station
        self.neighbor_stations = sorted(station_dist, key = lambda x: x[1])

        # Get the desired event type.
        event_types = self.load_event_types()
        dst_event_type = self.pref_manager.get_value('event_type')[0]
        self.event_type = [x for x in event_types if x.name == dst_event_type][0]



    def execute(self, stream, process_limits = None, origin_resource = None, **kwargs):
        ''' Execute the looper collection node.

        '''
        # Check for needed keyword arguments.
        if not self.kwargs_exists(['event'], **kwargs):
            raise RuntimeError("The needed event argument was not passed to the execute method.")


        event = kwargs['event']

        # Check for a detection at the nearest station.
        n_stations = self.pref_manager.get_value('n_stations')
        detection_stations = [x.scnl[0] for x in event.detections]
        detection_stations = list(set(detection_stations))
        if self.nearest_station.name not in detection_stations:
            return

        # Check for the minimum number of neighboring stations.
        neighbor_dist = 10000
        neighbors = [x for x in self.neighbor_stations if x[1] <= neighbor_dist]
        neighbors_name = [x[0].name for x in neighbors]
        neighbor_count = 0
        for cur_detection_station in detection_stations:
            if cur_detection_station in neighbors_name:
                neighbor_count += 1

        if neighbor_count >= n_stations:
            self.logger.info("Quarry blast event %d.", event.db_id)
        else:
            self.logger.info("Not enough neighbor stations for a quarry blast classification (db_id: %d).", event.db_id)


        # TODO: Check for the required velocity threshold.


        # Write the classification to the database.
        db_session = self.project.getDbSession()
        events_table = self.project.dbTables['event']
        try:
            db_session.query(events_table).\
                    filter(events_table.id == event.db_id).\
                    update({'ev_type_id': self.event_type.id}, synchronize_session = False)
            db_session.commit()
        finally:
            db_session.close()





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



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
import numpy as np
import psysmon
import psysmon.core.plugins
import psysmon.core.gui_view
import psysmon.artwork.icons as icons
import psysmon.packages.geometry.util as geom_util
import psysmon.core.preferences_manager as preferences_manager

import mpl_toolkits.basemap as basemap



class MapPlotter(psysmon.core.plugins.ViewPlugin):
    '''

    '''
    nodeClass = 'GraphicLocalizationNode'

    def __init__(self): 
        ''' The constructor.

        '''
        psysmon.core.plugins.ViewPlugin.__init__(self,
                                         name = 'map view',
                                         category = 'visualize',
                                         tags = None)

        # Create the logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # Define the plugin icons.
        self.icons['active'] = icons.iconsBlack16.waveform_icon_16

        # Add the plugin preferences.
        # Show or hide the seismogram envelope.
        #item = preferences_manager.CheckBoxPrefItem(name = 'show_envelope',
        #                                            label = 'show envelope',
        #                                            value = False
        #                                           )
        #self.pref_manager.add_item(item = item)



    def plot(self):
        ''' Plot available map plotter views.

        '''

        view_list = self.parent.viewport.get_node(name = self.rid)

        lon_lat = []
        station_name = []
        for cur_net in self.parent.project.geometry_inventory.networks:
            lon_lat.extend([stat.get_lon_lat() for stat in cur_net.stations])
            station_name.extend([x.name for x in cur_net.stations])


        lon = [x[0] for x in lon_lat]
        lat = [x[1] for x in lon_lat]

        for cur_view in view_list:
            if not cur_view.map_config:
                cur_view.init_map(lon_min = np.min(lon, 0),
                                  lon_max = np.max(lon, 0),
                                  lat_min = np.min(lat, 0),
                                  lat_max = np.max(lat, 0))

            cur_view.plot_stations(lon = lon, lat = lat, name = station_name)


    def getViewClass(self):
        ''' Get a class object of the view.

        '''
        return MapView




class MapView(psysmon.core.gui_view.ViewNode):
    ''' A 2D map view.

    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parent_viewport=None, name=None):
        ''' Initialize the instance.
        '''
        psysmon.core.gui_view.ViewNode.__init__(self,
                                                parent=parent,
                                                id=id,
                                                parent_viewport = parent_viewport,
                                                name=name)

        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # Setup the axes.
        self.axes.set_aspect('equal')

        # The map configuration.
        self.map_config = {}


    def init_map(self, lon_min, lon_max, lat_min, lat_max):
        self.map_config['utmZone'] = geom_util.lon2UtmZone(np.mean([lon_min, lon_max]))
        self.map_config['ellips'] = 'wgs84'
        self.map_config['lon_0'] = geom_util.zone2UtmCentralMeridian(self.map_config['utmZone'])
        self.map_config['lat_0'] = 0
        if np.mean([lat_min, lat_max]) >= 0:
            self.map_config['hemisphere'] = 'north'
        else:
            self.map_config['hemisphere'] = 'south'

        #lon_map_extent = lon_max - lon_min
        #lat_map_extent = lat_max - lat_min
        #self.map_config['limits'] = np.hstack([lon_lat_min - map_extent * 0.1, lon_lat_max + map_extent * 0.1]) 

        # Get the epsg code of the UTM projection.
        search_dict = {'projection': 'utm', 'ellps': self.map_config['ellips'].upper(), 'zone': self.map_config['utmZone'], 'no_defs': True, 'units': 'm'}
        if self.map_config['hemisphere'] == 'south':
            search_dict['south'] = True

        epsg_dict = geom_util.get_epsg_dict()
        code = [(c, x) for c, x in epsg_dict.items() if  x == search_dict]

        self.map_config['epsg'] = 'epsg:' + code[0][0]

        # Add some map annotation.
        self.axes.text(0.9, 0.9, self.map_config['epsg'],
            ha = 'right', transform = self.axes.transAxes)

        # Activate the auto scaling.
        self.axes.autoscale(True)




    def plot_stations(self, lon, lat, name):
        ''' Plot the stations.

        '''
        # Get the lon/lat limits of the inventory.
        proj = basemap.pyproj.Proj(init = self.map_config['epsg'])

        # Plot the stations.
        x,y = proj(lon, lat)
        self.axes.scatter(x, y, s=100, marker='^', color='r', picker=5, zorder = 3)
        for cur_name, cur_x, cur_y in zip(name, x, y):
            self.axes.text(cur_x, cur_y, cur_name)




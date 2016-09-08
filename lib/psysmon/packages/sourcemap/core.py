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
'''
The sourcemap module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    http://www.gnu.org/licenses/gpl-3.0.html
'''

import logging
import numpy as np

import psysmon
import psysmon.packages.geometry.inventory as inventory
import psysmon.packages.geometry.util as geom_util
from mpl_toolkits.basemap import pyproj


class Station(inventory.Station):
    ''' The sourcemap station.

    '''
    def __init__(self, station, data_v = None, data_h1 = None, data_h2 = None, corr = 0):
        ''' Initialize the instance.
        '''
        inventory.Station.__init__(self,
                                   name = station.name,
                                   location = station.location,
                                   x = station.x,
                                   y = station.y,
                                   z = station.z,
                                   coord_system = station.coord_system,
                                   description = station.description,
                                   author_uri = station.author_uri,
                                   agency_uri = station.agency_uri,)

        # The epi-distance matrix.
        self.epi_dist = None

        # The hypo-distance matrix.
        self.hypo_dist = None

        # The backprojection matrix.
        self.backprojection = None

        # The weight matrix.
        self.weight = None

        # The station correction for the backprojection.
        self.corr = corr

        # The waveform data.
        self.data_v = data_v
        self.data_h1 = data_h1
        self.data_h2 = data_h2

        # The pseudo-magnitude matrix.
        self.pseudo_mag = None


    @property
    def alt_resultant(self):
        minmax_v = np.abs(np.min(self.data_v)) + np.abs(np.max(self.data_v))
        minmax_h1 = np.abs(np.min(self.data_h1)) + np.abs(np.max(self.data_h1))
        minmax_h2 = np.abs(np.min(self.data_h2)) + np.abs(np.max(self.data_h2))
        return np.sqrt(minmax_v**2 + minmax_h1**2 + minmax_h2**2)




class SourceMap(object):
    ''' The sourcemap.
    '''

    def __init__(self, stations, map_dx = 1000, map_dy = 1000, hypo_depth = 8000, alpha = 1, method = 'min'):
        ''' Initialize the instance.
        '''
        # The logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The list of available stations.
        self.stations = stations

        # The list of stations to use for the computation.
        self.compute_stations = self.stations

        # The map grid spacings.
        self.map_dx = float(map_dx)
        self.map_dy = float(map_dy)

        # The fixed hypocentral depth.
        self.hypo_depth = hypo_depth

        # The alpha value of the backprojection.
        self.alpha = alpha

        # The sourcemap computation method.
        self.method = method

        # The map configuration.
        self.map_config = {}

        # The map grid
        self.map_x_coord = []
        self.map_y_coord = []

        # The resulting source map.
        self.result_map = []


    def compute_map_configuration(self):
        ''' The map limits computed from the stations.
        '''
        # Get the longitude and latidue coordinates of the stations.
        lon_lat = [stat.get_lon_lat() for stat in self.stations]
        lon = [x[0] for x in lon_lat]
        lat = [x[1] for x in lon_lat]

        # Get the UTM zone for the map limits.
        self.map_config['utmZone'] = geom_util.lon2UtmZone(np.mean([np.min(lon), np.max(lon)]))
        self.map_config['ellips'] = 'wgs84'
        self.map_config['lon_0'] = geom_util.zone2UtmCentralMeridian(self.map_config['utmZone'])
        self.map_config['lat_0'] = 0
        if np.mean([np.min(lat), np.max(lat)]) >= 0:
            self.map_config['hemisphere'] = 'north'
        else:
            self.map_config['hemisphere'] = 'south'

        #lon_lat_min = np.min(lon_lat, 0)
        #lon_lat_max = np.max(lon_lat, 0)
        #map_extent = lon_lat_max - lon_lat_min
        #self.map_config['limits'] = np.hstack([lon_lat_min, lon_lat_max])


        # Get the epsg code of the UTM projection.
        search_dict = {'projection': 'utm', 'ellps': self.map_config['ellips'].upper(), 'zone': self.map_config['utmZone'], 'no_defs': True, 'units': 'm'}
        if self.map_config['hemisphere'] == 'south':
            search_dict['south'] = True
        epsg_dict = geom_util.get_epsg_dict()
        code = [(c, x) for c, x in epsg_dict.items() if  x == search_dict]

        self.map_config['epsg'] = 'epsg:'+code[0][0]

        proj = pyproj.Proj(init = self.map_config['epsg'])

        x_coord, y_coord = proj(lon, lat)

        x_min = np.floor(np.min(x_coord) / float(self.map_dx)) * self.map_dx
        x_max = np.ceil(np.max(x_coord) / float(self.map_dx)) * self.map_dx

        y_min = np.floor(np.min(y_coord) / float(self.map_dy)) * self.map_dy
        y_max = np.ceil(np.max(y_coord) / float(self.map_dy)) * self.map_dy

        self.map_config['x_lim'] = (x_min, x_max)
        self.map_config['y_lim'] = (y_min, y_max)


    def compute_map_grid(self):
        ''' Compute the map grid based on the available stations.
        '''
        x_lim = self.map_config['x_lim']
        y_lim = self.map_config['y_lim']
        self.map_x_coord = np.arange(x_lim[0], x_lim[1] + self.map_dx, self.map_dx)
        self.map_y_coord = np.arange(y_lim[0], y_lim[1] + self.map_dy, self.map_dy)
        self.result_map = np.zeros((len(self.map_x_coord), len(self.map_y_coord)))


    def compute_backprojection(self):
        ''' Compute the backprojection matrixes of the stations.
        '''
        x_grid, y_grid = np.meshgrid(self.map_x_coord, self.map_y_coord)

        proj = pyproj.Proj(init = self.map_config['epsg'])

        for cur_station in self.compute_stations:
            stat_lon_lat = cur_station.get_lon_lat()
            stat_x, stat_y = proj(stat_lon_lat[0], stat_lon_lat[1])
            cur_station.epi_dist = np.sqrt((stat_x - x_grid)**2 + (stat_y - y_grid)**2)
            cur_station.hypo_dist = np.sqrt(cur_station.epi_dist**2 + self.hypo_depth**2)
            cur_station.backprojection = self.alpha * np.log10(cur_station.hypo_dist) + cur_station.corr


    def compute_pseudomag(self):
        ''' Compute the pseudo-magnitude.
        '''
        for cur_station in self.compute_stations:
            cur_station.pseudo_mag = np.log10(cur_station.alt_resultant) + cur_station.backprojection
            #cur_station.pseudo_mag = np.log10(np.abs(np.max(cur_station.data_v))) + cur_station.backprojection


    def compute_sourcemap(self):
        ''' Compute the source map.
        '''
        pm_list = [x.pseudo_mag for x in self.compute_stations]
        pm_mat = np.dstack(pm_list)
        if self.method == 'std':
            self.result_map = np.std(pm_mat, axis = 2)
        elif self.method == 'min':
            self.result_map = pm_mat.min(axis = 2)
        elif self.method == 'quart':
            perc_25 = np.percentile(pm_mat, 25., axis = 2)
            perc_75 = np.percentile(pm_mat, 75., axis = 2)
            self.result_map = perc_75 - perc_25
        else:
            self.logging.error('Unknown computation method: %s.', self.method)












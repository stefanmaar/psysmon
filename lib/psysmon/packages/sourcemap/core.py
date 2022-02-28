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
from __future__ import print_function
from __future__ import division

from builtins import str
from builtins import object
from past.utils import old_div
import logging
import numpy as np
import obspy
import obspy.geodetics
import obspy.taup


import psysmon
import psysmon.packages.geometry.inventory as inventory
import psysmon.packages.geometry.util as geom_util
import pyproj


# TODO: Make the number of data components (e.g. Z, N, E) flexible. Use
# N data traces. Using only two channels should work as well.

class Station(inventory.Station):
    ''' The sourcemap station.

    '''
    def __init__(self, station, corr = 0):
        ''' Initialize the instance.
        '''
        inventory.Station.__init__(self,
                                   name = station.name,
                                   location = station.location,
                                   parent_network = station.parent_network,
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

        # The travel time matrix.
        self.tt_grid = {}

        self.weight = []

        # The amplitude representation of the data.
        self.pseudo_amp = None

        # The station correction for the backprojection.
        self.corr = corr

        # The length of the data in seconds.
        self.data_length = None

        # The sampling rate of the station data.
        self.sps = None

        # The list of waveform data.
        self.data = None

        # The pseudo-magnitude matrix.
        self.pseudo_mag = None


    @property
    def time(self):
        return np.arange(self.data.shape[1]) * 1/float(self.sps)

    @property
    def alt_resultant(self):
        minmax = []
        for cur_data in self.data:
            cur_minmax = np.abs(np.min(cur_data)) + np.abs(np.max(cur_data))
            minmax.append(cur_minmax)

        minmax = np.array(minmax)
        return np.sqrt(np.sum(minmax**2))


    def clear(self):
        ''' Clear the data of the sourcemap.
        '''
        self.data = None
        self.pseudo_mag = None
        self.pseudo_amp = None


    def add_data(self, data, sps):
        # TODO: Add a check if the length of the data fits the expected length
        # base on the window_length of the station.
        if len(data) != self.data_length * sps:
            raise ValueError("The length of the passed data doesn't fit the expected data length of the station.")

        if self.sps is None:
            self.sps = sps

        if self.data is None:
            self.data = np.array(data)
        elif len(data) == len(self.data) and self.sps == sps:
            self.data = np.vstack((self.data, data))
        else:
            raise ValueError("The size of the data or the sampling rate doesn't match the existing data.")

        self.logger.debug("The size of data: %s.", self.data.shape())


    def compute_pseudo_amp(self, method = 'weighted'):
        if self.data is None or len(self.data) == 0:
            return

        if method == 'plain':
            self.compute_plain_res()
        elif method == 'weighted':
            self.compute_weighted_res()
        elif method == 'windowed_max':
            self.compute_windowed_max_res()
        else:
            raise ValueError('Wrong value for attribute method.')


    def compute_plain_res(self):
        #v_w = self.data_v[np.newaxis, np.newaxis, ...]
        #h1_w = self.data_h1[np.newaxis, np.newaxis, ...]
        #h2_w = self.data_h2[np.newaxis, np.newaxis, ...]
        #res = np.sqrt(v_w**2 + h1_w**2 + h2_w**2)

        res = np.sqrt(np.sum(self.data**2, axis = 0))
        res = res[np.newaxis, np.newaxis, ...]
        nx = self.epi_dist.shape[0]
        ny = self.epi_dist.shape[1]
        nz = self.data.shape[1]
        alt_res = np.broadcast_to(res, (nx, ny, nz))
        alt_res = np.max(alt_res, axis = 2)

        # Handle zero values. This would cause problems when using the log.
        ind = np.argwhere(alt_res <= 0)
        alt_res[ind[:, 0], ind[:, 1]] = np.min(alt_res[alt_res > 0])

        self.pseudo_amp = alt_res


    def compute_weighted_res(self):
        v_w = self.data_v[np.newaxis, np.newaxis, ...]
        h1_w = self.data_h1[np.newaxis, np.newaxis, ...]
        h2_w = self.data_h2[np.newaxis, np.newaxis, ...]

        alt_res = np.sqrt(v_w**2 + h1_w**2 + h2_w**2)

        nx = self.epi_dist.shape[0]
        ny = self.epi_dist.shape[1]
        nz = len(self.data_v)
        alt_res = np.broadcast_to(alt_res, (nx, ny, nz))

        alt_res = np.sum(alt_res * self.weight, axis = 2)

        # Handle zero values. This will cause problems when using the log.
        ind = np.argwhere(alt_res <= 0)
        #alt_res[ind[:, 0], ind[:, 1]] = np.min(alt_res[alt_res > 0])
        alt_res[ind[:, 0], ind[:, 1]] = 1e-10

        self.pseudo_amp = alt_res


    def compute_windowed_max_res(self):
        #v_w = self.data_v[np.newaxis, np.newaxis, ...]
        #h1_w = self.data_h1[np.newaxis, np.newaxis, ...]
        #h2_w = self.data_h2[np.newaxis, np.newaxis, ...]
        #res = np.sqrt(v_w**2 + h1_w**2 + h2_w**2)

        res = np.sqrt(np.sum(self.data**2, axis = 0))
        res = res[np.newaxis, np.newaxis, ...]
        nx = self.epi_dist.shape[0]
        ny = self.epi_dist.shape[1]
        nz = self.data.shape[1]
        alt_res = np.broadcast_to(res, (nx, ny, nz))
        weight = self.weight.copy()
        weight[weight > 0 ] = 1
        alt_res = np.max(alt_res * weight, axis = 2)

        # Handle zero values. This would cause problems when using the log.
        ind = np.argwhere(alt_res <= 0)
        alt_res[ind[:, 0], ind[:, 1]] = np.min(alt_res[alt_res > 0])

        self.pseudo_amp = alt_res


    def compute_amplitude_weight(self):
        ''' Compute the amplitude weight for each grid point.
        '''
        if self.data is None or len(self.data) == 0:
            return

        # TODO: This matrix is too large for large networks and dense grid
        # spacing. Make it more efficient.
        nx = self.epi_dist.shape[0]
        ny = self.epi_dist.shape[1]
        nz = self.data.shape[1]

        weight = np.zeros((nx, ny, nz))
        print("weight.shape: %s; %d total points; %d MB" % (str(weight.shape), weight.size, old_div(weight.nbytes, (1024 * 1024))))

        time = self.time[np.newaxis, np.newaxis,...]
        time = np.broadcast_to(time, (nx, ny, nz))

        tt_p = self.tt_grid['p'][..., np.newaxis]
        tt_p = np.broadcast_to(tt_p, (nx, ny, nz))
        weight[time >= tt_p] = 1

        tt_s = self.tt_grid['s'][..., np.newaxis]
        tt_s = np.broadcast_to(tt_s, (nx, ny, nz))
        weight[time >= tt_s] = 2

        tt_surf_max = self.tt_grid['surf_max'][..., np.newaxis]
        tt_surf_max = np.broadcast_to(tt_surf_max, (nx, ny, nz))
        weight[time >= tt_surf_max] = 0

        weight_sum = np.sum(weight, axis = 2)
        weight_sum[weight_sum == 0] = 1.
        weight = old_div(weight, np.broadcast_to(weight_sum[..., np.newaxis], (weight.shape[0], weight.shape[1], weight.shape[2])))

        self.weight = weight





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

        # The slowest surface wave velocity [m/s].
        self.v_surf_min = 1500

        # The list of stations to use for the computation.
        self.compute_stations = self.stations

        # The maximum station to station distance.
        self.max_station_dist = None

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

        # The location map.
        self.location_map = []

        # The maximum peak-ground velocity map.
        self.max_pgv_map = []

        # The maximum Modified Mercalli intensity map.
        self.max_mmi_map = []


    @property
    def window_length(self):
        ''' The minimum analyse window length.
        '''
        if self.max_station_dist is not None:
            return old_div(self.max_station_dist, self.v_surf_min)
        else:
            return None

    def clear(self):
        ''' Clear all result variables and the stations.
        '''
        self.result_map = []
        self.location_map = []
        self.max_pgv_map = []
        self.max_mmi_map = []

        for cur_station in self.stations:
            cur_station.clear()


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
        code = [(c, x) for c, x in list(epsg_dict.items()) if  x == search_dict]

        self.map_config['epsg'] = 'epsg:'+code[0][0]

        proj = pyproj.Proj(init = self.map_config['epsg'])

        x_coord, y_coord = proj(lon, lat)

        x_min = np.floor(np.min(x_coord) / float(self.map_dx)) * self.map_dx
        x_max = np.ceil(np.max(x_coord) / float(self.map_dx)) * self.map_dx

        y_min = np.floor(np.min(y_coord) / float(self.map_dy)) * self.map_dy
        y_max = np.ceil(np.max(y_coord) / float(self.map_dy)) * self.map_dy

        self.map_config['x_lim'] = (x_min, x_max)
        self.map_config['y_lim'] = (y_min, y_max)

        # Compute the maximum station to station distance.
        self.compute_station_distance()

        # Set the data length of the stations.
        for cur_station in self.stations:
            cur_station.data_length = np.ceil(self.window_length)


    def compute_map_grid(self):
        ''' Compute the map grid based on the available stations.
        '''
        x_lim = self.map_config['x_lim']
        y_lim = self.map_config['y_lim']
        self.map_x_coord = np.arange(x_lim[0], x_lim[1] + self.map_dx, self.map_dx)
        self.map_y_coord = np.arange(y_lim[0], y_lim[1] + self.map_dy, self.map_dy)
        self.result_map = np.zeros((len(self.map_x_coord), len(self.map_y_coord)))


    def compute_station_distance(self):
        ''' Compute the maximum station to station distance.

        '''
        # Get the longitude and latidue coordinates of the stations.
        lon_lat = [stat.get_lon_lat() for stat in self.stations]
        lon = [x[0] for x in lon_lat]
        lat = [x[1] for x in lon_lat]
        proj = pyproj.Proj(init = self.map_config['epsg'])
        x, y = proj(lon, lat)
        x = np.reshape(x, (len(x), 1))
        y = np.reshape(y, (len(y), 1))
        x_mat = np.tile(np.array(x), (1, len(x)))
        y_mat = np.tile(np.array(y), (1, len(y)))

        rows, cols = np.ogrid[:x_mat.shape[0], :x_mat.shape[1]]
        rows = rows - np.arange(x_mat.shape[0])
        x_mat_roll = x_mat[rows, cols]

        rows, cols = np.ogrid[:y_mat.shape[0], :y_mat.shape[1]]
        rows = rows - np.arange(y_mat.shape[0])
        y_mat_roll = y_mat[rows, cols]

        # Compute the distances between all stations.
        dist = np.sqrt((x_mat - x_mat_roll)**2 + (y_mat - y_mat_roll)**2)
        self.max_station_dist = np.max(dist)


    def compute_distance_grid(self):
        ''' Compute the hypo- and epi-distance for all stations.
        '''
        x_grid, y_grid = np.meshgrid(self.map_x_coord, self.map_y_coord)

        proj = pyproj.Proj(init = self.map_config['epsg'])

        for cur_station in self.compute_stations:
            stat_lon_lat = cur_station.get_lon_lat()
            stat_x, stat_y = proj(stat_lon_lat[0], stat_lon_lat[1])
            cur_station.epi_dist = np.sqrt((stat_x - x_grid)**2 + (stat_y - y_grid)**2)
            cur_station.hypo_dist = np.sqrt(cur_station.epi_dist**2 + (cur_station.z + self.hypo_depth)**2)



    def compute_traveltime_grid(self, dist_step = None):
        ''' Compute the grid of traveltimes for p, s and surface waves.

        '''
        model = obspy.taup.TauPyModel(model = 'iasp91')

        # Use a 10th of the minimum map grid as the traveltime distance step.
        if dist_step is None:
            dist_step = min(self.map_dx, self.map_dy) / 10.

        # Compute the traveltime curves for interpolation.
        dist = np.arange(0, self.max_station_dist + 10 * dist_step, dist_step)
        tt = {}
        tt['p'] = []
        tt['s'] = []
        tt['surf_max'] = []
        mean_station_height = np.mean([x.z for x in self.compute_stations])
        mean_hypo_depth = self.hypo_depth + mean_station_height
        for cur_dist in dist:
            cur_dist_deg = obspy.geodetics.base.kilometer2degrees(old_div(cur_dist, 1000))
            p_arrivals = model.get_travel_times(source_depth_in_km = mean_hypo_depth / 1000.,
                                                distance_in_degree = cur_dist_deg,
                                                phase_list = ['ttp'])
            tt['p'].append(p_arrivals[0].time)
            s_arrivals = model.get_travel_times(source_depth_in_km = mean_hypo_depth / 1000.,
                                                distance_in_degree = cur_dist_deg,
                                                phase_list = ['tts'])
            tt['s'].append(s_arrivals[0].time)
            surf_arrivals = model.get_travel_times(source_depth_in_km = 0.,
                                                   distance_in_degree = cur_dist_deg,
                                                   phase_list = ['1.5kmps'])
            tt['surf_max'].append(surf_arrivals[0].time)

        for cur_key in tt:
            tt[cur_key] = np.array(tt[cur_key])


        for cur_station in self.compute_stations:
            cur_station.tt_grid['p'] = np.interp(cur_station.hypo_dist, dist, tt['p'])
            cur_station.tt_grid['s'] = np.interp(cur_station.hypo_dist, dist, tt['s'])
            cur_station.tt_grid['surf_max'] = np.interp(cur_station.epi_dist, dist, tt['surf_max'])

            #epi_dist_deg = obspy.geodetics.base.kilometer2degrees(cur_station.epi_dist / 1000)
            #tt_grid = {}
            #tt_grid['p'] = np.zeros(epi_dist_deg.shape)
            #tt_grid['s'] = np.zeros(epi_dist_deg.shape)
            #tt_grid['surf_max'] = np.zeros(epi_dist_deg.shape)
            #it = np.nditer(op = [epi_dist_deg,
            #                     tt_grid['p'],
            #                     tt_grid['s'],
            #                     tt_grid['surf_max']],
            #               flags = ['buffered'],
            #               op_flags = [['readonly'],
            #                           ['writeonly', 'allocate', 'no_broadcast'],
            #                           ['writeonly', 'allocate', 'no_broadcast'],
            #                           ['writeonly', 'allocate', 'no_broadcast']])
            #for cur_epi_dist, cur_tt_p, cur_tt_s, cur_tt_surf in it:
            #    p_arrivals = model.get_travel_times(source_depth_in_km = hypo_depth / 1000.,
            #                                        distance_in_degree = cur_epi_dist,
            #                                        phase_list = ['ttp'])
            #    s_arrivals = model.get_travel_times(source_depth_in_km = hypo_depth / 1000.,
            #                                        distance_in_degree = cur_epi_dist,
            #                                        phase_list = ['tts'])
            #    surf_slow_arrivals = model.get_travel_times(source_depth_in_km = hypo_depth / 1000.,
            #                                           distance_in_degree = cur_epi_dist,
            #                                           phase_list = ['1.5kmps'])
            #
            #    cur_tt_p[...] = p_arrivals[0].time
            #    cur_tt_s[...] = s_arrivals[0].time
            #    cur_tt_surf[...] = surf_slow_arrivals[0].time


    def compute_amplitude_weight(self):
        ''' Compute the weight matrix based on seismic travel times.

        '''
        for cur_station in [x for x in self.compute_stations if len(x.weight) == 0]:
            cur_station.compute_amplitude_weight()


    def compute_pseudo_amp(self, method = 'weighted'):
        ''' Compute the weight matrix based on seismic travel times.

        '''
        for cur_station in self.compute_stations:
            cur_station.compute_pseudo_amp(method = method)




    def compute_backprojection(self, use_station_corr = True):
        ''' Compute the backprojection matrixes of the stations.
        '''
        for cur_station in self.compute_stations:
            if use_station_corr:
                self.logger.info("Using station correction %s:  %f.", ':'.join((cur_station.network, cur_station.name, cur_station.location)), cur_station.corr)
                cur_station.backprojection = self.alpha * np.log10(cur_station.hypo_dist) + cur_station.corr
            else:
                cur_station.backprojection = self.alpha * np.log10(cur_station.hypo_dist)


    def compute_pseudomag(self):
        ''' Compute the pseudo-magnitude.
        '''
        for cur_station in self.compute_stations:
            if cur_station.pseudo_amp is None:
                continue
            #cur_station.pseudo_mag = np.log10(2 * np.pi * cur_station.pseudo_amp) + cur_station.backprojection
            cur_station.pseudo_mag = np.log10(cur_station.pseudo_amp * 1e3) - 2.074 + cur_station.backprojection


    def compute_sourcemap(self, method = None):
        ''' Compute the source map.
        '''
        if method is None:
            method = self.method

        pm_list = [x.pseudo_mag for x in self.compute_stations if x.pseudo_mag is not None]
        if len(pm_list) == 0:
            self.logger.error("No data available to compute the sourcemap.")
            return

        pm_mat = np.dstack(pm_list)
        if method == 'std':
            self.result_map = np.std(pm_mat, axis = 2)
        elif method == 'min':
            self.result_map = pm_mat.min(axis = 2)
        elif method == 'quart':
            perc_25 = np.percentile(pm_mat, 25., axis = 2)
            perc_75 = np.percentile(pm_mat, 75., axis = 2)
            self.result_map = perc_75 - perc_25
        elif method == 'minmax':
            map_min = pm_mat.min(axis = 2)
            map_max = pm_mat.max(axis = 2)
            self.result_map = map_max - map_min
        else:
            self.logging.error('Unknown computation method: %s.', method)
        self.location_map = np.std(pm_mat, axis = 2)


    def compute_max_pgv_map(self, hypo_depth = None):
        ''' Compute the map of the maximal peag-ground-velocities.
        '''
        if hypo_depth is None:
            hypo_depth = self.hypo_depth
        m = np.reshape(self.result_map, (1, 1, -1))
        m = np.broadcast_to(m, (self.result_map.shape[0], self.result_map.shape[1], m.shape[2]))
        x_grid, y_grid, z_grid = np.meshgrid(self.map_x_coord, self.map_y_coord, np.arange(m.shape[2]))
        m_x = np.reshape(x_grid[:,:,0], (1, 1, -1))
        m_x = np.broadcast_to(m_x, (self.result_map.shape[0], self.result_map.shape[1], m.shape[2]))
        m_y = np.reshape(y_grid[:,:,0], (1, 1, -1))
        m_y = np.broadcast_to(m_y, (self.result_map.shape[0], self.result_map.shape[1], m.shape[2]))
        dist = np.sqrt((m_x - x_grid)**2 + (m_y - y_grid)**2 + hypo_depth**2)
        pgv = old_div(10**m, (2*np.pi) * (dist**-self.alpha))
        self.max_pgv_map = np.max(pgv, axis = 2)

        # Compute the Modified Mercalli intensity using the mapping laws from Wald (1999).
        self.max_mmi_map = 2.10 * np.log10(self.max_pgv_map * 100) + 3.4
        mask = self.max_pgv_map > 0.080
        self.max_mmi_map[mask] = 3.47 * np.log10(self.max_pgv_map[mask] * 100) + 2.35
        self.max_mmi_map[self.max_mmi_map < 0] = 0.










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
The pSysmon result module.

:copyright:
    Mertl Research GmbH

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)

This module contains the pSysmon result system.
'''

import os
import itertools
from operator import attrgetter

import numpy as np


class ResultBag(object):
    ''' A container holding results.
    '''

    def __init__(self):
        ''' Initialize the instance.
        '''
        # A dictionary with the resource_ids as keys.
        self.results = {}


    def add(self, resource_id, results):
        ''' Add results computed for a certain resource.

        Parameters
        ----------
        resource_id : String
            The id of the resource for which the results where computed.

        results : List of :class:`Result` or :class:`Result` instance
            The results to add to the bag.
        '''
        if resource_id not in self.results.keys():
            self.results[resource_id] = {}

        for cur_result in results:
            cur_result.origin_resource = resource_id
            self.results[resource_id][cur_result.rid] = cur_result


    def save(self, output_dir, scnl, group_by = 'result', format = 'csv'):
        ''' Save the results in the specified format.

        '''
        if format == 'csv':
            self.save_csv(output_dir = output_dir,
                          scnl = scnl,
                          group_by = group_by)


    def save_csv(self, output_dir, scnl, group_by):
        ''' Save the results in CSV format.

        '''
        import csv

        if group_by == 'result':
            result_rids = list(set(list(itertools.chain.from_iterable(self.results.values()))))
            for cur_result_rid in result_rids:
                results_to_export = self.get_results(result_rid = cur_result_rid)
                export_values = []
                for cur_result in results_to_export:
                    scnl, values = cur_result.get_as_list(scnl)
                    values.reverse()
                    try:
                        id_only = cur_result.origin_resource.split('/')[-1]
                        if id_only.isdigit():
                            id_only = int(id_only)
                    except:
                        id_only = ''
                    values.append(id_only)
                    values.append(cur_result.origin_resource)
                    values.reverse()
                    export_values.append(values)



                # Save the export values to a csv file.
                filename = cur_result_rid.replace('/', '-')
                if filename.startswith('-'):
                    filename = filename[1:]
                if filename.endswith('-'):
                    filename = filename[:-1]
                filename = filename + '.csv'
                filename = os.path.join(output_dir, filename)

                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                fid = open(filename, 'wt')
                try:
                    header = ['resource', 'id']
                    header.extend(['.'.join(x) for x in scnl])
                    writer = csv.writer(fid, quoting = csv.QUOTE_MINIMAL)
                    writer.writerow(header)
                    writer.writerows(export_values)
                finally:
                    fid.close()




    def get_results(self, resource_rid = None, result_rid = None):
        ''' Get the results based on some search criteria.

        '''
        ret_val = sorted(list(itertools.chain.from_iterable([x.values() for x in self.results.values()])),
                         key = attrgetter('rid', 'origin_resource'),
                         reverse = False)

        if result_rid:
            ret_val = [x for x in ret_val if x.rid == result_rid]

        if resource_rid:
            ret_val = [x for x in ret_val if x.rid == result_rid]

        return ret_val






class Result(object):
    ''' A result of a processing node.

    Processing nodes can produce results which are than stored in the
    processing stack for further use.
    The origin is a unique identifier of the processing node which created
    the result.
    When executing a processing stack several times in a loop, e.g when
    processing a list of events, the results of each loop can be
    added to an existing result of the same origin.
    '''

    def __init__(self, name, origin_name, origin_pos = None,
                 origin_resource = None, metadata = None):
        ''' Initialize the instance.
        '''
        # The name of the result.
        self.name = name

        # The node which created the result.
        self.origin_name = origin_name

        # The position of the origin node in the stack.
        self.origin_pos = origin_pos

        # The result data.
        self.values = {}

        # The parent resource ID for which the result was computed.
        self.origin_resource = origin_resource

        # Additional values describing the result data.
        if metadata:
            self.metadata = metadata
        else:
            self.metadata = {}


    @property
    def rid(self):
        ''' The resource ID of the result.
        '''
        name_slug = self.name.replace(' ', '_')
        origin_name_slug = self.origin_name.replace(' ', '_')
        return '/result/' + origin_name_slug + '/' + str(self.origin_pos) + '/' + name_slug



    def add_value(self, scnl, value):
        ''' Add a value to the result.
        '''
        self.values[scnl] = value


    def get_as_list(self, scnl = None):
        ''' Get the results as a list.

        Parameters
        ----------
        scnl : List of tuples
            The SCNL codes for which to get the results.
            If scnl is None, all results are returned.

        Returns
        -------
        A list of results in the order of the scnl list.
        '''
        assert False, 'get_as_list must be defined'





class ValueResult(Result):
    ''' A result representing a single value.

    '''
    def __init__(self, **kwargs):
        ''' Initialize the instance.

        '''
        Result.__init__(self, **kwargs)


    def get_as_list(self, scnl = None):
        ''' Get the results as a list.

        Parameters
        ----------
        scnl : List of tuples
            The SCNL codes for which to get the results.
            If scnl is None, all results are returned.

        Returns
        -------
        A list of results in the order of the scnl list.
        '''
        if scnl is None:
            scnl = self.values.keys()

        return scnl, [self.values.get(key, None) for key in scnl]




class Grid2dResult(Result):
    ''' A result representing a 2D grid.
    '''
    def __init__(self, **kwargs):
        ''' Initialize the instance.
        '''
        Result.__init__(self, **kwargs)

        self.x_coord = []

        self.y_coord = []

        self.grid = []

        self.start_time = None

        self.end_time = None

        self.epsg = None


    def add_grid(self, grid, x_coord, y_coord, dx, dy, start_time, end_time, nodata_value = -9999, epsg = None):
        ''' Add a grid to the result.
        '''
        self.grid = grid

        self.x_coord = x_coord

        self.y_coord = y_coord

        self.dx = dx

        self.dy = dy

        self.start_time = start_time

        self.end_time = end_time

        self.nodata_value = nodata_value

        self.epsg = epsg


    def save(self, formats = ['ascii_grid',], output_dir = None):
        ''' Save the result in the specified format.

        Parameters
        ----------
        format : List of Strings
            The formats in which the result should be written.
            ('ascii_grid', 'png')
        '''

        for cur_format in formats:
            if cur_format == 'ascii_grid':
                self.save_ascii_grid(output_dir = output_dir)
            elif cur_format == 'png':
                self.save_png(output_dir = output_dir)
            else:
                # TODO: Throw an exception.
                pass

    def save_png(self, output_dir):
        ''' Save the result as a png image.
        '''
        # TODO: Think about a consistent method to save results, that provide a
        # single file output like the grid_2d and those that provide outputs
        # that can be combined in a spreadsheet like the value results. The
        # saving currently is not consistent. See also the todo note in
        # window_processor modul in the process method.
        from mpl_toolkits.basemap import pyproj
        import matplotlib.pyplot as plt

        map_config = self.metadata['map_config']
        proj = pyproj.Proj(init = map_config['epsg'])
        #stat_lon_lat = [x.get_lon_lat() for x in sm.compute_stations]
        #stat_lon = [x[0] for x in stat_lon_lat]
        #stat_lat = [x[1] for x in stat_lon_lat]
        #stat_x, stat_y = proj(stat_lon, stat_lat)
        plt.pcolormesh(self.x_coord, self.y_coord, self.grid, cmap = 'rainbow')
        plt.colorbar()
        plt.contour(self.x_coord, self.y_coord, self.grid, colors = 'k')
        #plt.scatter(stat_x, stat_y)
        plt.show()


    def save_ascii_grid(self, output_dir):
        ''' Save the result in ascii grid format.
        '''
        import json

        if self.dx != self.dy:
            #self.logger.error("The grid cell size in dx (%f) and dy(%f) are not equal. Can't save in ASCII grid format.", self.dx, self.dy)
            return

        if not output_dir:
            output_dir = ''

        header = "ncols     %s\n" % self.grid.shape[1]
        header += "nrows    %s\n" % self.grid.shape[0]
        header += "xllcorner %f\n" % self.x_coord[0]
        header += "yllcorner %f\n" % self.y_coord[0]
        header += "cellsize %f\n" % self.dx
        header += "NODATA_value %f\n" % self.nodata_value

        filename = self.rid.replace('/', '-')
        if filename.startswith('-'):
            filename = filename[1:]
        if filename.endswith('-'):
            filename = filename[:-1]

        asc_filename = filename + '_' + self.start_time.isoformat().replace(':', '').replace('.', '') + '_' + self.end_time.isoformat().replace(':', '').replace('.', '') + '.asc'

        json_filename = filename + '_' + self.start_time.isoformat().replace(':', '').replace('.', '') + '_' + self.end_time.isoformat().replace(':', '').replace('.', '') + '_metadata.json'

        prj_filename = filename + '_' + self.start_time.isoformat().replace(':', '').replace('.', '') + '_' + self.end_time.isoformat().replace(':', '').replace('.', '') + '.prj'

        output_dir = os.path.join(output_dir, self.name)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        asc_filename = os.path.join(output_dir, asc_filename)
        json_filename = os.path.join(output_dir, json_filename)
        prj_filename = os.path.join(output_dir, prj_filename)

        np.savetxt(asc_filename,
                   np.flipud(self.grid),
                   comments = '',
                   header=header)
        #self.logger.info("Saved %s result %s to file %s.", self.res_type, self.rid, self.asc_filename)

        if self.epsg:
            with open(prj_filename, 'w') as fp:
                fp.write('PROJCS[\nAUTHORITY["EPSG","%s"]\n]' % self.epsg.split(':')[1])

        with open(json_filename, 'w') as fp:
            json.dump(self.metadata, fp, indent = 4, sort_keys = True)
            #self.logger.info("Saved %s metadata %s to file %s.", self.res_type, self.rid, self.json_filename)








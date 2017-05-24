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
import warnings

import numpy as np


class ResultBag(object):
    ''' A container holding results.
    '''

    def __init__(self):
        ''' Initialize the instance.
        '''
        # A list holding all results.
        self.results = []


    def add(self, results):
        ''' Add results computed for a certain resource.

        Parameters
        ----------
        results : List of :class:`Result` or :class:`Result` instance
            The results to add to the bag.
        '''
        import collections
        if not isinstance(results, collections.Iterable):
            results = [results, ]

        self.results.extend(results)


    def clear(self):
        ''' Remove all results from the bag.
        '''
        self.results = []


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




    def get_results(self, **kwargs):
        ''' Get the results based on some search criteria.

        '''
        #ret_val = sorted(list(itertools.chain.from_iterable([x.values() for x in self.results.values()])),
        #                 key = attrgetter('rid', 'origin_resource'),
        #                 reverse = False)
        ret_val = self.results

        valid_keys = ['resource_id', 'result_rid', 'name']

        for cur_key, cur_value in kwargs.iteritems():
            if cur_key in valid_keys:
                ret_val = [x for x in ret_val if getattr(x, cur_key) == cur_value]
            else:
                warnings.warn('Search attribute %s is not existing.' % cur_key, RuntimeWarning)

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
                 origin_resource = None, metadata = None,
                 start_time = None, end_time = None, postfix = None,
                 sub_directory = None):
        ''' Initialize the instance.
        '''
        # The name of the result.
        self.name = name

        # The node which created the result.
        self.origin_name = origin_name

        # The position of the origin node in the stack.
        self.origin_pos = origin_pos

        # The parent resource ID for which the result was computed.
        self.origin_resource = origin_resource

        # The start time of the time window to which the result is associated.
        self.start_time = start_time

        # The end time of the time window to which the result is associated.
        self.end_time = end_time


        # The directory structure created for the result.
        self.sub_directory = sub_directory

        # The filename postfix.
        self.postfix = postfix

        # The default filename extension. Should be overwritten by the
        # subclasses.
        self.filename_ext = 'dat'

        # The base output directory.
        self.base_output_dir = ''

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
        return '/result/' + origin_name_slug + '/' + name_slug + '/' + self.start_time.isoformat().replace(':', '').replace('-', '') + '-' + self.end_time.isoformat().replace(':', '').replace('-', '')


    @property
    def filename(self):
        ''' The filename of the result.
        '''
        filename = self.name.lower() + '_' \
                   + self.start_time.isoformat().replace(':', '').replace('.', '').replace('-','') \
                   + '_' \
                   + self.end_time.isoformat().replace(':', '').replace('.', '').replace('-','')

        if self.postfix:
            filename += '_' + self.postfix

        filename += '.' + self.filename_ext
        return filename


    @property
    def output_dir(self):
        ''' The output sub directory of the result.
        '''
        output_dir = self.base_output_dir
        output_dir = os.path.join(output_dir, self.name)

        if self.sub_directory:
            output_dir = os.path.join(output_dir, *self.sub_directory)

        return output_dir


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
    def __init__(self, value, **kwargs):
        ''' Initialize the instance.

        '''
        Result.__init__(self, **kwargs)

        # The result data.
        self.value = value


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



class TableResult(Result):
    ''' A table holding one or more single value Results.
    '''

    def __init__(self, key_name, column_names, **kwargs):
        ''' Initialize the instance.

        Parameters
        ----------
        column_names : List of String
            The names of the columns of the table.
        '''
        Result.__init__(self, **kwargs)

        self.key_name = key_name

        self.column_names = column_names

        self.rows = []

    def add_row(self, key, **kwargs):
        ''' Add a value result to the spreadsheet.

        Parameters
        ----------
        result : :class:`ValueResult` instance
            The result to add to the spreadsheet.
        '''
        row = TableResultRow(key, self.column_names)
        row.add_cells(**kwargs)
        self.rows.append(row)


    def save(self, formats = ['csv', ], output_dir = None):
        ''' Save the result in the specified format.

        Parameters
        ----------
        format : List of Strings
            The formats in which the result should be written.
            ('csv')
        '''
        for cur_format in formats:
            if cur_format == 'csv':
                self.save_csv(output_dir = output_dir)
            else:
                # TODO: Throw an exception.
                pass

    def save_csv(self, output_dir):
        '''Save the result in CSV format.
        '''
        import csv

        export_values = []
        for cur_row in self.rows:
            cur_values = [cur_row.key, self.start_time.isoformat(), self.end_time.isoformat()]
            cur_values.extend([cur_row[key] for key in self.column_names])
            #cur_values.reverse()
            #try:
            #    id_only = cur_row.origin_resource.split('/')[-1]
            #    if id_only.isdigit():
            #        id_only = int(id_only)
            #except:
            #    id_only = ''
            #cur_values.append(id_only)
            #cur_values.append(cur_row.origin_resource)
            #cur_values.reverse()
            for k, cur_value in enumerate(cur_values):
                if isinstance(cur_value, unicode):
                    cur_values[k] = cur_value.encode('utf8')
            export_values.append(cur_values)

        # Save the export values to a csv file.
        filename = self.rid.replace('/', '-')
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
            header = [self.key_name, 'start_time', 'end_time']
            header.extend(self.column_names)
            writer = csv.writer(fid, quoting = csv.QUOTE_MINIMAL)
            writer.writerow(header)
            writer.writerows(export_values)
        finally:
            fid.close()



class TableResultRow(object):
    ''' Row of the table result class.
    '''

    def __init__(self, key, columns):
        ''' Initialize the instance.

        Parameters
        ----------
        key : String or number
            The row identifier.
        '''
        self.key = key

        self.cells = {}
        for cur_column in columns:
            self.cells[cur_column] = None


    def __getitem__(self, key):
        ''' Return the cell value of the column key.
        '''
        return self.cells[key]


    def add_cells(self, **kwargs):
        ''' Add values to the row.
        '''
        for cur_key, cur_value in kwargs.iteritems():
            if cur_key in self.cells.keys():
                self.cells[cur_key] = cur_value
            else:
                warnings.warn('The specified key %s was not found in the row columns %s.' % (cur_key, self.cells.keys()), RuntimeWarning)






class Grid2dResult(Result):
    ''' A result representing a 2D grid.
    '''
    def __init__(self, grid, x_coord, y_coord, dx, dy, nodata_value = -9999, epsg = None, **kwargs):
        ''' Initialize the instance.
        '''
        Result.__init__(self, **kwargs)

        self.grid = grid

        self.x_coord = x_coord

        self.y_coord = y_coord

        self.dx = dx

        self.dy = dy

        self.epsg = epsg

        self.nodata_value = nodata_value


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



class ShelveResult(Result):
    ''' A shelve dictionary result.
    '''
    def __init__(self, db, **kwargs):
        ''' Initialize the instance.

        Parameters
        ----------
        db : Dictionary
            The pickle-able instances.
        '''
        Result.__init__(self, **kwargs)

        if not isinstance(db, dict):
            raise ValueError("db has to be a dictionary.")
        self.db = db

        self.filename_ext = 'db'


    def save(self):
        ''' Save the result as a shelve file.
        '''
        import shelve

        #filename = self.rid.replace('/', '-')
        #if filename.startswith('-'):
        #    filename = filename[1:]
        #if filename.endswith('-'):
        #    filename = filename[:-1]

        #filename = filename + '_' + self.start_time.isoformat().replace(':', '').replace('.', '') + '_' + self.end_time.isoformat().replace(':', '').replace('.', '') + '.db'

        #output_dir = os.path.join(output_dir, self.name)

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        #if self.sub_directory:
        #    output_dir = os.path.join(output_dir, *self.sub_directory)
        #    os.makedirs(output_dir)
        #filename = os.path.join(output_dir, self.filename)

        filename = os.path.join(self.output_dir, self.filename)

        db = shelve.open(filename)
        db.update(self.db)
        db.close()










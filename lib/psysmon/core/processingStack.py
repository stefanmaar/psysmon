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
The pSysmon processingStack module.

:copyright:
    Mertl Research GmbH

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)

This module contains the pSysmon processingStack system.
'''

import os
import copy
import itertools
import weakref
import logging
from operator import attrgetter

import psysmon
from psysmon.core.preferences_manager import PreferencesManager
from psysmon.core.guiBricks import PrefEditPanel

import numpy as np

class ProcessingStack:
    ''' The ProcessingStack class.

    The processing stack handles the editing and execution of the processing nodes.
    Processing nodes can be added to the stack. The position in the stack can be 
    changed. 
    When executing the processing stack, each processing node contained in the stack 
    is executed from top to bottom. 
    The processing stack takes care about passing the correct data to the processingNode
    and to pass the processed data to the next processing node.
    '''
    def __init__(self, name, project, nodes = None, parent = None):
        ''' The constructor

        '''
        # The name of the processing stack.
        self.name = name

        # The list of the processing nodes contained in the processing
        # stack.
        if nodes is None:
            self.nodes = []
        else:
            self.nodes = nodes
            for cur_node in self.nodes:
                cur_node.parentStack = self

        # The current project.
        self.project = project

        # The object holding the processing stack.
        if parent is not None:
            self._parent = weakref.ref(parent)
        else:
            self._parent = None


    @property
    def geometry_inventory(self):
        ''' The geometry inventory of the parent project.
        '''
        return self.project.geometry_inventory

    @property
    def parent(self):
        '''
        '''
        if self._parent is None:
            return self._parent
        else:
            return self._parent()


    def __getitem__(self, index):
        ''' Get a node at a given position of the processing stack.

        Parameters
        ----------
        index : Integer
            The index of the collection node to get from the nodes list.
        '''
        return self.nodes[index]


    def get_settings(self, upper_node_limit = None):
        ''' Get the settings of the nodes in the processing stack.

        The upper limit can be set by the upper_node_limit attribute.
        '''
        settings = []
        for cur_node in self.nodes:
            settings.append(cur_node.settings)

            if cur_node == upper_node_limit:
                break

        return settings


    def addNode(self, nodeTemplate, position = -1):
        ''' Add a node to the processing stack.

        Insert a node before a specified position in the processing stack.
        If the position is set to -1, the node is appended at the end of the stack.

        Parameters
        ----------
        node : :class:`~psysmon.core.processingStack.ProcessingNode`
            The node to be added to the collection.
        position : Integer
            The position in the stack before which the node should be inserted.
        '''
        node = copy.deepcopy(nodeTemplate)
        node.parentStack = self
        if position==-1:
            self.nodes.append(node)
        else:
            self.nodes.insert(position, node)


    def popNode(self, position):
        ''' Remove a node from the stack.

        Parameters
        ----------
        position : Integer
            The position of the node which should be removed.
        '''
        if len(self.nodes) > 0:
            return self.nodes.pop(position)


    def editNode(self, position):
        ''' Edit a node.

        Edit the node at a given position in the stack. This is done by 
        calling the :meth:`~psysmon.core.processingStack.ProcessingNode.edit()` 
        method of the according instance.

        Parameters
        ----------
        position : Integer
            The position in the stack of the node to edit.
        '''
        self.nodes[position].edit()



    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the stack.

        Parameters
        ----------

        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        for curNode in self.nodes:
            curNode.clear_results()
            if curNode.isEnabled():
                curNode.execute(stream, process_limits, origin_resource)


    def clear_results(self):
        ''' Clear the results of all processing nodes.
        '''
        for cur_node in self.nodes:
            cur_node.clear_results()


    def get_results(self):
        ''' Get all results of the processing nodes.
        '''
        return list(itertools.chain.from_iterable([x.results.values() for x in self.nodes]))






class ProcessingNode:
    ''' The ProcessingNode class.

    The processing node gets data from the processing stack, does some computation with 
    this data and returns the processed data to the processing stack.
    The type of data needed has to be defined by the ProcessingNode. Currently the processing 
    of obspy Stream objects is supported.
    The return value has to be of the same type as the data passed to the processing node.
    '''
    # The class to which the processing node is assigned to.
    # User *common* for nodes which can be used by every class.
    # Nodes with a specified nodeClass usually depend on some special 
    # variables which have to be passed to them using the variable kwargs 
    # argument.
    nodeClass = 'common'

    def __init__(self, name, mode, category, tags, enabled = True, docEntryPoint=None, parentStack=None):
        ''' The constructor

        '''
        # The name of the stack node.
        self.name = name

        # The mode of the stack node (editable, uneditable).
        self.mode = mode

        # The category of the stack node.
        self.category = category

        # The tags assigned to the stack node.
        self.tags = tags

        # The result of the processing node.
        self.results = {}

        # The preferences of the stack node.
        self.pref_manager = PreferencesManager()

        # The entry point of the documentation of the node.
        self.docEntryPoint = docEntryPoint

        # The parent stack holding the stack node.
        self.parentStack = parentStack

        # The enabled state of the node.
        self.enabled = enabled

    @property
    def settings(self):
        ''' The configuration settings of the node.
        '''
        settings = {}
        settings[self.name] = self.pref_manager.settings
        return settings


    def __getstate__(self):
        ''' Remove instances that can't be pickled.
        '''
        result = self.__dict__.copy()

        # The following attributes can't be pickled and therefore have
        # to be removed.
        # These values have to be reset when loading the project.
        if 'logger' in result.keys():
            del result['logger']
        return result


    def __setstate__(self, d):
        ''' Fill missing attributes after unpickling.

        '''
        self.__dict__.update(d) # I *think* this is a safe way to do it
        #print dir(self)

        # Track some instance attribute changes.
        if not "logger" in dir(self):
            logger_prefix = psysmon.logConfig['package_prefix']
            loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
            self.logger = logging.getLogger(loggerName)



    def isEnabled(self):
        ''' Check the enabled state of the node.

        '''
        return self.enabled



    def toggleEnabled(self):
        ''' Toggle the enabled state of the node.

        '''
        self.enabled = not self.enabled




    def getEditPanel(self, parent):
        ''' The method to build and return the edit panel for the processing 
        stack GUI.

        '''
        return PrefEditPanel(pref = self.pref_manager,
                             parent = parent)



    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the stack node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        assert False, 'execute must be defined'


    def update_pref_manager(self, pref_manager):
        ''' Update the existing preferences manager with the one passed as an argument.

        This is used when loading a psysmon project. The preference items are created
        during the instance initialization of the processing nodes.
        The values saved in the project file are not updated. The update is done
        using this method.
        '''
        self.pref_manager.update(pref_manager)



    def add_result(self, name, res_type = 'value', description = None,
                   origin_resource = None, custom_class = None, **kwargs):
        ''' Add a result.

        Parameters
        ----------
        result : object
            The result to add to the processing node results.

        res_type : String
            The type of the result to add. ('value', 'custom')

        custom_class : class inhereted from :class:`ProcessingResult`
            The custom class of a result of kind 'custom'.
        '''
        if name not in self.results.keys():
            if res_type == 'value':
                self.results[name] = ValueResult(name = name,
                                                 origin_name = self.name,
                                                 origin_pos = self.parentStack.nodes.index(self),
                                                 res_type = res_type,
                                                 description = description,
                                                 origin_resource = origin_resource)
            elif res_type == 'grid_2d':
                self.results[name] = Grid2dResult(name = name,
                                                  origin_name = self.name,
                                                  origin_pos = self.parentStack.nodes.index(self),
                                                  description = description,
                                                  origin_resource = origin_resource)
            else:
                raise ValueError('The result of type %s is not supported.' % res_type)

        if self.results[name].type != res_type:
            raise ValueError("The type %s of the existing results doesn't match the type %s of the result to add." % (self.results[name].type, res_type))


        if res_type == 'value':
            self.results[name].add_value(scnl = kwargs['scnl'],
                                         value = kwargs['value'])
        elif res_type == 'grid_2d':
            self.results[name].add_grid(grid = kwargs['grid'],
                                        x_coord = kwargs['x_coord'],
                                        y_coord = kwargs['y_coord'],
                                        dx = kwargs['dx'],
                                        dy = kwargs['dy'],
                                        start_time = kwargs['start_time'],
                                        end_time = kwargs['end_time'])



    def clear_results(self):
        ''' Remove the results.
        '''
        self.results = {}


    def get_result_names(self):
        ''' Get the available result names.

        '''
        return list(set([x.name for x in self.results]))




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

        results : List of :class:`Result`
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

    def __init__(self, name, origin_name, origin_pos, res_type = None,
                 origin_resource = None, description = None):
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

        # The type of the result.
        self.type = res_type

        # The parent resource ID for which the result was computed.
        self.origin_resource = origin_resource

        # Additional values describing the result data.
        if description:
            self.description = description
        else:
            self.description = {}


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
    def __init__(self, res_type = 'grid_2d', **kwargs):
        ''' Initialize the instance.
        '''
        Result.__init__(self, res_type = 'grid_2d', **kwargs)

        self.x_coord = []

        self.y_coord = []

        self.grid = []

        self.start_time = None

        self.end_time = None


    def add_grid(self, grid, x_coord, y_coord, dx, dy, start_time, end_time, nodata_value = -9999):
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

        map_config = self.description['map_config']
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

        json_filename = filename + '_' + self.start_time.isoformat().replace(':', '').replace('.', '') + '_' + self.end_time.isoformat().replace(':', '').replace('.', '') + '_description.json'

        output_dir = os.path.join(output_dir, self.name)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        asc_filename = os.path.join(output_dir, asc_filename)
        json_filename = os.path.join(output_dir, json_filename)

        np.savetxt(asc_filename,
                   np.flipud(self.grid),
                   comments = '',
                   header=header)
        #self.logger.info("Saved %s result %s to file %s.", self.res_type, self.rid, self.asc_filename)

        with open(json_filename, 'w') as fp:
            json.dump(self.description, fp, indent = 4, sort_keys = True)
            #self.logger.info("Saved %s description %s to file %s.", self.res_type, self.rid, self.json_filename)








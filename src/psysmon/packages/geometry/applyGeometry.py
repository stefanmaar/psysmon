## @file psysmon.packages.geometry.applyGeometry.py
# 

## @package psysmon.packages.geometry.applyGeometry
#
#
#
# @author: Stefan Mertl
# Created on Jul 24, 2011

## @page psysmon.packages.geometry.applyGeometry_page  Page for module psysmon.packages.geometry.applyGeometry
#
# @section sec_intro Introduction
#
#
# @section sec_license License
#     This file is part of Seismon.
#
#     If you use Seismon in any program or publication, please inform and
#     acknowledge its author Stefan Mertl (info@stefanmertl.com). 
# 
#     Seismon is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.


import psysmon.core.base

## The ApplyGeometry class.
# 
# This class creates the apply geometry collection node. 
# This node transfers the geometry information from the current inventory to the 
# data files imported into the traceheader database table.
# Each time, this node is executed, all the station_id, recorder_id and sensor_id 
# fields are reset.
#
# The apply geometry collection node is an uneditable node.
class ApplyGeometry(psysmon.core.base.CollectionNode):
    
        
    ## The edit method.
    #
    # The EditGeometry node is an uneditable node - ignore the edit method.
    def edit(self):
        pass
        
        
    ## The execute method.
    # 
    # Transfer the geometry of the current inventory to the traceheader 
    # database table.
    # This is done by executing two mysql queries. The first one resets the 
    # station_id, recorder_id and sensor_if fields, the second one assigns the 
    # new id's based on the geometry tables.
    #
    # @param self The object pointer.
    # @param psyProject The current pSysmon project.
    # @param prevNodeOutput The output of the previous collection node. 
    # Not used in this method.
    def execute(self, prevNodeOutput={}):
        stationTable = self.project.dbTableNames['geom_station']
        recorderTable = self.project.dbTableNames['geom_recorder']
        sensorTable = self.project.dbTableNames['geom_sensor']
        sensorTimeTable = self.project.dbTableNames['geom_sensor_time']
        traceheaderTable = self.project.dbTableNames['traceheader']
        
        
        # Reset all files in the traceheader table. Set the station_id, recorder_id  
        # and sensor_id to -1.
        query =  ("UPDATE %s "
                  "SET recorder_id=-1, station_id=-1, sensor_id=-1 ") % traceheaderTable
                  
        res = self.project.executeQuery(query)
        
        if not res['isError']:
            self.log("status", "Successfully reset the traceheader geometry.")
        else:
            self.log("error", res['msg'])  
            return 
        
        
        # Assign the station-, recorder- and sensor ids to the fileheaders in 
        # the traceheader table.
        query =  ("UPDATE %s as th, %s as rec, %s as sens, %s as sensTime, %s as stat "
                  "SET th.recorder_id = rec.id, th.station_id = stat.id, th.sensor_id = sens.id "
                  "WHERE "
                  "rec.serial LIKE th.recorder_serial "
                  "AND rec.id = sens.recorder_id "
                  "AND th.channel = sens.rec_channel_name "
                  "AND sensTime.sensor_id = sens.id "
                  "AND sensTime.stat_id = stat.id "
                  "AND (th.begin_time >= sensTime.start_time AND (th.begin_time <= sensTime.end_time OR sensTime.end_time IS NULL))") % (traceheaderTable, recorderTable, sensorTable, sensorTimeTable, stationTable) 
                  
        res = self.project.executeQuery(query)
        
        if not res['isError']:
            self.log("status", "Successfully updated the traceheader geometry.")
        else:
            self.log("error", res['msg'])  
            return 
        
        
        

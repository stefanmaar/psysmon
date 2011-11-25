# LICENSE
#
# This file is part of pSysmon.
#
# If you use pSysmon in any program or publication, please inform and
# acknowledge its author Stefan Mertl (info@stefanmertl.com).
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

from psysmon.core.packageNodes import CollectionNodeTemplate

name = "geometry"
version = "0.1.1"
author = "Stefan Mertl"
minPsysmonVersion = "0.0.1"
description = "The geometry package."
website = "http://www.stefanmertl.com"


def nodeFactory():
    nodeTemplates = []

    # Create a pSysmon collection node template and add it to the package.
    options = {}
    myNodeTemplate = CollectionNodeTemplate(
                                            name = 'edit geometry',
                                            mode = 'standalone',
                                            category = 'Geometry',
                                            tags = ['stable'],
                                            nodeClass = 'EditGeometry',
                                            options = options
                                            )
    nodeTemplates.append(myNodeTemplate) 
    
    # Create a pSysmon collection node template and add it to the package.
    options = {}
    myNodeTemplate = CollectionNodeTemplate(
                                            name = 'apply geometry',
                                            mode = 'uneditable',
                                            category = 'Geometry',
                                            tags = ['stable'],
                                            nodeClass = 'ApplyGeometry',
                                            options = options
                                            )
    nodeTemplates.append(myNodeTemplate)

    return nodeTemplates



def databaseFactory():
    queries=[]

    # The geom_recorder table.
    myQuery = ("CREATE TABLE IF NOT EXISTS </PREFIX/>_geom_recorder "
              "("
              "id int(10) NOT NULL auto_increment,"
              "serial varchar(45) NOT NULL default '',"
              "type varchar(255) NOT NULL default '',"
              "PRIMARY KEY  (id),"
              "UNIQUE (serial, type)"
              ") "
              "ENGINE=MyISAM "
              "DEFAULT CHARSET=latin1 "
              "COLLATE latin1_general_cs")
    queries.append(myQuery)

    # The geom_sensor table.
    myQuery = ("CREATE TABLE  </PREFIX/>_geom_sensor "
               "("
               "id int(10) NOT NULL auto_increment,"
               "recorder_id int(10) NOT NULL,"
               "serial varchar(45) NOT NULL default '',"
               "type varchar(255) NOT NULL default '',"
               "rec_channel_name varchar(10) NOT NULL default '',"
               "channel_name varchar(10) NOT NULL default '',"
               "PRIMARY KEY  (id),"
               "UNIQUE (recorder_id, serial, type, rec_channel_name, channel_name)"
               ") " 
               "ENGINE=MyISAM "
               "DEFAULT CHARSET=latin1 COLLATE "
               "latin1_general_cs")
    queries.append(myQuery) 
    
    # The geom_paz table.
    myQuery = ("CREATE TABLE  </PREFIX/>_geom_sensor_param "
             "("
             "id int(10) NOT NULL auto_increment,"
             "sensor_id int(10) NOT NULL default '-1',"
             "start_time double default NULL,"
             "end_time double default NULL,"
             "normalization_factor float default NULL,"
             "normalization_frequency float default NULL,"
             "type varchar(150) default NULL,"
             "tf_units varchar(20) default NULL,"
             "gain float default NULL,"
             "sensitivity double default NULL,"
             "sensitivity_units varchar(15) default NULL,"
             "bitweight double default NULL,"
             "bitweight_units varchar(15) default NULL,"
             "PRIMARY KEY (id),"
             "UNIQUE(sensor_id, start_time, end_time)"
             ") " 
             "ENGINE=MyISAM "
             "DEFAULT CHARSET=latin1 COLLATE "
             "latin1_general_cs")
    queries.append(myQuery) 
    
    # The geom_paz_pz table.
    myQuery = ("CREATE TABLE  </PREFIX/>_geom_tf_pz "
             "("
             "param_id int(10) NOT NULL,"
             "type int(1) unsigned NOT NULL default 1,"
             "complex_real float NOT NULL,"
             "complex_imag float NOT NULL"
             ") " 
             "ENGINE=MyISAM "
             "DEFAULT CHARSET=latin1 COLLATE "
             "latin1_general_cs")
    queries.append(myQuery) 
    
    # The geom_network table.
    myQuery = ("CREATE TABLE  </PREFIX/>_geom_network "
             "("
             "name varchar(10) NOT NULL,"
             "description varchar(100) default NULL,"
             "type varchar(255) default NULL,"
             "PRIMARY KEY (name)"
             ") "
             "ENGINE=MyISAM "
             "DEFAULT CHARSET=latin1 "
             "COLLATE latin1_general_cs")
    queries.append(myQuery) 
    
    # The geom_station table.
    myQuery = ("CREATE TABLE  </PREFIX/>_geom_station "
             "("
             "id int(10) NOT NULL auto_increment,"
             "net_name varchar(10) default NULL,"
             "name varchar(10) NOT NULL default '',"
             "location varchar(3) NOT NULL default '00',"
             "X double NOT NULL default 0,"
             "Y double NOT NULL default 0,"
             "Z float NOT NULL default 0,"
             "coord_system varchar(50) default NULL,"
             "description varchar(255) default NULL,"
             "PRIMARY KEY  (id),"
             "UNIQUE (net_name, name, location)"
             ") "
             "ENGINE=MyISAM "
             "DEFAULT CHARSET=latin1 "
             "COLLATE latin1_general_cs")
    queries.append(myQuery) 
    
    # The geom_sensor_time table.
    myQuery = ("CREATE TABLE  </PREFIX/>_geom_sensor_time "
             "("
             "stat_id int(10) NOT NULL,"
             "sensor_id int(10) NOT NULL,"
             "start_time double signed NOT NULL,"
             "end_time double default NULL,"
             "PRIMARY KEY  (stat_id, sensor_id, start_time)"
             ") "
             "ENGINE=MyISAM "
             "DEFAULT CHARSET=latin1 "
             "COLLATE latin1_general_cs")
    queries.append(myQuery) 
    
    return queries

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

name = "obspyImportWaveform"
version = "0.1.1"
author = "Stefan Mertl"
minPsysmonVersion = "0.0.1"
description = "The obspyImportWaveform packages"
website = "http://www.stefanmertl.com"


def nodeFactory():
    from importWaveform import ImportWaveform

    nodeTemplates = []

    # Create a pSysmon collection node template and add it to the package.
    options = {}
    options['inputFiles'] = []                     # The files to import.
    options['lastDir'] = ""                        # The last used directory.
    myNodeTemplate = ImportWaveform(name = 'import waveform',
                                    mode = 'editable',
                                    category = 'Data Import',
                                    tags = ['stable'],
                                    options = options
                                    )
    nodeTemplates.append(myNodeTemplate)

    return nodeTemplates



def databaseFactory():
    queries = []

    # Create the traceheader database table.
    query = ("CREATE TABLE IF NOT EXISTS </PREFIX/>_traceheader "
             "("
             "id int(10) NOT NULL auto_increment,"
             "file_type varchar(10) NOT NULL default '',"
             "wf_id INT(10) NOT NULL default -1,"
             "filename varchar(255) NOT NULL,"
             "orig_path text NOT NULL,"
             "network varchar(3) NOT NULL default '',"
             "recorder_serial varchar(45) NOT NULL default '',"
             "channel varchar(45) NOT NULL default '',"
             "location varchar(3) NOT NULL default '',"
             "sps int(10) unsigned NOT NULL default 0,"
             "numsamp int(10) unsigned NOT NULL default 0,"
             "begin_date VARCHAR(26) NOT NULL default '0000-00-00 00:00:00',"
             "begin_time double unsigned NOT NULL default 0,"
             "station_id int(10) NOT NULL default -1,"
             "recorder_id int(10) NOT NULL default -1,"
             "sensor_id int(10) NOT NULL default -1,"
             "PRIMARY KEY  (id)"
             ")"
             "ENGINE=MyISAM "
             "DEFAULT CHARSET=latin1 "
             "COLLATE latin1_general_cs")
    queries.append(query)

    # Create the waveformdir database table.
    query = ("CREATE TABLE IF NOT EXISTS </PREFIX/>_waveformDir "
            "("
            "id int(10) unsigned NOT NULL auto_increment,"
            "directory varchar(255) NOT NULL,"
            "description varchar(255) NOT NULL,"
            "PRIMARY KEY (id),"
            "UNIQUE KEY dirIndex (directory)"
            ")"
            "ENGINE=MyISAM "
            "DEFAULT CHARSET=latin1 "
            "COLLATE latin1_general_cs")
    queries.append(query)

    # Create the waveformdiralias database table.
    query = ("CREATE TABLE IF NOT EXISTS </PREFIX/>_waveformDirAlias "
            "("
            "wf_id int(10) unsigned NOT NULL,"
            "user varchar(45) NOT NULL,"
            "alias varchar(255) NOT NULL,"
            "PRIMARY KEY  (wf_id, user)"
            ")"
            "ENGINE=MyISAM "
            "DEFAULT CHARSET=latin1 "
            "COLLATE latin1_general_cs")
    queries.append(query)

    return queries

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

from psysmon.core.base import CollectionNodeTemplate

name = "example"
version = "0.1.1"
author = "Stefan Mertl"
minPsysmonVersion = "0.0.1"
description = "The example packages"
website = "http://www.stefanmertl.com"


def databaseFactory():
    queries = []
    myQuery = """CREATE TABLE IF NOT EXISTS </PREFIX/>_exampleTable 
            (
            id INT(10) NOT NULL AUTO_INCREMENT,
            value VARCHAR(20) NOT NULL,
            PRIMARY KEY  (id)
            )
            ENGINE=MyISAM 
            DEFAULT CHARSET=latin1 
            COLLATE latin1_general_cs"""
    queries.append(myQuery)

    return queries



def nodeFactory():
    nodeTemplates = []

    myTemplate = CollectionNodeTemplate(
                                        name = 'example node',
                                        mode = 'editable',
                                        category = 'Example',
                                        tags = ['stable', 'example'],
                                        nodeClass = 'exampleNode',
                                        options = None,
                                        docEntryPoint = 'exampleNode.html'
                                       )
    nodeTemplates.append(myTemplate)

    return nodeTemplates




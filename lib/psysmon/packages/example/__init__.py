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

name = "example"                                # The package name.
version = "0.1.1"                               # The package version.
author = "Stefan Mertl"                         # The package author.
minPsysmonVersion = "0.0.1"                     # The minimum pSysmon version required.
description = "The example packages"            # The package description.
website = "http://www.stefanmertl.com"          # The package website.


def databaseFactory(base):
    from sqlalchemy import Column
    from sqlalchemy import Integer, String

    tables = []

    # Define the sqlAlchemy database table mapper class.
    class ExampleTable(base):
        __tablename__ = 'exampleTable'
        __table_args__ = {'mysql_engine': 'InnoDB'}

        id = Column(Integer, primary_key=True, autoincrement=True)
        value = Column(String(20))


    exampleTable = ExampleTable
    tables.append(exampleTable)
    return tables



def nodeFactory():
    from exampleNode import ExampleNode

    nodeTemplates = []

    myTemplate = ExampleNode(name = 'example node',
                             mode = 'editable',
                             category = 'Example',
                             tags = ['stable', 'example'],
                             options = None,
                             docEntryPoint = 'exampleNode.html',
                             requires = None, 
                             provides = ('exp2InputData', )
                           )
    nodeTemplates.append(myTemplate)

    return nodeTemplates






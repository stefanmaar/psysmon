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

name = "tracedisplay"
version = "0.1.1"
author = "Stefan Mertl"
minPsysmonVersion = "0.0.1"
description = "The tracedisplay package."
website = "http://www.stefanmertl.com"


def nodeFactory():
    from tracedisplay import TraceDisplay
    nodeTemplates = []

   # Create a pSysmon collection node template and add it to the package.
    options = {}
    #options['datetime'] = []                   # The begin of the selected timespan.
    myNodeTemplate = TraceDisplay(name = 'tracedisplay',
                                  mode = 'editable',
                                  category = 'Display',
                                  tags = ['development'],
                                  nodeClass = 'TraceDisplay',
                                  options = options
                                  )

    nodeTemplates.append(myNodeTemplate)

    return nodeTemplates

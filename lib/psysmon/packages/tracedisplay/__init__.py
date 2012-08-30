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

    myNodeTemplate = TraceDisplay(name = 'tracedisplay',
                                  mode = 'editable',
                                  category = 'Display',
                                  tags = ['development'],
                                  options = options
                                  )

    nodeTemplates.append(myNodeTemplate)

    return nodeTemplates


def pluginFactory():
    ''' Provide some plugins.
    '''
    from plugins import SelectStation, SelectChannel, Zoom, SeismogramPlotter, DemoPlotter

    pluginTemplates = []

    myPluginTemplate = SelectStation(name = 'select station',
                                     category = 'view',
                                     tags = ['station', 'view', 'select'],
                                     nodeClass = 'TraceDisplay'
                                     )
    pluginTemplates.append(myPluginTemplate)



    myPluginTemplate = SelectChannel(name = 'select channel',
                                     category = 'view',
                                     tags = ['channel', 'view', 'select'],
                                     nodeClass = 'TraceDisplay'
                                     )
    pluginTemplates.append(myPluginTemplate)



    myPluginTemplate = SeismogramPlotter(name = 'plot seismogram',
                            category = 'views',
                            tags = None,
                            nodeClass = 'TraceDisplay'
                            )
    pluginTemplates.append(myPluginTemplate)


    myPluginTemplate = DemoPlotter(name = 'demo plotter',
                            category = 'views',
                            tags = None,
                            nodeClass = 'TraceDisplay'
                            )
    pluginTemplates.append(myPluginTemplate)


    myPluginTemplate = Zoom(name = 'zoom',
                            category = 'interactive',
                            tags = None,
                            nodeClass = 'TraceDisplay'
                            )
    pluginTemplates.append(myPluginTemplate)

    return pluginTemplates



def processingNodeFactory():
    ''' Provide some processing nodes.
    '''
    from processingNodes import Detrend

    procNodeTemplates = []

    options = {}

    myProcNodeTemplate = Detrend(name = 'detrend',
                                 mode = 'uneditable',
                                 category = 'test',
                                 tags = ['remove', 'mean'],
                                 options = options
                                 )

    procNodeTemplates.append(myProcNodeTemplate)

    return procNodeTemplates

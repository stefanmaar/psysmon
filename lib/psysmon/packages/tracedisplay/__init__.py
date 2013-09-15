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

name = "tracedisplay"
version = "0.1.1"
author = "Stefan Mertl"
minPsysmonVersion = "0.0.1"
description = "The tracedisplay package."
website = "http://www.stefanmertl.com"


def nodeFactory():
    from tracedisplay import TraceDisplay

    nodeTemplates = [TraceDisplay, ]

    return nodeTemplates


def pluginFactory():
    ''' Provide some plugins.
    '''
    from plugins import SelectStation
    from plugins import SelectChannel 
    from plugins import Zoom
    from plugins import SeismogramPlotter
    from plugins import DemoPlotter
    from plugins import ProcessingStack
    from plugins import SpectrogramPlotter
    from plugins import SonificationPyoControl
    from plugins import SonificationPlayLoop

    pluginTemplates = [SelectStation,
                       SelectChannel,
                       Zoom,
                       ProcessingStack,
                       SeismogramPlotter,
                       DemoPlotter,
                       SpectrogramPlotter,
                       SonificationPyoControl,
                       SonificationPlayLoop]

    return pluginTemplates



def processingNodeFactory():
    ''' Provide some processing nodes.
    '''
    from processingNodes import Detrend
    from processingNodes import FilterBandPass
    from processingNodes import FilterLowPass
    from processingNodes import FilterHighPass

    procNodeTemplates = [Detrend,
                         FilterBandPass,
                         FilterLowPass,
                         FilterHighPass]

    return procNodeTemplates


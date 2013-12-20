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

import psysmon.core.plugins

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
    plugin_modules = ['plugins',]
    plugin_templates = psysmon.core.plugins.scan_module_for_plugins(__name__, plugin_modules)
    print plugin_templates
    #from plugins import SelectStation
    #from plugins import SelectChannel
    #from plugins import Zoom
    #from plugins import SeismogramPlotter
    #from plugins import DemoPlotter
    #from plugins import ProcessingStack
    #from plugins import SpectrogramPlotter
    #from plugins import SonificationPyoControl
    #from plugins import SonificationPlayPhaseVocoder
    #from plugins import SonificationPlayParameterMapping
    #from plugins import SonificationPlayTimeCompress
    #from plugins import SonificationLooperTimeCompress
    #from plugins import AutoPlay
    #from plugins import RealTimeAutoPlay

    #pluginTemplates = [SelectStation,
    #                   SelectChannel,
    #                   Zoom,
    #                   ProcessingStack,
    #                   SeismogramPlotter,
    #                   DemoPlotter,
    #                   SpectrogramPlotter,
    #                   SonificationPyoControl,
    #                   SonificationPlayPhaseVocoder,
    #                   SonificationPlayParameterMapping,
    #                   SonificationPlayTimeCompress,
    #                   SonificationLooperTimeCompress,
    #                   AutoPlay,
    #                   RealTimeAutoPlay]

    #print pluginTemplates
    return plugin_templates



def processingNodeFactory():
    ''' Provide some processing nodes.
    '''
    from processingNodes import Detrend
    from processingNodes import FilterBandPass
    from processingNodes import FilterLowPass
    from processingNodes import FilterHighPass
    from processingNodes import ConvertToSensorUnits
    from processingNodes import ScaleLog10

    procNodeTemplates = [Detrend,
                         FilterBandPass,
                         FilterLowPass,
                         FilterHighPass,
                         ConvertToSensorUnits,
                         ScaleLog10]

    return procNodeTemplates


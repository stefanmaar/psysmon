# -*- coding: utf-8 -*-
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
The projectserver module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)

This module contains the classes to run the psysmon project server system
'''

import logging

import Pyro4 as pyro
pyro.config.REQUIRE_EXPOSE = True

class ProjectServer(object):
    ''' Provide remote access to project data.

    '''

    def __init__(self):
        ''' The instance initialization.
        '''
        # The system logger used for debugging and system wide error logging.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The data managed by the server.
        self.data = {}


    @pyro.expose
    def get_data(self, uri):
        ''' Get the dataserver of a current project.
        '''
        if uri in self.data.keys():
            return self.data[uri]

    @pyro.expose
    def list_data(self):
        ''' Return a list of uri of the available data.
        '''
        return self.data.keys()


    @pyro.expose
    def register_data(self, uri, data):
        ''' Register data to be exported by the server.
        '''
        if uri not in self.data.keys():
            self.data[uri] = data
        else:
            raise ValueError('The given uri %s already exists in the data dictionary.', uri)



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
import re

import Pyro4 as pyro
pyro.config.REQUIRE_EXPOSE = True
pyro.config.SERIALIZERS_ACCEPTED = set(('pickle', ))
pyro.config.SERIALIZER = 'pickle'

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
    def get_data(self, uri = None, exact = True):
        ''' Get the dataserver of a current project.
        '''
        if uri is None:
            return self.data
        elif exact is True and uri in self.data.iterkeys():
            return self.data[uri]
        elif exact is False:
            keys_to_return = [x for x in self.data.iterkeys() if re.search(uri, x) is not None]
            return [self.data[x] for x in keys_to_return]
        else:
            return None

    @pyro.expose
    def list_data(self):
        ''' Return a list of uri of the available data.
        '''
        return self.data.iterkeys()


    @pyro.expose
    def register_data(self, uri, data):
        ''' Register data to be exported by the server.
        '''
        # TODO: Add some checks for the data which is registered.
        self.data[uri] = data


    @pyro.expose
    def unregister_data(self, uri = None, recursive = False):
        ''' Remove selected data from the the server.
        '''
        if uri is None:
            data_to_remove = self.data.iterkeys()
        elif recursive is True:
            data_to_remove = [x for x in self.data.iterkeys() if x.startswith(uri)]
        else:
            data_to_remove = [uri,]

        for cur_key in data_to_remove:
            if cur_key in self.data.iterkeys():
                self.data.pop(cur_key)





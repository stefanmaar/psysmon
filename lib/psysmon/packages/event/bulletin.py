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
Handle earthquake bulletins.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)

'''
import psysmon
import logging


class ImsParser(object):
    ''' Parse bulletins in IMS format.
    '''


    def __init__(self):
        # the logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        logger_name = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(logger_name)

        # The bulletin file handle.
        self.b_file = None

        # The bulletin title.
        self.bulletin_title = None

        self.parser = {}
        self.parser['ims1.0:short'] = self.parse_ims1_0_short


    def parse(self, filename):
        catalogs = []
        bulletin_format = None

        try:
            self.b_file = open(filename, 'r')
            for cur_line in self.b_file:
                cur_line = cur_line.rstrip()
                if bulletin_format is None:
                    # Waiting for the data_type line.
                    if cur_line.lower().startswith('data_type'):
                        tmp = cur_line.split(' ')
                        if tmp[1].lower() == 'bulletin':
                            bulletin_format = tmp[2].lower()
                            self.parser[bulletin_format]()

            self.b_file.close()
        finally:
            self.b_file.close()

        return catalogs


    def parse_ims1_0_short(self):
        ''' Parse an IMS1.0:short bulletin.
        '''

        for cur_line in self.b_file:
            cur_line = cur_line.rstrip()
            if cur_line.startswith(' ') or cur_line.startswith('#'):
                # Lines starting with an blank are comments or header lines.
                # Lines starting with a hashtag are comments.
                continue

            if cur_line.lower().startswith('event'):
                # Parse the event title block.
                self.logger.debug('Parsing the event title block.')
            elif cur_line.lstrip().lower().startswith('date'):
                # Parse the origin block.
                self.logger.debug('Parsing the origin block.')
            elif cur_line.lstrip().lower().startswith('magnitude'):
                # Parse the magnitude sub-block.
                self.logger.debug('Parsing the magnitude sub-block.')
            elif cur_line.lower().startswith('sta'):
                # Parse the phase block.
                self.logger.debug('Parsing the phase block.')
            elif self.bulletin_title is None:
                # Read the bulletin title string.
                self.logger.debug('Reading the bulletin title.')
                self.bulletin_title = cur_line





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

import logging

import wx

import psysmon


class psyContextMenu(wx.Menu):

        def __init__(self, cmData):
            wx.Menu.__init__(self)

            # The logger.
            self.logger = psysmon.get_logger(self)

            for cmLabel, cmHandler in cmData:
                if cmLabel.lower() == "separator":
                    self.AppendSeparator()
                else:
                    if (isinstance(cmHandler, list) or
                            isinstance(cmHandler, tuple)):
                        # This is a submenu.
                        submenu = wx.Menu()
                        for subLabel, subHandler in cmHandler:
                            item = submenu.Append(-1, subLabel)
                            submenu.Bind(wx.EVT_MENU, subHandler, item)
                        self.AppendMenu(-1, cmLabel, submenu)
                    else:
                        item = self.Append(-1, cmLabel)
                        self.Bind(wx.EVT_MENU, cmHandler, item)

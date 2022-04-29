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

import wx
import wx.lib.mixins.inspection as wit


class PsysmonApp(wx.App, wit.InspectionMixin):
    ''' The pSysmon wxPython App class.
    '''
    #def __init__(self, redirect=False, filename=None,
    #             useBestVisual=False, clearSigInt=True):
    #    wx.App.__init__(self, redirect, filename, useBestVisual,
    #                    clearSigInt)

    def OnInit(self):
        # The widget inspection tool can be called using CTRL+ALT+i
        self.Init()
        return True

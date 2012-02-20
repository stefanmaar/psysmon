#!/usr/bin/env python

# License
#     This file is part of Seismon.
#
#     If you use Seismon in any program or publication, please inform and
#     acknowledge its author Stefan Mertl (info@stefanmertl.com). 
# 
#     Seismon is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
The pSysmon main program.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)


Examples
-----------

**Starting from the command line**

    To start pSysmon from the command line, change into the psysmon directory 
    where the file pSysmon.py is located and type the following command in your 
    linux shell or your window command prompt:

    >>> pSysmon.py

    or

    >>> python pSysmon.py

**Starting from a python shell**

    To start psysmon from a python shell (e.g. ipython) use the following 
    commands:

        >>> import psysmon.pSysmon as psysmon
        >>> psysmon.run()
'''

import psysmon
import psysmon.core.gui as psygui
import psysmon.core.base as psybase
import os
import logging


def run():
    '''
    Start the pSysmon main program.

    Basic Usage
    -----------

    **Starting from the command line**

        To start pSysmon from the command line, change into the psysmon directory 
        where the file pSysmon.py is located and type the following command in your 
        linux shell or your window command prompt:
        python pSysmon.py:

    **Starting from a python shell**

        To start psysmon from a python shell (e.g. ipython) use the following 
        commands:

        >>> import psysmon.pSysmon as psysmon
        >>> psysmon.run
    '''

    logger = logging.getLogger('psysmon')
    logger.setLevel(psysmon.logConfig['level'])
    logger.addHandler(psysmon.getLoggerHandler())

    psyBaseDir = os.path.abspath(__file__)
    psyBaseDir = os.path.dirname(psyBaseDir)

    # Initialize the pSysmon base object.
    psyBase = psybase.Base(psyBaseDir)

    # Scan for available pSysmon packages.
    #psyBase.initialize()

    # Create the app and run the GUI.
    app =psygui.PSysmonApp()
    pSysmon = psygui.PSysmonGui(psyBase, None)
    pSysmon.Show()
    app.MainLoop()


if __name__ == '__main__':
    run()





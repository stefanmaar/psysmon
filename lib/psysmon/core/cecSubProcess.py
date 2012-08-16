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
'''

#from twisted.internet import wxreactor
#wxreactor.install()

import psysmon
from psysmon.core.waveclient import PsysmonDbWaveClient, EarthwormWaveClient
import psysmon.core.base as psybase
#from twisted.internet import reactor
import sys
import shelve
import wx
import logging
import os

class ExecutionFrame(wx.Frame):

    def __init__(self, collection):
        wx.Frame.__init__(self, None, wx.ID_ANY, 'Execution frame')
        #wx.CallAfter(collection.execute, 'halloooo')





if __name__ == "__main__":

    # The process name and the temp. file are passes as arguments. 
    filename = sys.argv[1]
    procName = sys.argv[2]

    db = shelve.open(filename)
    project = db['project']
    collection = db['collection']
    packages = db['packages']
    waveclients = db['waveclient']
    db.close()

    #logfileName = os.path.join(tempfile.gettempdir(), procName + '.log')
    logfileName = os.path.join(project.tmpDir, procName + '.log')

    logger = logging.getLogger('psysmon')
    logger.setLevel(psysmon.logConfig['level'])
    logger.addHandler(psysmon.getLoggerFileHandler(logfileName))
    logger.addHandler(psysmon.getLoggerHandler())

    logger.info('Starting process %s', procName)
    logger.info('Loading data from file %s', filename)

    logger.info('Project: %s', project)
    logger.info('Collection: %s', collection)

    logger.info('Executing collection %s of project %s.', collection, project)

    psyBaseDir = os.path.abspath(psysmon.__file__)
    psyBaseDir = os.path.dirname(psyBaseDir)
    psyBase = psybase.Base(psyBaseDir)

    # Reinitialize the project.
    project.connect2Db(project.activeUser.pwd)
    project.loadDatabaseStructure(packages)

    for curName, curMode in waveclients:
        if curMode == 'psysmonDb':
            waveclient = PsysmonDbWaveClient(curName, project)
        elif curMode == 'earthworm':
            waveclient = EarthwormWaveClient(curName)
        else:
            waveclient = None

        if waveclient != None:
            project.addWaveClient(waveclient)

    collection.setNodeProject(project) 
    collection.createNodeLoggers()

    project.psyBase = psyBase

    logger.debug('psyBase: %s', project.psyBase)

    collection.execute()

    logger.info('Finished the execution. Cleaning up....')
    logger.info('Deleting data file %s.', filename)
    os.remove(filename)

    #reactor.registerWxApp(app)

    # Create a CecClient and connect it to the project's CecServer.
    #myClient = CecClient('localhost', port)
    #myClient.connect()

    # Start the twisted eventloop.
    #reactor.run()






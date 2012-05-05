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

import psysmon.core.gui as psygui
from psysmon.core.collectionExecutionControl import CecClient
from psysmon.core.waveclient import PsysmonDbWaveClient
from twisted.internet import reactor
import sys
import shelve
import wx

class ExecutionFrame(wx.Frame):

    def __init__(self, collection):
        wx.Frame.__init__(self, None, wx.ID_ANY, 'Execution frame')
        #wx.CallAfter(collection.execute, 'halloooo')

    



if __name__ == "__main__":

    # The port number is passed as the first commandline argument.
    filename = sys.argv[1]
    print "Filename: %s" % filename

    db = shelve.open(filename)
    project = db['project']
    collection = db['collection']
    packages = db['packages']
    print "Project: %s" % project
    print "collection: %s" % collection

    # Reinitialize the project.
    project.connect2Db(project.activeUser.pwd)
    project.loadDatabaseStructure(packages)
    waveclient = PsysmonDbWaveClient('main client', project)
    project.addWaveClient(waveclient)
    collection.setNodeProject(project) 
     
    collection.execute('halloooo')

    print "Finished the execution."
    #frame = ExecutionFrame(collection)
    #frame.Show(True)
    
    #app.MainLoop()
    
    #reactor.registerWxApp(app)

    # Create a CecClient and connect it to the project's CecServer.
    #myClient = CecClient('localhost', port)
    #myClient.connect()

    # Start the twisted eventloop.
    #reactor.run()






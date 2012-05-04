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

from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver
import pickle
from psysmon.core.waveclient import PsysmonDbWaveClient

class CecServer():

    def __init__(self, port, project, packages):
        #factory = protocol.ServerFactory()
        #factory.protocol = Echo
        self.factory = CecServerFactory(project, packages)
        port = reactor.listenTCP(port, self.factory)
        self.port = port.getHost().port

    def addCollection(self, collection):
        self.factory.addCollection(collection)




class CecClient():

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.factory = CecClientFactory()


    def connect(self):
        tmp = reactor.connectTCP(self.host, self.port, self.factory)
        print tmp

    def requestCollection(self):
        if self.factory.protocolInstance:
            self.factory.protocolInstance.requestCollection()
        else:
            print "protocolInstance not ready."




class CecServerProtocol(LineReceiver):
    """This is just about the simplest possible protocol"""

    def connectionMade(self):
        print "SERVER: got a connection from client."


    def lineReceived(self, data):
        "As soon as any data is received, write it back."
        try:
            obj = pickle.loads(data)
            print "SERVER: Client sent: %s" % obj 
        except:
            print "SERVER: Client sent: %s" % data
        

        #returnData = "Collection to be executed."
        #self.sendLine(returnData)

        print self.factory.collections
        if self.factory.collections:
            data2Send = {}
            data2Send['project'] = self.factory.project
            #data2Send['project'] = None
            #data2Send['collection'] = self.factory.collections.pop()
            print "SERVER: Sending data %s" % data2Send
            tmp = pickle.dumps(data2Send)
            self.sendLine(tmp)
            print "SERVER: Sent data %s" % data2Send
        else:
            self.sendLine("No Collection available.")


class CecServerFactory(protocol.ServerFactory):
    protocol = CecServerProtocol

    def __init__(self, project, packages):
        self.project = project
        self.packages = packages
        self.collections = []


    def addCollection(self, collection):

        self.collections.append(collection)



class CecClientProtocol(LineReceiver):
    """Once connected, send a message, then print the result."""

    def connectionMade(self):
        self.factory.clientReady(self)
        self.requestCollection()

    def lineReceived(self, data):
        """ As soon as any data is received, write it back. """
       
        collection = None 
        
        print "CLIENT: Trying to unpickle the data."
            #serverData = pickle.loads(data)
            #project = serverData['project']
            #collection = serverData['collection']
            #print "CLIENT: SERVER sent project: %s" % project
            #print "CLIENT: SERVER sent collection: %s" % collection
        #print "CLIENT: SERVER sent data: %s" % data
        
        if collection:
            self.executeCollection(collection)
        else:
            print "CLIENT: No collection to execute"
        #self.transport.loseConnection()

    def connectionLost(self, reason):
        print "CLIENT: lost connection."


    def requestCollection(self):
        test = {'type': 'RQST', 'msg': 'Requesting collection from server.'}
        self.sendLine(pickle.dumps(test))


    def executeCollection(self, collection):
        print "Executing collection %s" % collection

        # Create the project links loosed due to pickling.
        # The project database waveclient.
        waveclient = PsysmonDbWaveClient('main client', collection.project)
        self.psyBase.project.addWaveClient(waveclient)

        collection.execute(self)




class CecClientFactory(protocol.ClientFactory):
    protocol = CecClientProtocol

    def startFactory(self):
        self.protocolInstance = None

    def clientReady(self, protocol):
        self.protocolInstance = protocol

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed - goodbye!"
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print "Connection lost - goodbye!"
        reactor.stop()




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


class CecServer():

    def __init__(self, port):
        factory = protocol.ServerFactory()
        factory.protocol = Echo
        port = reactor.listenTCP(port, factory)
        self.port = port.getHost().port



class CecClient():

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.protocol = EchoFactory()


    def connect(self):
        reactor.connectTCP(self.host, self.port, self.protocol)



class Echo(LineReceiver):
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
        

        returnData = "Collection to be executed."
        self.sendLine(returnData)



class EchoClient(LineReceiver):
    """Once connected, send a message, then print the result."""

    def connectionMade(self):
        test = {'type': 'RQST', 'msg': 'Requesting collection data'}
        self.sendLine(pickle.dumps(test))

    def lineReceived(self, data):
        """ As soon as any data is received, write it back. """
        print "CLIENT: Server said:", data
        self.transport.loseConnection()

    def connectionLost(self, reason):
        print "CLIENT: lost connection."



class EchoFactory(protocol.ClientFactory):
    protocol = EchoClient

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed - goodbye!"
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print "Connection lost - goodbye!"
        reactor.stop()



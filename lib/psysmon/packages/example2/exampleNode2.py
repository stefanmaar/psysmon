# LICENSE
#
# This file is part of pSysmon.
#
# If you use pSysmon in any program or publication, please inform and
# acknowledge its author Stefan Mertl (info@stefanmertl.com).
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

from psysmon.core.packageNodes import CollectionNode

class ExampleNode2(CollectionNode):
    '''
    An example node.

    This node demonstrates the usage of pSysmon collection nodes.
    The node inherints from the class :class:`~psysmon.core.base.CollectionNode`.

    The creator of the node has to define the edit and the execute method.

    The inherited log method can be used to display messages in the pSysmon 
    log area.

    In the execute method, accessing output of the previous node in the collection 
    is demonstrated. The output has been set by the example node.
    '''

    def edit(self):
        msg = "Editing the node %s." % self.name


    def execute(self, prevModuleOutput={}):
        self.logger.debug("Executing the node %s." % self.name)

        requiredData = self.requireData(('exp2InputData', ))

        print "Unpickled Data: %s" % requiredData['exp2InputData']



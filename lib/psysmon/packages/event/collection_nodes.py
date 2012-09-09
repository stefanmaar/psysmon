

from psysmon.core.packageNodes import CollectionNode
from psysmon.packages.event.core import PsysmonEvent


class EventExample(CollectionNode):
    '''
    An example node.

    This node demonstrates the usage of pSysmon collection nodes.
    The node inherints from the class :class:`~psysmon.core.base.CollectionNode`.

    The creator of the node has to define the edit and the execute method.

    The inherited log method can be used to display messages in the pSysmon 
    log area.
    '''

    def edit(self):
        msg = "Editing the node %s." % self.name

    def execute(self, prevModuleOutput={}):

        myEvent = PsysmonEvent(resource_id = 'smi:stefan/test')
        print myEvent




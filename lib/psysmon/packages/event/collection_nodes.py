

from psysmon.core.packageNodes import CollectionNode
from psysmon.packages.event.core import Event


class EventExample(CollectionNode):
    '''
    An example node.

    This node demonstrates the usage of pSysmon collection nodes.
    The node inherints from the class :class:`~psysmon.core.base.CollectionNode`.

    The creator of the node has to define the edit and the execute method.

    The inherited log method can be used to display messages in the pSysmon 
    log area.
    '''
    name = 'event example node'
    mode = 'uneditable'
    category = 'Example'
    tags = ['stable', 'example']

    def __init__(self):
        CollectionNode.__init__(self)
        self.options = {}

    def edit(self):
        msg = "Editing the node %s." % self.name

    def execute(self, prevModuleOutput={}):

        myEvent = Event(resource_id = 'smi:stefan/test')
        print myEvent




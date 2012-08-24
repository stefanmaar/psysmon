

from psysmon.core.packageNodes import CollectionNode
import time
import wx
import psysmon.core.gui as psygui


class ExampleNode(CollectionNode):
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

        #myTable = self.project.dbTables['exampleTable']
        #session = self.project.dbSession
        #data2Insert = {'id': None, 'value': 200}
        #addValue = myTable(**data2Insert)
        #session.add(addValue)
        #session.commit()

        #self.project.waveserver.getWaveform()
        #self.logger.debug("Executing the node.")


        self.provideData(name = 'test_data', 
                         data = 'Hallihallo', 
                         description = 'Ein Test'
                         )

        self.provideData(name = 'my_data', 
                         data = 'Stefan', 
                         description = 'Ein weiterer Test.'
                         )

        #for k in range(5):
        #    msg = "value: " + str(k)
        #    self.log('status', msg)
        #    time.sleep(1)




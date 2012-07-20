'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import psysmon
import logging
from psysmon.core.base import Base
from psysmon.core.waveclient import PsysmonDbWaveClient,EarthwormWaveClient
import psysmon.core.gui as psygui
import os
import copy


class TracedisplayTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """
    def setUp(self):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel(psysmon.logConfig['level'])
        logger.addHandler(psysmon.getLoggerHandler())

        # Get the pSysmon base directory.
        psyBaseDir = '/home/stefan/01_gtd/04_aktuelleProjekte/pSysmon/01_src/psysmon/lib/psysmon/'
        psyBaseDir = os.path.dirname(psyBaseDir)

        # Initialize the pSysmon base object.
        psyBase = Base(psyBaseDir)
        #psyBase.scan4Package()

        # Load the pSysmon test project.
        path = "/home/stefan/01_gtd/04_aktuelleProjekte/pSysmon/03_pSysmonProjects/test/test.ppr"
        psyBase.loadPsysmonProject(path)

        # Quest for the user and the database password.
        psyBase.project.setActiveUser('stefan','')

        # Load the database structure of the project packages.
        psyBase.project.loadDatabaseStructure(psyBase.packageMgr.packages)

        # Create the project waveclient.
        waveclient = PsysmonDbWaveClient('main client', psyBase.project)
        psyBase.project.addWaveClient(waveclient)
        waveclient = EarthwormWaveClient('earthworm')
        psyBase.project.addWaveClient(waveclient)
        self.app =psygui.PSysmonApp()

        nodeTemplate = psyBase.packageMgr.getCollectionNodeTemplate('tracedisplay')
        self.node = copy.deepcopy(nodeTemplate)
        self.node.project = psyBase.project

        # Create the node logger. This is usually done in the collection.
        loggerName = __name__ + "." + self.node.__class__.__name__
        self.node.logger = logging.getLogger(loggerName)


        #self.dlg = EditGeometryDlg(node, psyBase.project)
        #self.dlg.Show()


    def tearDown(self):
        print "\n\nEs war sehr schoen - auf Wiederseh'n.\n"

    def testDlg(self):
        self.node.execute()
        self.app.MainLoop()


#def suite():
#    suite = unittest.makeSuite(EditGeometryDlgTestCase, 'test')
#    return suite

def suite():
    # return unittest.TestSuite(map(EditGeometryDlgTestCase, tests))
    return unittest.makeSuite(TracedisplayTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')


import ipdb
'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
from psysmon.core.preferences_manager import PreferencesManager
from psysmon.core.preferences_manager import PreferenceItem
from psysmon.core.gui_project_preferences import EditProjectPreferencesDlg
from psysmon.core.gui import PSysmonApp

class ProjectPreferencesDlgTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """

    @classmethod
    def setUpClass(cls):
        print "In setUpClass...\n"



    @classmethod
    def tearDownClass(cls):
        print "....in tearDownClass.\n"


    def setUp(self):
        self.app = PSysmonApp()
        self.app.Init()                 # The widget inspection tool can be called using CTRL+ALT+i

        self.pref = PreferencesManager()

        # Add the logging page.
        self.pref.add_page('Logging')

        # The logging verbose level.
        item = PreferenceItem(name = 'verbose', 
                              value = 'DEBUG',
                              mode = 'single_choice',
                              limit = ('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG')
                             )
        self.pref.add_item(pagename = 'Logging', item = item)   

    def tearDown(self):
        pass



    def test_dialog_creation(self):
        ''' Test the creation of the dialog window.
        '''
        dlg = EditProjectPreferencesDlg(preferences = self.pref)
        dlg.ShowModal()
        dlg.Destroy()
        print self.pref
        self.app.MainLoop()



def suite():
    return unittest.makeSuite(ProjectPreferencesDlgTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')


'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
from psysmon.core.preferences_manager import PreferencesManager
from psysmon.core.preferences_manager import PreferenceItem
from psysmon.core.preferences_manager import SingleChoicePrefItem
from psysmon.core.preferences_manager import FloatSpinPrefItem
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

        # Add a single_choice field.
        item = SingleChoicePrefItem(name = 'single_choice',
                              group = 'test group 1',
                              limit = ('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'),
                              value = 'ERROR',
                             )
        self.pref.add_item(pagename = 'Logging', item = item)   

        # Add a textedit field.
        item = PreferenceItem(name = 'textedit', 
                              group = 'test group 1',
                              mode = 'textedit',
                              value = 'this is a textedit field'
                             )
        self.pref.add_item(pagename = 'Logging', item = item)   

        # Add a integer_control field.
        item = PreferenceItem(name = 'integer_control', 
                              group = 'test group 1',
                              mode = 'integer_control',
                              value = 10
                             )
        self.pref.add_item(pagename = 'Logging', item = item)   

        # Add an integer_range field.
        item = PreferenceItem(name = 'integer_range', 
                              group = 'test group 1',
                              mode = 'integer_range',
                              value = 10,
                              limit = (0, 100)
                             )
        self.pref.add_item(pagename = 'Logging', item = item)   

        # Add an float_spin field.
        item = FloatSpinPrefItem(name = 'float_spin', 
                              group = 'test group 1',
                              value = 10.3,
                              limit = (0, 100)
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


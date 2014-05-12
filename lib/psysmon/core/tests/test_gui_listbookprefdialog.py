'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import nose.plugins.attrib as nose_attrib
from psysmon.core.preferences_manager import PreferencesManager
from psysmon.core.preferences_manager import TextEditPrefItem
from psysmon.core.preferences_manager import IntegerControlPrefItem
from psysmon.core.preferences_manager import IntegerSpinPrefItem
from psysmon.core.preferences_manager import SingleChoicePrefItem
from psysmon.core.preferences_manager import MultiChoicePrefItem
from psysmon.core.preferences_manager import FloatSpinPrefItem
from psysmon.core.preferences_manager import FileBrowsePrefItem
from psysmon.core.preferences_manager import DirBrowsePrefItem
from psysmon.core.gui_preference_dialog import ListbookPrefDialog
from psysmon.core.gui import PSysmonApp


@nose_attrib.attr('interactive')
class ListbookPrefDialogTestCase(unittest.TestCase):
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

        # Add a multi_choice field.
        item = MultiChoicePrefItem(name = 'multi_choice',
                              group = 'test group 1',
                              limit = ('value 1', 'value 2', 'value 3', 'value 4', 'value 5'),
                              value = ['value 2', 'value 4'],
                             )
        self.pref.add_item(pagename = 'Logging', item = item)   

        # Add a textedit field.
        item = TextEditPrefItem(name = 'textedit', 
                              group = 'test group 1',
                              value = 'this is a textedit field'
                             )
        self.pref.add_item(pagename = 'Logging', item = item)   

        # Add a integer_control field.
        item = IntegerControlPrefItem(name = 'integer_control', 
                              group = 'test group 1',
                              value = 10
                             )
        self.pref.add_item(pagename = 'Logging', item = item)   

        # Add an integer_range field.
        item = IntegerSpinPrefItem(name = 'integer_range', 
                              group = 'test group 1',
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

        # Add an filebrowse field.
        item = FileBrowsePrefItem(name = 'filebrowse', 
                              group = 'test group 2',
                              value = '',
                              filemask = 'comma separated version (*.csv)|*.csv|' \
                                        'all files (*)|*'
                             )
        self.pref.add_item(pagename = 'Logging', item = item)   

        # Add an dirbrowse field.
        item = DirBrowsePrefItem(name = 'dirbrowse', 
                              group = 'test group 2',
                              value = '' 
                             )
        self.pref.add_item(pagename = 'Logging', item = item)   


    def tearDown(self):
        pass



    def test_dialog_creation(self):
        ''' Test the creation of the dialog window.
        '''
        dlg = ListbookPrefDialog(preferences = self.pref)
        dlg.ShowModal()
        dlg.Destroy()
        print self.pref
        self.app.MainLoop()



def suite():
    return unittest.makeSuite(ListbookPrefDialogTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')


'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import nose.plugins.attrib as nose_attrib
import obspy.core.utcdatetime as udt
from psysmon.core.preferences_manager import PreferencesManager
from psysmon.core.preferences_manager import TextEditPrefItem
from psysmon.core.preferences_manager import IntegerControlPrefItem
from psysmon.core.preferences_manager import IntegerSpinPrefItem
from psysmon.core.preferences_manager import SingleChoicePrefItem
from psysmon.core.preferences_manager import MultiChoicePrefItem
from psysmon.core.preferences_manager import FloatSpinPrefItem
from psysmon.core.preferences_manager import FileBrowsePrefItem
from psysmon.core.preferences_manager import DirBrowsePrefItem
from psysmon.core.preferences_manager import DateTimeEditPrefItem
from psysmon.core.preferences_manager import ListCtrlEditPrefItem
from psysmon.core.preferences_manager import ListGridEditPrefItem
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
        self.pref.add_page('List editor')

        # Add a single_choice field.
        item = SingleChoicePrefItem(name = 'single_choice',
                              group = 'test group 1',
                              limit = ('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'),
                              value = 'ERROR',
                              tool_tip = 'tooltip of the single choice control element'
                             )
        self.pref.add_item(pagename = 'Logging', item = item)

        # Add a multi_choice field.
        item = MultiChoicePrefItem(name = 'multi_choice',
                              group = 'test group 1',
                              limit = ('value 1', 'value 2', 'value 3', 'value 4', 'value 5'),
                              value = ['value 2', 'value 4'],
                              tool_tip = 'tooltip of the multi choice control element'
                             )
        self.pref.add_item(pagename = 'Logging', item = item)

        # Add a textedit field.
        item = TextEditPrefItem(name = 'textedit',
                              group = 'test group 1',
                              value = 'this is a textedit field',
                              tool_tip = 'tooltip of the textedit control element'
                             )
        self.pref.add_item(pagename = 'Logging', item = item)

        # Add a integer_control field.
        item = IntegerControlPrefItem(name = 'integer_control',
                              group = 'test group 1',
                              value = 10,
                              tool_tip = 'tooltip of the integer control element'
                             )
        self.pref.add_item(pagename = 'Logging', item = item)

        # Add an integer_range field.
        item = IntegerSpinPrefItem(name = 'integer_range',
                              group = 'test group 1',
                              value = 10,
                              limit = (0, 100),
                              tool_tip = 'tooltip of the integer spin control element'
                             )
        self.pref.add_item(pagename = 'Logging', item = item)

        # Add an float_spin field.
        item = FloatSpinPrefItem(name = 'float_spin',
                              group = 'test group 1',
                              value = 10.3,
                              limit = (0, 100),
                              tool_tip = 'tooltip of the float spin control element'
                             )
        self.pref.add_item(pagename = 'Logging', item = item)

        # Add a datetime_edit field.
        item = DateTimeEditPrefItem(name = 'datetime',
                                    group = 'test group 1',
                                    value = udt.UTCDateTime('2014-01-01T01:02:03.123456'),
                                    tool_tip = 'tooltip of the datetime edit control element'
                                    )
        self.pref.add_item(pagename = 'Logging', item = item)

        # Add an filebrowse field.
        item = FileBrowsePrefItem(name = 'filebrowse',
                              group = 'test group 2',
                              value = '',
                              filemask = 'comma separated version (*.csv)|*.csv|' \
                                        'all files (*)|*',
                              tool_tip = 'tooltip of the file browse control element'
                             )
        self.pref.add_item(pagename = 'Logging', item = item)

        # Add an dirbrowse field.
        item = DirBrowsePrefItem(name = 'dirbrowse',
                              group = 'test group 2',
                              value = '',
                              tool_tip = 'tooltip of the dir browse control element'
                             )
        self.pref.add_item(pagename = 'Logging', item = item)

        # Add a list grid edit field.
        item = ListCtrlEditPrefItem(name = 'list ctrl',
                                    group = 'list editor',
                                    value = [[11, 12, 13, 14],[21, 22, 23,24]],
                                    column_labels = ['eins', 'zwei', 'drei', 'vier'],
                                    tool_tip = 'tooltip of the list ctrl edit control element'
                                   )
        self.pref.add_item(pagename = 'List editor', item = item)

        # Add a list grid edit field.
        item = ListGridEditPrefItem(name = 'list grid',
                                    group = 'list editor',
                                    value = [],
                                    column_labels = ['eins', 'zwei', 'drei', 'vier'],
                                    tool_tip = 'tooltip of the list grid edit control element'
                                   )
        self.pref.add_item(pagename = 'List editor', item = item)


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


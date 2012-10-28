'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
from psysmon.core.preferences_manager import PreferencesManager
from psysmon.core.preferences_manager import PreferenceItem
from psysmon.core.guiBricks import SingleChoiceField

class PreferencesManagerTestCase(unittest.TestCase):
    """
    Test suite for psysmon.core.preferences_manager.PreferencesManager class.
    """

    @classmethod
    def setUpClass(cls):
        print "In setUpClass...\n"



    @classmethod
    def tearDownClass(cls):
        print "....in tearDownClass.\n"


    def setUp(self):
        self.pref = PreferencesManager()


    def tearDown(self):
        pass


    def test_add_item(self):
        ''' Test the add_item method.
        '''
        # The logging verbose level.
        item = PreferenceItem(name = 'verbose', 
                              value = 'DEBUG',
                              mode = 'single_choice',
                              limit = ('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG')
                             )
        self.pref.add_item(item)     
        self.assertEqual(len(self.pref.pages['preferences']), 1)  
        self.assertTrue(self.pref.pages['preferences'][0].guiclass, SingleChoiceField)                           
        self.assertEqual(self.pref.pages['preferences'][0].name, 'verbose')


        item = PreferenceItem(name = 'pref2', 
                              value = 'value2',
                              mode = 'custom'
                             )
        self.pref.add_item(item)     
        self.assertEqual(len(self.pref.pages['preferences']), 2)                             
        self.assertEqual(self.pref.pages['preferences'][0].name, 'verbose')
        self.assertTrue(self.pref.pages['preferences'][0].guiclass, None)                           
        self.assertEqual(self.pref.pages['preferences'][1].name, 'pref2')

        self.pref.add_page('Testpage')
        item = PreferenceItem(name = 'pref3',
                              value = 'value3',
                              mode = 'custom'
                             )
        self.pref.add_item(item, pagename = 'Testpage')
        self.assertEqual(len(self.pref.pages['Testpage']), 1)
        self.assertEqual(self.pref.pages['Testpage'][0].name, 'pref3')



    def test_get_item(self):
        ''' The the get_item method.
        '''
        item = PreferenceItem(name = 'pref1', 
                              value = 'value1',
                              mode = 'custom'
                             )
        self.pref.add_item(item)     
        item = PreferenceItem(name = 'pref2', 
                              value = 'value2',
                              mode = 'custom'
                             )
        self.pref.add_item(item)     

        cur_item = self.pref.get_item(name = 'pref2')
        self.assertEqual(len(cur_item), 1)
        self.assertEqual(cur_item[0].name, 'pref2')
        self.assertEqual(cur_item[0].value, 'value2')
        self.assertEqual(cur_item[0].mode, 'custom')




def suite():
    return unittest.makeSuite(PreferencesManagerTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')


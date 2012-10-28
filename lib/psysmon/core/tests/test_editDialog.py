'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import psysmon.core.guiBricks as editDialog
import psysmon.core.gui as psygui



class EditDialogTestCase(unittest.TestCase):
    """
    Test suite for psysmon.core.editDialog.EditDialog
    """
    def setUp(self):           
        self.app =psygui.PSysmonApp()
        self.app.Init()                 # The widget inspection tool can be called using CTRL+ALT+i

        self.property = {}
        self.property['prop1'] = "value 1"
        self.property['prop2'] = 15
        self.property['prop3'] = 50
        self.property['prop4'] = "choice 2"
        self.property['prop5'] = ["mChoice 2", "mChoice 4"]
        self.property['prop6'] = '/home/stefan/test.file'
        self.property['prop7'] = '/home/stefan'

        fieldSize = (250, 30)
        largeFieldSize = (250, 90)

        self.dlg = editDialog.EditDialog(options = None)

        # Add two pages
        self.dlg.addPage('MyPage')
        self.dlg.addPage('Second Page')

        # Add a file browse item.
        item = 

        # Create a static box.
        #cont1 = editDialog.StaticBoxContainer(label='Parameters',
        #                                      parent=self.dlg)
        #self.dlg.addContainer(cont1, 'MyPage')



        # Add the fields to the dialog.
        #curField = editDialog.TextEditField(parent=self.dlg,
        #                               name="test",
        #                               propertyKey="prop1",
        #                               size=fieldSize)
        #
        #self.dlg.addField(curField, cont1)


        # Create a second static box.
        #curContainer = editDialog.StaticBoxContainer(label='Another box',
        #                                             parent=self.dlg)
        #self.dlg.addContainer(curContainer, 'Second Page')



        #curField = editDialog.IntegerRangeField(parent=self.dlg,
        #                               name="test 2",
        #                               propertyKey="prop2",
        #                               size=fieldSize,
        #                               range=(10,20))

        #self.dlg.addField(curField, curContainer)



        #curField = editDialog.FloatRangeField(parent=self.dlg,
        #                               name="floatSpin",
        #                               propertyKey="prop3",
        #                               size=fieldSize,
        #                               range=(0,1),
        #                               increment = 0.01,
        #                               digits=2)

        #self.dlg.addField(curField, curContainer)

        #curField = editDialog.FloatRangeField(parent=self.dlg,
        #                               name="floatSpin",
        #                               propertyKey="prop3",
        #                               size=fieldSize,
        #                               range=(0,1),
        #                               increment = 0.01,
        #                               digits=2)

        #self.dlg.addField(curField, curContainer)


        #curField = editDialog.FloatRangeField(parent=self.dlg,
        #                               name="floatSpin",
        #                               propertyKey="prop3",
        #                               size=fieldSize,
        #                               range=(0,1),
        #                               increment = 0.01,
        #                               digits=2)

        #self.dlg.addField(curField, curContainer)



        #choices = ['choice 1', 'choice 2', 'choice 3', 'choice 4']
        #curField = editDialog.SingleChoiceField(parent=self.dlg,
        #                               name="single choice",
        #                               propertyKey="prop4",
        #                               size=fieldSize,
        #                               choices = choices)

        #self.dlg.addField(curField, cont1)


        # A multiChoice field.
        #choices = ['mChoice 1', 'mChoice 2', 'mChoice 3', 'mChoice 4']
        #curField = editDialog.MultiChoiceField(parent=self.dlg,
        #                               name="multi choice",
        #                               propertyKey="prop5",
        #                               size=largeFieldSize,
        #                               choices = choices)

        #self.dlg.addField(curField, cont1)


        # A filebrowser field.
        #curField = editDialog.FileBrowseField(parent=self.dlg,
        #                                      name="file browser",
        #                                      propertyKey="prop6",
        #                                      size=fieldSize)
        #self.dlg.addField(curField, cont1)


        # A dirbrowser field.
        #curField = editDialog.DirBrowseField(parent=self.dlg,
        #                                     name="dir browser",
        #                                     propertyKey="prop7",
        #                                     size=fieldSize)
        #self.dlg.addField(curField, cont1)


        # Show the dialog.
        self.dlg.Show()

        #self.dlg.refit()

    def tearDown(self):
        print self.property
        print "Good by."

    def testDlg(self):
        self.dlg.Show()
        self.app.MainLoop()


#def suite():
#    suite = unittest.makeSuite(EditGeometryDlgTestCase, 'test')
#    return suite

def suite():
    tests = ['testDlg']
    return unittest.TestSuite(map(EditDialogTestCase, tests))


if __name__ == '__main__':
    unittest.main(defaultTest='suite')


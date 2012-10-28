import wx
from wx.lib.stattext import GenStaticText as StaticText
import  wx.lib.filebrowsebutton as filebrowse
import wx.lib.intctrl as intctrl

try:
    from agw import floatspin as FS
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.floatspin as FS

import  wx.lib.rcsizer  as rcs

## The Field class.
# 
# The Field class acts as a superclass of all EditDialog fields. 
# It's an abstract class requiring some methods to be implemented by the 
# subclasses.
class Field(wx.Panel):
    ''' A GUI field.

    The Field class acts as a superclass for all gui-bricks. It's an abstract 
    class requiring some methods to be implemented by the subclasses.
    '''

    def __init__(self, name, pref_item, size, parent=None):
        ''' The constructor.

        Parameters
        ----------
        name : String
            The name of the field. It is used as the field label.

        pref_item : :class:`~psysmon.core.preferences.PrefItem`
            The key of the base option edited by this field.

        size : tuple (width, height)
            The size of the field.

        parent :
            The parent wxPyton window of this field.
        '''
        wx.Panel.__init__(self, parent=parent, size=size, id=wx.ID_ANY)

        #self.SetBackgroundStyle(wx.BG_STYLE_COLOUR)
        #self.SetBackgroundColour('blue')

        ## The parent container of the field.
        #
        # This attribute is set when the field is added to a FieldList.
        self.parentList = None

        ## The name of the field.
        #
        self.name = name

        ## The preference item bound to this field.
        self.pref_item = pref_item

        ## The size of the field.
        #
        self.size = size

        ## The label of the field.
        self.label = name + ":"

        ## The ratio of the label area.
        self.labelRatio = 0.4

        ## The ratio of the control area.
        self.ctrlRatio = 1 - self.labelRatio

        ## The default value of the field element.
        #
        # The default value is set by the EditDialog instance when adding the 
        # field.
        self.defaultValue = None

        # The label element.
        self.labelElement = None

        # The control element.
        self.controlElement = None

        ## The field layout manager.
        self.sizer = wx.GridBagSizer(5,5)
        #self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        #self.sizer = rcs.RowColSizer()

        #self.sizer.AddGrowableCol(0)
        #self.sizer.AddGrowableCol(1)
        #self.sizer.AddGrowableRow(0)

        self.SetSizer(self.sizer)


    def addLabel(self, labelElement):
        self.labelElement = labelElement
        self.sizer.Add(labelElement, pos=(0,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border=1)


    def addControl(self, controlElement):
        self.controlElement = controlElement
        self.sizer.Add(controlElement, pos=(0,1), flag=wx.EXPAND|wx.ALL, border=2)


    def onValueChange(self, event):
        self.setPrefValue()


    ## Set the corresponding value in the options dictionary.
    #
    # @param self The object pointer.
    # @param options The options dictionary to be changed.
    def setPrefValue(self):
        self.pref_item.set_value = self.controlElement.GetValue()

    ## Set the default value of the field element.  
    #
    # @param self The object pointer.
    # @param value The value to be set.      
    def setDefaultValue(self, value):
        self.defaultValue = value
        self.controlElement.SetValue(value)


## The OptionsEditPanel
#
# This class provides an easy to use edit dialog for pSysmon collection nodes.
# One can choose from a set of fields which can be used to change the values 
# of the collection node properties.        
class OptionsEditPanel(wx.Panel):
    ''' The options edit panel.

    This class provides the base container to edit pSysmon nodes (e.g. collection 
    nodes or processing nodes). One can choose from a set of fields which can be
    used to change the values of the options of the related node.
    '''
    def __init__(self, options, parent=None, id=wx.ID_ANY,
                 size=(400,600)):
        wx.Panel.__init__(self, parent=parent, 
                          id=id)


        # The node options being edited with the dialog.
        self.options = options

        # A dictionary of pages created in the notebook.
        self.pages = {}

        # A dictionary of page sizers associated with the pages.
        self.pageSizers = {}

        # The list of container panels holding the fields.
        self.fieldContainer = {}

        # Create the UI elements.
        self.initUI()


    def initUI(self):
        ''' Create the user interface of the panel.

        '''
        # The sizers of the panel.
        self.sizer = wx.GridBagSizer(5,10)
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(0)

        # The panel manages the content in a notebook.
        self.notebook = wx.Notebook(parent=self, id=wx.ID_ANY, style=wx.BK_DEFAULT)
        self.sizer.Add(self.notebook, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=2)  

        self.SetSizer(self.sizer)



    def addPage(self, name):
        ''' Add a page to the notebook of the panel.

        Parameters
        ----------
        name : String
            The name of the page.
        '''
        # All fields are children of the fieldPanel.
        # The field elements should be parents of the same panel to ensure a 
        # consistent tab traversal. 
        self.pages[name] = wx.Panel(self.notebook, wx.ID_ANY)
        self.pageSizers[name] = wx.GridBagSizer(5,10)
        self.pageSizers[name].AddGrowableCol(0)
        self.pages[name].SetSizer(self.pageSizers[name])
        #self.sizer.Add(self.fieldPanel, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=0)

        self.notebook.AddPage(self.pages[name], name) 


    def addContainer(self, container, pageName):
        ''' Add a container to the page of a notebook.

        '''
        if not self.pages:
            print "No dialog pages found. Create one first."
            return

        if not pageName in self.pages.keys():
            print "The specified page is not in the container list."
            return

        container.Reparent(self.pages[pageName])
        row = len(self.fieldContainer)

        print "Adding container at row %d" % row
        self.pageSizers[pageName].Add(container, pos=(row, 0), flag=wx.EXPAND|wx.ALL, border=4)

        container.options = self.options

        print "Adding container with name %s to the dictionary" % container.GetName()
        self.fieldContainer[container.GetName()] = container





## The EditDialog class.
#
# This class provides an easy to use edit dialog for pSysmon collection nodes.
# One can choose from a set of fields which can be used to change the values 
# of the collection node properties.        
class EditDialog(wx.Frame):

    ## The constructor
    #
    # @param self The object pointer.
    # @param options The CollectionNode options being edited with the EditDialog.
    # @param parent The parent wxPython window.
    # @param id The wxPython id.
    # @param title The dialog's title.
    # @param size The dialog's size.
    def __init__(self, options, parent=None, id=wx.ID_ANY, title='edit node', 
                 size=(400,600)):
        wx.Frame.__init__(self, parent=parent, 
                          id=id, 
                          title=title, 
                          pos=wx.DefaultPosition,
                          style=wx.DEFAULT_FRAME_STYLE)
        self.SetMinSize(size)  

        ## The node options being edited with the dialog.
        #
        self.options = options


        ## A dictionary of pages created in the notebook.
        #
        self.pages = {}

        ## A dictionary of page sizers associated with the pages.
        #
        self.pageSizers = {}

        ## The list of container panels holding the fields.
        #
        self.fieldContainer = {}

        # Create the UI elements.
        self.initUI()


    ## Create the dialog's user interface.  
    #
    def initUI(self):
        # The dialog's sizer.
        self.sizer = wx.GridBagSizer(5,10)
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(0)
        self.notebook = wx.Notebook(parent=self, id=wx.ID_ANY, style=wx.BK_DEFAULT)
        self.sizer.Add(self.notebook, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=2)  

        # Create the dialog buttons.
        okButton = wx.Button(self, wx.ID_OK)
        okButton.SetDefault()
        cancelButton = wx.Button(self, wx.ID_CANCEL)
        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        self.sizer.Add(btnSizer, pos=(1,0), flag=wx.EXPAND|wx.ALL, border=4)

        self.SetSizerAndFit(self.sizer)

        # Bind the button events.
        self.Bind(wx.EVT_BUTTON, self.onOk, okButton)
        self.Bind(wx.EVT_BUTTON, self.onCancel, cancelButton)

        #self.Bind(wx.EVT_SIZE, self.onResize)



    ## Handle the ok button click.
    #
    # Update all options values and close the dialog.  
    def onOk(self, event):
        for curContainer in self.fieldContainer.values():
            curContainer.setOptionsValue()

        self.Destroy()

    ## Handle the cancel button click.
    # 
    # Close the dialog.
    def onCancel(self, event):
        self.Destroy()


    def onResize(self, event):
        self.refit()


    def addPage(self, name):
        # All fields are children of the fieldPanel.
        # The field elements should be parents of the same panel to ensure a 
        # consistent tab traversal. 
        self.pages[name] = wx.Panel(self.notebook, wx.ID_ANY)
        self.pageSizers[name] = wx.GridBagSizer(5,10)
        self.pageSizers[name].AddGrowableCol(0)
        self.pages[name].SetSizer(self.pageSizers[name])
        #self.sizer.Add(self.fieldPanel, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=0)

        self.notebook.AddPage(self.pages[name], name) 


    def addContainer(self, container, pageName):
        if not self.pages:
            print "No dialog pages found. Create one first."
            return

        if not pageName in self.pages.keys():
            print "The specified page is not in the container list."
            return

        container.Reparent(self.pages[pageName])
        row = len(self.fieldContainer)

        print "Adding container at row %d" % row
        self.pageSizers[pageName].Add(container, pos=(row, 0), flag=wx.EXPAND|wx.ALL, border=4)

        container.options = self.options

        print "Adding container with name %s to the dictionary" % container.GetName()
        self.fieldContainer[container.GetName()] = container

        self.notebook.Fit()
        self.Fit()

    ## Add a field to the dialog.
    #
    # The field is added to the dialog fieldlist and the field elements are 
    # initialized with the options values.
    def addField(self, field, container):

        if not self.fieldContainer:
            print "No field container found. Create one first."
            return

        if not container in self.fieldContainer.values():
            print "The specified container is not in the container list."
            return

        container.addField(field)
        container.Fit()
        self.notebook.Fit()
        self.Fit()
        #field.SetSize(field.GetBestSize())


    def refit(self):
        self.notebook.Fit()
        for curContainer in self.fieldContainer.values():
            curContainer.SetSize(curContainer.GetBestSize())

            for curField in curContainer.fieldList:
                curField.SetSize(curField.GetBestSize())


## The StaticBoxContainer class.
#
# This class is a container for fields. It is styled as an wx.StaticBox window 
# with a label on the top left of the box.
class StaticBoxContainer(wx.Panel):

    ## The constructor
    #
    # @param self The object pointer.
    # @param parent The window parent.
    # @param label The label of the box appearing on the top left. Also used as the window's name.
    # @param id The wxPython id of the window. 
    def __init__(self, parent, label='Parameters', id=wx.ID_ANY):
        wx.Panel.__init__(self, parent=parent, id=id, name=label)

        ## The parent editDialog.
        self.parentEditDialog = None

        ## The node options being edited with the dialog.
        #
        self.options = None

        ## The list of fields hold by the container.
        self.fieldList = []

        # Create the static box and it's sizer.
        box = wx.StaticBox(self, id=wx.ID_ANY, label=label, name=label)
        self.bSizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        # Create the sizer holding the static box.        
        #border = wx.BoxSizer()
        #border.Add(self.bSizer, wx.ID_ANY,  wx.VERTICAL|wx.EXPAND|wx.ALL, 2)
        self.SetSizer(self.bSizer)


    ## Add a field to the container.
    #
    # The field is added to the container and it's fieldlist.
    def addField(self, field):
        # Set the new field parent.
        field.Reparent(self)
        #field.options = self.options

        #if field.optionsKey in self.options.keys():
        #    field.setDefaultValue(self.options[field.optionsKey])

        self.bSizer.Add(field, 1, wx.EXPAND|wx.LEFT|wx.BOTTOM, 2)

        self.fieldList.append(field)

        self.adjustLabelSize()


    def adjustLabelSize(self):
        labelWidth = [x.labelElement.GetBestSize()[0] for x in self.fieldList]
        maxWidth = max(labelWidth)
        for curField in self.fieldList:
            curSize = curField.labelElement.GetBestSize()
            curField.labelElement.SetMinSize((maxWidth, curSize[1]))

        #self.sizer.Layout()



    ## Set the options values of all the fields in the container.
    #
    # @param self The object pointer. 
    def setOptionsValue(self):
        for curField in self.fieldList:
            curField.setOptionsValue(self.options)




class TextEditField(Field):
    ''' A text edit field.

    A field to edit String values.
    It consits of a label and a TextCtrl element.
    '''

    def __init__(self, name, pref_item, size, parent=None):
        ''' The constructor.

        Parameters
        ----------
        name : String
            The name of the field. It is used as the field label.

        pref_item : :class:`~psysmon.core.preferences.PrefItem`
            The key of the base option edited by this field.

        size : tuple (width, height)
            The size of the field.

        parent :
            The parent wxPyton window of this field.
        '''
        Field.__init__(self, parent=parent, name=name, pref_item = pref_item, size=size)

        # Create the field label.
        self.labelElement = StaticText(parent=self, 
                                       ID=wx.ID_ANY, 
                                       label=self.label,
                                       style=wx.ALIGN_RIGHT)

        # Create the field text control.
        self.controlElement = wx.TextCtrl(self,
                                    wx.ID_ANY)

        # Add the gui elements to the field.
        self.addLabel(self.labelElement)
        self.addControl(self.controlElement)
    
        # Bind the events.
        self.Bind(wx.EVT_TEXT, self.onValueChange, self.controlElement)


    

## The IntegerRangeField class.
#
# A field to edit integer values within a limited range.
# The field consits of a label and a SpinCtrl element.
class IntegerCtrlField(Field):

    ## The constructor
    #
    # @param self The object pointer.
    # @param name The name of the field. Is used as the label too.
    # @param optionsKey The key of the collection node options edited by this field.
    # @param size The size of the field. A tuple. (width, height)
    # @param parent The parent wxPython window of this field.
    # @param range The range limits of the spincontrol. A tuple (min, max).
    def __init__(self, name, optionsKey, size, parent=None):
        Field.__init__(self, parent=parent, name=name, optionsKey=optionsKey, size=size)

        # Create the field label.
        labelElement = StaticText(parent=self, 
                                  ID=wx.ID_ANY, 
                                  label=self.label,
                                  style=wx.ALIGN_RIGHT)

        # Create the field spincontrol.
        controlElement = intctrl.IntCtrl(self, wx.ID_ANY)

        # Add the gui elements to the field.
        self.addLabel(labelElement)
        self.addControl(controlElement)

        # Bind the events.
        self.Bind(intctrl.EVT_INT, self.onValueChange, self.controlElement)




## The IntegerRangeField class.
#
# A field to edit integer values within a limited range.
# The field consits of a label and a SpinCtrl element.
class IntegerRangeField(Field):

    ## The constructor
    #
    # @param self The object pointer.
    # @param name The name of the field. Is used as the label too.
    # @param optionsKey The key of the collection node options edited by this field.
    # @param size The size of the field. A tuple. (width, height)
    # @param parent The parent wxPython window of this field.
    # @param range The range limits of the spincontrol. A tuple (min, max).
    def __init__(self, name, optionsKey, size, parent=None, range=(0,100)):
        Field.__init__(self, parent=parent, name=name, optionsKey=optionsKey, size=size)

        # Create the field label.
        labelElement = StaticText(parent=self, 
                                  ID=wx.ID_ANY, 
                                  label=self.label,
                                  style=wx.ALIGN_RIGHT)

        # Create the field spincontrol.
        controlElement = wx.SpinCtrl(self, wx.ID_ANY)
        controlElement.SetRange(range[0], range[1])

        # Add the gui elements to the field.
        self.addLabel(labelElement)
        self.addControl(controlElement)

        # Bind the event.
        self.Bind(wx.EVT_SPINCTRL, self.onValueChange, self.controlElement)





## The FloatRangeField class.
#
# A field to edit float values within a limited range.
# The field consits of a label and a SpinCtrl element.
class FloatSpinField(Field):

    ## The constructor
    #
    # @param self The object pointer.
    # @param name The name of the field. Is used as the label too.
    # @param optionsKey The key of the collection node options edited by this field.
    # @param size The size of the field. A tuple. (width, height)
    # @param parent The parent wxPython window of this field.
    # @param range The range limits of the spincontrol. A tuple (min, max).
    def __init__(self, name, optionsKey, size, parent=None, min_val=None, max_val=None, increment=0.1, digits=3):
        Field.__init__(self, parent=parent, name=name, optionsKey=optionsKey, size=size)

        # Create the field label.
        labelElement = StaticText(parent=self, 
                                  ID=wx.ID_ANY, 
                                  label=self.label,
                                  style=wx.ALIGN_RIGHT)

        # Create the field spincontrol.
        controlElement = FS.FloatSpin(parent=self, 
                                      id=wx.ID_ANY,
                                      min_val = min_val,
                                      max_val = max_val,
                                      increment=increment,
                                      digits=digits,
                                      agwStyle=FS.FS_LEFT)

        # Add the elements to the field sizer.
        self.addLabel(labelElement)
        self.addControl(controlElement)

        # Bind the events.
        self.Bind(FS.EVT_FLOATSPIN, self.onValueChange, self.controlElement)




## The SingleChoiceField class.
#
# A field to select from a set of choices.
# The choices are listed in a wx.Choice window.
class SingleChoiceField(Field):

    ## The constructor
    #
    # @param self The object pointer.
    # @param name The name of the field. Is used as the label too.
    # @param optionsKey The key of the collection node options edited by this field.
    # @param size The size of the field. A tuple. (width, height)
    # @param parent The parent wxPython window of this field.
    # @param choices A list of choices from which the user can select one value.
    def __init__(self, name, pref_item, size, parent=None):
        Field.__init__(self, parent=parent, name=name, pref_item = pref_item, size=size)

        # Create the field label.
        self.labelElement = StaticText(parent=self, 
                                       ID=wx.ID_ANY, 
                                       label=self.label,
                                       style=wx.ALIGN_RIGHT)

        # Create the field text control.
        self.controlElement = wx.Choice(self, 
                                        wx.ID_ANY,
                                        choices = pref_item.limit)

        self.addLabel(self.labelElement)
        self.addControl(self.controlElement)

        # Set the default value of the field.
        self.setDefaultValue(pref_item.default)

        # Bind the events.
        self.Bind(wx.EVT_CHOICE, self.onValueChange, self.controlElement)



    ## Set the corresponding value in the options dictionary.
    #
    # @param self The object pointer.
    # @param options The options dictionary to be changed.
    def setPrefValue(self):
        print "Setting the value.\n"
        self.pref_item.set_value(self.controlElement.GetStringSelection())


    ## Set the default value of the field element.  
    #
    # @param self The object pointer.
    # @param value The value to be set.  
    def setDefaultValue(self, value):
        self.defaultValue = value
        pos = self.controlElement.FindString(value)
        self.controlElement.SetSelection(pos)



## The MultiChoiceField class.
#
# A field to select multiple entries from a set of choices.
# The choices are listed in a wx.ListBox window.
class MultiChoiceField(Field):

    ## The constructor
    #
    # @param self The object pointer.
    # @param name The name of the field. Is used as the label too.
    # @param optionsKey The key of the collection node options edited by this field.
    # @param size The size of the field. A tuple. (width, height)
    # @param parent The parent wxPython window of this field.
    # @param choices A list of choices from which the user can select one value.
    def __init__(self, name, optionsKey, size, parent=None, choices=[]):
        Field.__init__(self, parent=parent, name=name, optionsKey=optionsKey, size=size)

        # Create the field label.
        labelElement = StaticText(parent=self, 
                                  ID=wx.ID_ANY, 
                                  label=self.label,
                                  style=wx.ALIGN_RIGHT)

        # Create the field text control.
        controlElement = wx.ListBox(self, 
                                    wx.ID_ANY, 
                                    size=(size[0]*self.ctrlRatio, size[1]),
                                    choices=choices,
                                    style=wx.LB_MULTIPLE)

        self.addLabel(labelElement)
        self.addControl(controlElement)
        
        # Bind the events.
        self.Bind(wx.EVT_CHOICE, self.onValueChange, self.controlElement)


    ## Set the corresponding value in the options dictionary.
    #
    # @param self The object pointer.
    # @param options The options dictionary to be changed.
    def setOptionsValue(self):
        if self.optionsKey in self.options.keys():
            selections = self.controlElement.GetSelections()
            selectedStrings = []
            for k in selections:
                selectedStrings.append(self.controlElement.GetString(k))

            self.options[self.optionsKey] = selectedStrings


    ## Set the default value of the field element.  
    #
    # @param self The object pointer.
    # @param value The value to be set.  
    def setDefaultValue(self, value):
        self.defaultValue = value
        for curValue in self.defaultValue:
            self.controlElement.SetStringSelection(curValue) 




## The FileBrowseField class.
#
# A field to select multiple entries from a set of choices.
# The choices are listed in a wx.ListBox window.
class FileBrowseField(Field):

    ## The constructor
    #
    # @param self The object pointer.
    # @param name The name of the field. Is used as the label too.
    # @param optionsKey The key of the collection node options edited by this field.
    # @param size The size of the field. A tuple. (width, height)
    # @param parent The parent wxPython window of this field.
    # @param choices A list of choices from which the user can select one value.
    def __init__(self, name, optionsKey, size, parent=None):

        Field.__init__(self, parent=parent, name=name, optionsKey=optionsKey, size=size)

        # Create the field label.
        labelElement = StaticText(parent=self, 
                                  ID=wx.ID_ANY, 
                                  label=self.label,
                                  style=wx.ALIGN_RIGHT)

        # Create the field text control.
        controlElement = filebrowse.FileBrowseButton(self, 
                                                     wx.ID_ANY, 
                                                     labelWidth=0,
                                                     labelText='',
                                                     changeCallback = self.onValueChange)

        # Add the gui elements to the field.
        self.addLabel(labelElement)
        self.addControl(controlElement)





## The DirBrowseField class.
#
# A field to select multiple entries from a set of choices.
# The choices are listed in a wx.ListBox window.
class DirBrowseField(Field):

    ## The constructor
    #
    # @param self The object pointer.
    # @param name The name of the field. Is used as the label too.
    # @param optionsKey The key of the collection node options edited by this field.
    # @param size The size of the field. A tuple. (width, height)
    # @param parent The parent wxPython window of this field.
    # @param choices A list of choices from which the user can select one value.
    def __init__(self, name, optionsKey, size, parent=None):

        Field.__init__(self, parent=parent, name=name, optionsKey=optionsKey, size=size)

        # Create the field label.
        labelElement = StaticText(parent=self, 
                                       ID=wx.ID_ANY, 
                                       label=self.label,
                                       style=wx.ALIGN_RIGHT)

        # Create the field text control.
        controlElement = filebrowse.DirBrowseButton(self, 
                                                    wx.ID_ANY, 
                                                    size=(size[0]*self.ctrlRatio, size[1]),
                                                    labelText='',
                                                    changeCallback=self.onValueChange
                                                   )

        # Add the gui elements to the field.
        self.addLabel(labelElement)
        self.addControl(controlElement)


    def onValueChange(self, event):
        self.dirBrowseButton.startDirectory = event.GetString()
        self.setOptionsValue()


    ## Set the default value of the field element.  
    #
    # @param self The object pointer.
    # @param value The value to be set.  
    def setDefaultValue(self, value):
        self.defaultValue = value
        self.controlElement.SetValue(value)
        self.controlElement.startDirectory = value


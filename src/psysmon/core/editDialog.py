

import wx
from wx.lib.stattext import GenStaticText as StaticText
import  wx.lib.filebrowsebutton as filebrowse

try:
    from agw import floatspin as FS
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.floatspin as FS

## The Field class.
# 
# The Field class acts as a superclass of all EditDialog fields. 
# It's an abstract class requiring some methods to be implemented by the 
# subclasses.
class Field(wx.Panel):
        
    ## The constructor
    #
    # @param self The object pointer.
    # @param name The name of the field. Is used as the label too.
    # @param propertyKey The key of the collection node property edited by this field.
    # @param size The size of the field. A tuple (width, height).
    # @param parent The parent wxPython window of this field.
    def __init__(self, name, propertyKey, size, parent=None):
        
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
        
        ## The key of the related node property.
        #
        self.propertyKey = propertyKey
        
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
        
                
        ## The field layout manager.
        self.sizer = wx.GridBagSizer(5,5)
        
        
    ## Set the corresponding value in the property dictionary.
    #
    # @param self The object pointer.
    # @param property The property dictionary to be changed.
    def setPropertyValue(self, property):
        assert False, 'setPropertyValue must be defined'
          
    ## Set the default value of the field element.  
    #
    # @param self The object pointer.
    # @param value The value to be set.   
    def setDefaultValue(self):
        assert False, 'setDefaultValue must be defined'
        
        
        
## The EditDialog class.
#
# This class provides an easy to use edit dialog for pSysmon collection nodes.
# One can choose from a set of fields which can be used to change the values 
# of the collection node properties.        
class EditDialog(wx.Frame):
    
    ## The constructor
    #
    # @param self The object pointer.
    # @param property The CollectionNode property being edited with the EditDialog.
    # @param parent The parent wxPython window.
    # @param id The wxPython id.
    # @param title The dialog's title.
    # @param size The dialog's size.
    def __init__(self, property, parent=None, id=wx.ID_ANY, title='edit node', 
                 size=(400,600)):
        wx.Frame.__init__(self, parent=parent, 
                          id=id, 
                          title=title, 
                          pos=wx.DefaultPosition,
                          style=wx.DEFAULT_FRAME_STYLE)
        self.SetMinSize(size)  
        
        ## The node property being edited with the dialog.
        #
        self.property = property
        
        
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
    # Update all property values and close the dialog.  
    def onOk(self, event):
        for curContainer in self.fieldContainer.values():
            curContainer.setPropertyValue()
            
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
        
        container.property = self.property
        
        print "Adding container with name %s to the dictionary" % container.GetName()
        self.fieldContainer[container.GetName()] = container
        
        self.notebook.Fit()
        self.Fit()
        
    ## Add a field to the dialog.
    #
    # The field is added to the dialog fieldlist and the field elements are 
    # initialized with the property values.
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
        
        ## The node property being edited with the dialog.
        #
        self.property = None
        
        ## The list of fields hold by the container.
        self.fieldList = []
        
        # Create the static box and it's sizer.
        box = wx.StaticBox(self, id=wx.ID_ANY, label=label, name=label)
        self.bSizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        
        # Create the sizer holding the static box.        
        border = wx.BoxSizer()
        border.Add(self.bSizer, wx.ID_ANY,  wx.VERTICAL|wx.EXPAND|wx.ALL, 2)
        self.SetSizer(border)
        
        
    ## Add a field to the container.
    #
    # The field is added to the container and it's fieldlist.
    def addField(self, field):
        # Set the new field parent.
        field.Reparent(self)
        
        if field.propertyKey in self.property.keys():
            field.setDefaultValue(self.property[field.propertyKey])
        
        self.bSizer.Add(field, 0, wx.EXPAND|wx.LEFT|wx.BOTTOM, 2)
        
        self.fieldList.append(field)
        
     
    ## Set the property values of all the fields in the container.
    #
    # @param self The object pointer. 
    def setPropertyValue(self):
        for curField in self.fieldList:
            curField.setPropertyValue(self.property)
    
    
        

## The TextEditField class.
#
# A field to edit String values. 
# It consits of a label and a TextCtrl element.
class TextEditField(Field):
    
    ## The constructor
    #
    # @param self The object pointer.
    # @param name The name of the field. Is used as the label too.
    # @param propertyKey The key of the collection node property edited by this field.
    # @param size The size of the field. A tuple. (width, height)
    # @param parent The parent wxPython window of this field.
    def __init__(self, name, propertyKey, size, parent=None):
        Field.__init__(self, parent=parent, name=name, propertyKey=propertyKey, size=size)
                
        # Create the field label.
        self.labelElement = StaticText(parent=self, 
                                       ID=wx.ID_ANY, 
                                       label=self.label,
                                       style=wx.ALIGN_RIGHT)
        self.labelElement.SetMinSize((size[0]*self.labelRatio, -1))
        #self.labelElement.SetBackgroundColour('green')
        
        # Create the field text control.
        self.textCtrl = wx.TextCtrl(self, wx.ID_ANY, size=(size[0]*self.ctrlRatio, size[1]))
        
        # Add the elements to the field sizer.
        self.sizer.Add(self.labelElement, pos=(0, 0), 
                       flag=wx.ALIGN_CENTER_VERTICAL|
                       wx.ALL, 
                       border=2)
        self.sizer.Add(self.textCtrl, pos=(0, 1), flag=wx.EXPAND|wx.ALL, border=2)
        
        # Specify the sizer properties.
        self.sizer.AddGrowableCol(1)
        self.sizer.AddGrowableRow(0)
        self.SetSizer(self.sizer)
        
        
    ## Set the corresponding value in the property dictionary.
    #
    # @param self The object pointer.
    # @param property The property dictionary to be changed.
    def setPropertyValue(self, property):
        if self.propertyKey in property.keys():
            property[self.propertyKey] = self.textCtrl.GetValue().strip()
        
        
    ## Set the default value of the field element.  
    #
    # @param self The object pointer.
    # @param value The value to be set.  
    def setDefaultValue(self, value):
        self.defaultValue = value
        self.textCtrl.SetValue(value)
            
            
## The IntegerRangeField class.
#
# A field to edit integer values within a limited range.
# The field consits of a label and a SpinCtrl element.
class IntegerRangeField(Field):
    
    ## The constructor
    #
    # @param self The object pointer.
    # @param name The name of the field. Is used as the label too.
    # @param propertyKey The key of the collection node property edited by this field.
    # @param size The size of the field. A tuple. (width, height)
    # @param parent The parent wxPython window of this field.
    # @param range The range limits of the spincontrol. A tuple (min, max).
    def __init__(self, name, propertyKey, size, parent=None, range=(0,100)):
        Field.__init__(self, parent=parent, name=name, propertyKey=propertyKey, size=size)
                
        # Create the field label.
        self.labelElement = StaticText(parent=self, 
                                       ID=wx.ID_ANY, 
                                       label=self.label,
                                       style=wx.ALIGN_RIGHT)
        self.labelElement.SetMinSize((size[0]*self.labelRatio, -1))
        
        # Create the field spincontrol.
        self.spinCtrl = wx.SpinCtrl(self, wx.ID_ANY, size=(size[0]*self.ctrlRatio, size[1]))
        self.spinCtrl.SetRange(range[0], range[1])
        
        # Add the elements to the field sizer.
        self.sizer.Add(self.labelElement, pos=(0, 0), 
                       flag=wx.ALIGN_CENTER_VERTICAL|
                       wx.ALL, 
                       border=2)
        self.sizer.Add(self.spinCtrl, pos=(0, 1), flag=wx.ALL, border=2)
        
        # Set the sizer properties.
        self.sizer.AddGrowableCol(1)
        self.sizer.AddGrowableRow(0)
        self.SetSizer(self.sizer)
        
    ## Set the corresponding value in the property dictionary.
    #
    # @param self The object pointer.
    # @param property The property dictionary to be changed.
    def setPropertyValue(self, property):
        if self.propertyKey in property.keys():
            property[self.propertyKey] = self.spinCtrl.GetValue()
            
    ## Set the default value of the field element.  
    #
    # @param self The object pointer.
    # @param value The value to be set.      
    def setDefaultValue(self, value):
        self.defaultValue = value
        self.spinCtrl.SetValue(value)
        
        
        
## The FloatRangeField class.
#
# A field to edit float values within a limited range.
# The field consits of a label and a SpinCtrl element.
class FloatRangeField(Field):
    
    ## The constructor
    #
    # @param self The object pointer.
    # @param name The name of the field. Is used as the label too.
    # @param propertyKey The key of the collection node property edited by this field.
    # @param size The size of the field. A tuple. (width, height)
    # @param parent The parent wxPython window of this field.
    # @param range The range limits of the spincontrol. A tuple (min, max).
    def __init__(self, name, propertyKey, size, parent=None, range=(0,100), increment=0.1, digits=3):
        Field.__init__(self, parent=parent, name=name, propertyKey=propertyKey, size=size)
                
        # Create the field label.
        self.labelElement = StaticText(parent=self, 
                                       ID=wx.ID_ANY, 
                                       label=self.label,
                                       style=wx.ALIGN_RIGHT)
        self.labelElement.SetMinSize((size[0]*self.labelRatio, -1))
        
        # Create the field spincontrol.
        self.spinCtrl = FS.FloatSpin(parent=self, 
                                  id=wx.ID_ANY, 
                                  size=(size[0]*self.ctrlRatio, size[1]),
                                  min_val=range[0],
                                  max_val=range[1],
                                  increment=increment,
                                  digits=digits,
                                  agwStyle=FS.FS_LEFT)
        
        # Add the elements to the field sizer.
        self.sizer.Add(self.labelElement, pos=(0, 0), 
                       flag=wx.ALIGN_CENTER_VERTICAL|
                       wx.ALL, 
                       border=2)
        self.sizer.Add(self.spinCtrl, pos=(0, 1), flag=wx.ALL, border=2)
        
        # Set the sizer properties.
        self.sizer.AddGrowableCol(1)
        self.sizer.AddGrowableRow(0)
        self.SetSizer(self.sizer)
        
    ## Set the corresponding value in the property dictionary.
    #
    # @param self The object pointer.
    # @param property The property dictionary to be changed.
    def setPropertyValue(self, property):
        if self.propertyKey in property.keys():
            property[self.propertyKey] = float(self.spinCtrl.GetValue())
            
    ## Set the default value of the field element.  
    #
    # @param self The object pointer.
    # @param value The value to be set.      
    def setDefaultValue(self, value):
        self.defaultValue = value
        self.spinCtrl.SetValue(value)
            
            
            

## The SingleChoiceField class.
#
# A field to select from a set of choices.
# The choices are listed in a wx.Choice window.
class SingleChoiceField(Field):
    
    ## The constructor
    #
    # @param self The object pointer.
    # @param name The name of the field. Is used as the label too.
    # @param propertyKey The key of the collection node property edited by this field.
    # @param size The size of the field. A tuple. (width, height)
    # @param parent The parent wxPython window of this field.
    # @param choices A list of choices from which the user can select one value.
    def __init__(self, name, propertyKey, size, parent=None, choices=[]):
        Field.__init__(self, parent=parent, name=name, propertyKey=propertyKey, size=size)
                
        # Create the field label.
        self.labelElement = StaticText(parent=self, 
                                       ID=wx.ID_ANY, 
                                       label=self.label,
                                       style=wx.ALIGN_RIGHT)
        self.labelElement.SetMinSize((size[0]*self.labelRatio, -1))
        
        # Create the field text control.
        self.choiceCtrl = wx.Choice(self, 
                                    wx.ID_ANY, 
                                    size=(size[0]*self.ctrlRatio, size[1]),
                                    choices=choices)
        
        # Add the elements to the field sizer.
        self.sizer.Add(self.labelElement, pos=(0, 0), 
                       flag=wx.ALIGN_CENTER_VERTICAL|
                       wx.ALL, 
                       border=2)
        self.sizer.Add(self.choiceCtrl, pos=(0, 1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border=2)
        
        # Specify the sizer properties.
        self.sizer.AddGrowableCol(1)
        self.sizer.AddGrowableRow(0)
        self.SetSizer(self.sizer)
        
    ## Set the corresponding value in the property dictionary.
    #
    # @param self The object pointer.
    # @param property The property dictionary to be changed.
    def setPropertyValue(self, property):
        if self.propertyKey in property.keys():
            property[self.propertyKey] = self.choiceCtrl.GetStringSelection()
        
        
    ## Set the default value of the field element.  
    #
    # @param self The object pointer.
    # @param value The value to be set.  
    def setDefaultValue(self, value):
        self.defaultValue = value
        pos = self.choiceCtrl.FindString(value)
        self.choiceCtrl.SetSelection(pos)
     
     
## The MultiChoiceField class.
#
# A field to select multiple entries from a set of choices.
# The choices are listed in a wx.ListBox window.
class MultiChoiceField(Field):
    
    ## The constructor
    #
    # @param self The object pointer.
    # @param name The name of the field. Is used as the label too.
    # @param propertyKey The key of the collection node property edited by this field.
    # @param size The size of the field. A tuple. (width, height)
    # @param parent The parent wxPython window of this field.
    # @param choices A list of choices from which the user can select one value.
    def __init__(self, name, propertyKey, size, parent=None, choices=[]):
        Field.__init__(self, parent=parent, name=name, propertyKey=propertyKey, size=size)
                
        # Create the field label.
        self.labelElement = StaticText(parent=self, 
                                       ID=wx.ID_ANY, 
                                       label=self.label,
                                       style=wx.ALIGN_RIGHT)
        self.labelElement.SetMinSize((size[0]*self.labelRatio, -1))
        
        # Create the field text control.
        self.listBox = wx.ListBox(self, 
                                    wx.ID_ANY, 
                                    size=(size[0]*self.ctrlRatio, size[1]),
                                    choices=choices,
                                    style=wx.LB_MULTIPLE)
        
        # Add the elements to the field sizer.
        self.sizer.Add(self.labelElement, pos=(0, 0), 
                       flag=wx.ALIGN_TOP|
                       wx.ALL, 
                       border=2)
        self.sizer.Add(self.listBox, pos=(0, 1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border=2)
        
        # Specify the sizer properties.
        self.sizer.AddGrowableCol(1)
        self.sizer.AddGrowableRow(0)
        self.SetSizer(self.sizer)
        
    ## Set the corresponding value in the property dictionary.
    #
    # @param self The object pointer.
    # @param property The property dictionary to be changed.
    def setPropertyValue(self, property):
        if self.propertyKey in property.keys():
            selections = self.listBox.GetSelections()
            selectedStrings = []
            for k in selections:
                selectedStrings.append(self.listBox.GetString(k))
                
            property[self.propertyKey] = selectedStrings
        
        
    ## Set the default value of the field element.  
    #
    # @param self The object pointer.
    # @param value The value to be set.  
    def setDefaultValue(self, value):
        self.defaultValue = value
        for curValue in self.defaultValue:
            self.listBox.SetStringSelection(curValue) 
            
            
            

## The FileBrowseField class.
#
# A field to select multiple entries from a set of choices.
# The choices are listed in a wx.ListBox window.
class FileBrowseField(Field):
    
    ## The constructor
    #
    # @param self The object pointer.
    # @param name The name of the field. Is used as the label too.
    # @param propertyKey The key of the collection node property edited by this field.
    # @param size The size of the field. A tuple. (width, height)
    # @param parent The parent wxPython window of this field.
    # @param choices A list of choices from which the user can select one value.
    def __init__(self, name, propertyKey, size, parent=None):
        
        Field.__init__(self, parent=parent, name=name, propertyKey=propertyKey, size=size)
                
        # Create the field label.
        self.labelElement = StaticText(parent=self, 
                                       ID=wx.ID_ANY, 
                                       label=self.label,
                                       style=wx.ALIGN_RIGHT)
        self.labelElement.SetMinSize((size[0]*self.labelRatio, -1))
        
        # Create the field text control.
        self.fileBrowseButton = filebrowse.FileBrowseButton(self, 
                                                            wx.ID_ANY, 
                                                            size=(size[0]*self.ctrlRatio, size[1]),
                                                            labelWidth=0,
                                                            labelText='')
        
        # Add the elements to the field sizer.
        self.sizer.Add(self.labelElement, pos=(0, 0), 
                       flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, 
                       border=2)
        self.sizer.Add(self.fileBrowseButton, pos=(0, 1), 
                       flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL, 
                       border=2)
        
        # Specify the sizer properties.
        self.sizer.AddGrowableCol(1)
        self.sizer.AddGrowableRow(0)
        self.SetSizer(self.sizer)
        
        
    ## Set the corresponding value in the property dictionary.
    #
    # @param self The object pointer.
    # @param property The property dictionary to be changed.
    def setPropertyValue(self, property):
        if self.propertyKey in property.keys():                
            property[self.propertyKey] = self.fileBrowseButton.GetValue()
        
        
    ## Set the default value of the field element.  
    #
    # @param self The object pointer.
    # @param value The value to be set.  
    def setDefaultValue(self, value):
        self.defaultValue = value
        self.fileBrowseButton.SetValue(value)
        
        
        

## The DirBrowseField class.
#
# A field to select multiple entries from a set of choices.
# The choices are listed in a wx.ListBox window.
class DirBrowseField(Field):
    
    ## The constructor
    #
    # @param self The object pointer.
    # @param name The name of the field. Is used as the label too.
    # @param propertyKey The key of the collection node property edited by this field.
    # @param size The size of the field. A tuple. (width, height)
    # @param parent The parent wxPython window of this field.
    # @param choices A list of choices from which the user can select one value.
    def __init__(self, name, propertyKey, size, parent=None):
        
        Field.__init__(self, parent=parent, name=name, propertyKey=propertyKey, size=size)
                
        # Create the field label.
        self.labelElement = StaticText(parent=self, 
                                       ID=wx.ID_ANY, 
                                       label=self.label,
                                       style=wx.ALIGN_RIGHT)
        self.labelElement.SetMinSize((size[0]*self.labelRatio, -1))
        
        # Create the field text control.
        self.dirBrowseButton = filebrowse.DirBrowseButton(self, 
                                                          wx.ID_ANY, 
                                                          size=(size[0]*self.ctrlRatio, size[1]),
                                                          labelText='',
                                                          changeCallback=self.changeCallback
                                                          )
        
        # Add the elements to the field sizer.
        self.sizer.Add(self.labelElement, pos=(0, 0), 
                       flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, 
                       border=2)
        self.sizer.Add(self.dirBrowseButton, pos=(0, 1), 
                       flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL, 
                       border=2)
        
        # Specify the sizer properties.
        self.sizer.AddGrowableCol(1)
        self.sizer.AddGrowableRow(0)
        self.SetSizer(self.sizer)
        
    
    def changeCallback(self, event):
        self.dirBrowseButton.startDirectory = event.GetString()
    
    ## Set the corresponding value in the property dictionary.
    #
    # @param self The object pointer.
    # @param property The property dictionary to be changed.
    def setPropertyValue(self, property):
        if self.propertyKey in property.keys():                
            property[self.propertyKey] = self.dirBrowseButton.GetValue()
        
        
    ## Set the default value of the field element.  
    #
    # @param self The object pointer.
    # @param value The value to be set.  
    def setDefaultValue(self, value):
        self.defaultValue = value
        self.dirBrowseButton.SetValue(value)
        self.dirBrowseButton.startDirectory = value
        
# LICENSE
#
# This file is part of pSysmon.
#
# If you use pSysmon in any program or publication, please inform and
# acknowledge its author Stefan Mertl (stefan@mertl-research.at).
#
# pSysmon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import wx
from wx.lib.stattext import GenStaticText as StaticText
import  wx.lib.filebrowsebutton as filebrowse
import wx.lib.intctrl as intctrl
try:
    from agw import floatspin as FS
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.floatspin as FS
#import wx.lib.rcsizer  as rcs


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
        self.sizer.AddGrowableCol(1)
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
        self.pref_item.value = self.controlElement.GetValue()

    ## Set the default value of the field element.  
    #
    # @param self The object pointer.
    # @param value The value to be set.      
    def setDefaultValue(self, value):
        self.defaultValue = value
        self.controlElement.SetValue(value)






class PrefPagePanel(wx.Panel):
    ''' A panel representing a page of the preference manager.

    '''
    def __init__(self, parent = None, id = wx.ID_ANY, items = None):
        wx.Panel.__init__(self, parent = parent, id = id)

        self.items = items

        self.init_ui()


    def init_ui(self):
        ''' Build the gui elements required by the preference items.

        '''
        sizer = wx.GridBagSizer(0,0)
        # Find all groups.
        groups = list(set([x.group for x in self.items]))

        for k, cur_group in enumerate(groups):
            # Create a static box container for the group.
            if cur_group is None:
                container_label = ''
            else:
                container_label = cur_group
            cur_container = StaticBoxContainer(parent = self, 
                                label = container_label)

            groupitems = [x for x in self.items if x.group == cur_group]
            for cur_item in groupitems:
                if cur_item.mode in gui_elements.keys():
                    guiclass = gui_elements[cur_item.mode]
                    gui_element = guiclass(name = cur_item.label,
                                           pref_item = cur_item,
                                           size = (100, 10),
                                           parent = cur_container 
                                          )
                    cur_item.set_gui_element(gui_element)
                    cur_container.addField(gui_element)
                else:
                    self.logger.warning('Item %s of mode %s has no guiclass.', 
                            cur_item.name, cur_item.mode)

            sizer.Add(cur_container, pos = (k,0), flag = wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, border = 10)

        sizer.AddGrowableCol(0)
        self.SetSizer(sizer)




## The OptionsEditPanel
#
# This class provides an easy to use edit dialog for pSysmon collection nodes.
# One can choose from a set of fields which can be used to change the values 
# of the collection node properties.        
class PrefEditPanel(wx.Panel):
    ''' The preferences edit panel.

    This class provides the base container to edit pSysmon nodes (e.g. collection 
    nodes or processing nodes). One can choose from a set of fields which can be
    used to change the values of the options of the related node.
    '''
    def __init__(self, pref, parent=None, id=wx.ID_ANY,
                 size=(400,600)):
        wx.Panel.__init__(self, parent=parent, 
                          id=id)

        # The logger.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        # The node options being edited with the dialog.
        self.pref = pref

        # Create the UI elements.
        self.initUI()


    def initUI(self):
        ''' Create the user interface of the panel.

        '''
        # The sizers of the panel.
        self.sizer = wx.GridBagSizer(5,10)
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(0)

        # The notebook holding the differnt pages of the preferences.
        self.notebook = wx.Notebook(parent=self, id=wx.ID_ANY, style=wx.BK_DEFAULT)
        self.sizer.Add(self.notebook, pos=(0,0), flag=wx.EXPAND|wx.ALL, border=2)
        self.build_notebook()


        self.SetSizer(self.sizer)



    def build_notebook(self):
        ''' Build the notebook based on the project preferences.

        '''
        pagenames = sorted(self.pref.pages.keys())

        for cur_pagename in pagenames:
            panel = PrefPagePanel(parent = self.notebook, 
                                  id = wx.ID_ANY,
                                  items = self.pref.pages[cur_pagename]
                                 )
            self.notebook.AddPage(panel, cur_pagename)






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
        self.b_sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        # Create the sizer holding the fields.
        self.sizer = wx.GridBagSizer(5)
        self.sizer.AddGrowableCol(0)

        self.b_sizer.Add(self.sizer, 1, flag = wx.EXPAND)

        # Create the sizer holding the static box.        
        self.SetSizer(self.b_sizer)


    ## Add a field to the container.
    #
    # The field is added to the container and it's fieldlist.
    def addField(self, field):
        # Set the new field parent.
        field.Reparent(self)
        #field.options = self.options

        #if field.optionsKey in self.options.keys():
        #    field.setDefaultValue(self.options[field.optionsKey])

        #self.bSizer.Add(field, 1, wx.EXPAND|wx.LEFT|wx.BOTTOM, 2)
        self.sizer.Add(field, pos = (len(self.fieldList)+1, 0), flag=wx.EXPAND)

        self.fieldList.append(field)

        self.adjustLabelSize()


    def adjustLabelSize(self):
        labelWidth = [x.labelElement.GetBestSize()[0] for x in self.fieldList]
        maxWidth = max(labelWidth)
        for curField in self.fieldList:
            curSize = curField.labelElement.GetBestSize()
            curField.labelElement.SetMinSize((maxWidth, curSize[1]))

        #self.GetSizer().Layout()



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
        self.controlElement = wx.TextCtrl(self, wx.ID_ANY)

        # Set the default value of the field.
        self.setDefaultValue(pref_item.default)

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
        Field.__init__(self, parent=parent, name=name,
                       pref_item = pref_item, size=size)

        # Create the field label.
        self.labelElement = StaticText(parent=self, 
                                       ID=wx.ID_ANY, 
                                       label=self.label,
                                       style=wx.ALIGN_RIGHT)

        # Create the field spincontrol.
        self.controlElement = intctrl.IntCtrl(self, wx.ID_ANY)

        # Set the default value of the field.
        self.setDefaultValue(pref_item.default)
        
        # Add the gui elements to the field.
        self.addLabel(self.labelElement)
        self.addControl(self.controlElement)

        # Bind the events.
        self.Bind(intctrl.EVT_INT, self.onValueChange, self.controlElement)




## The IntegerRangeField class.
#
# A field to edit integer values within a limited range.
# The field consits of a label and a SpinCtrl element.
class IntegerRangeField(Field):
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
        Field.__init__(self, parent=parent, name=name, 
                       pref_item = pref_item, size=size)

        # Create the field label.
        self.labelElement = StaticText(parent=self, 
                                  ID=wx.ID_ANY, 
                                  label=self.label,
                                  style=wx.ALIGN_RIGHT)

        # Create the field spincontrol.
        self.controlElement = wx.SpinCtrl(self, wx.ID_ANY)
        self.controlElement.SetRange(pref_item.limit[0], pref_item.limit[1])

        # Set the default value of the field.
        self.setDefaultValue(pref_item.default)

        # Add the gui elements to the field.
        self.addLabel(self.labelElement)
        self.addControl(self.controlElement)

        # Bind the event.
        self.Bind(wx.EVT_SPINCTRL, self.onValueChange, self.controlElement)


class CheckBoxField(Field):

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
        Field.__init__(self, parent=parent, name=name, 
                       pref_item = pref_item, size=size)

        # Create the field label.
        self.labelElement = StaticText(parent=self, 
                                  ID=wx.ID_ANY, 
                                  label=self.label,
                                  style=wx.ALIGN_RIGHT)

        # Create the field spincontrol.
        self.controlElement = wx.CheckBox(parent=self,
                                          label = '',
                                          id=wx.ID_ANY)

        # Set the default value of the field.
        self.setDefaultValue(pref_item.default)

        # Add the elements to the field sizer.
        self.addLabel(self.labelElement)
        self.addControl(self.controlElement)

        # Bind the events.
        self.Bind(wx.EVT_CHECKBOX, self.onValueChange, self.controlElement)




## The FloatRangeField class.
#
# A field to edit float values within a limited range.
# The field consits of a label and a SpinCtrl element.
class FloatSpinField(Field):

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
        Field.__init__(self, parent=parent, name=name, 
                       pref_item = pref_item, size=size)

        # Create the field label.
        self.labelElement = StaticText(parent=self, 
                                  ID=wx.ID_ANY, 
                                  label=self.label,
                                  style=wx.ALIGN_RIGHT)

        # Create the field spincontrol.
        self.controlElement = FS.FloatSpin(parent=self, 
                                      id=wx.ID_ANY,
                                      min_val = pref_item.limit[0],
                                      max_val = pref_item.limit[1],
                                      increment = pref_item.increment,
                                      digits = pref_item.digits,
                                      agwStyle=FS.FS_LEFT)

        # Set the default value of the field.
        self.setDefaultValue(pref_item.default)

        # Add the elements to the field sizer.
        self.addLabel(self.labelElement)
        self.addControl(self.controlElement)

        # Bind the events.
        self.Bind(FS.EVT_FLOATSPIN, self.onValueChange, self.controlElement)




## The SingleChoiceField class.
#
# A field to select from a set of choices.
# The choices are listed in a wx.Choice window.
class SingleChoiceField(Field):

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
        self.pref_item.value = self.controlElement.GetStringSelection()


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
    ''' The MultiChoiceField class.

    A field to select multiple entries from a set of choices.
    The choices are listed in a wx.ListBox window.
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
        self.controlElement = wx.ListBox(self, 
                                    wx.ID_ANY, 
                                    choices = pref_item.limit,
                                    style=wx.LB_MULTIPLE)

        self.addLabel(self.labelElement)
        self.addControl(self.controlElement)
        
        # Set the default value of the field.
        self.setDefaultValue(pref_item.default)
        
        # Bind the events.
        self.Bind(wx.EVT_LISTBOX, self.onValueChange, self.controlElement)
        #self.Bind(wx.EVT_CHOICE, self.onValueChange, self.controlElement)


    ## Set the corresponding value in the options dictionary.
    #
    # @param self The object pointer.
    # @param options The options dictionary to be changed.
    def setPrefValue(self):
        selections = self.controlElement.GetSelections()
        selectedStrings = []
        for k in selections:
            selectedStrings.append(self.controlElement.GetString(k))

        self.pref_item.value = selectedStrings


    ## Set the default value of the field element.  
    #
    # @param self The object pointer.
    # @param value The value to be set.  
    def setDefaultValue(self, value):
        self.defaultValue = value
        for curValue in value:
            self.controlElement.SetStringSelection(curValue) 




class FileBrowseField(Field):
    ''' The fileBrowseField class.
    
    A field to select a single file using a file select dialog.
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
        self.controlElement = filebrowse.FileBrowseButton(self, 
                                                     wx.ID_ANY, 
                                                     labelWidth=0,
                                                     labelText='',
                                                     fileMask = pref_item.filemask,
                                                     changeCallback = self.onValueChange)

        # Add the gui elements to the field.
        self.addLabel(self.labelElement)
        self.addControl(self.controlElement)


        # Set the default value of the field.
        self.setDefaultValue(pref_item.default)


    def setPrefValue(self):
        ''' Set the value of the preference item bound to the field.
        '''
        self.pref_item.value = self.controlElement.GetValue()


    def setDefaultValue(self, value):
        ''' Set the value of the field control element.

        Parameters
        ----------
        value : String
            The new value of the filebrowse control element.
        '''
        self.defaultValue = value
        self.controlElement.SetValue(value)


class DirBrowseField(Field):
    ''' The DirBrowseField class.

    A field to select a single directory using a directory select dialog.
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
        self.controlElement = filebrowse.DirBrowseButton(self, 
                                                    wx.ID_ANY, 
                                                    labelText='',
                                                    changeCallback=self.onValueChange,
                                                    startDirectory = pref_item.start_directory
                                                   )

        # Add the gui elements to the field.
        self.addLabel(self.labelElement)
        self.addControl(self.controlElement)

        # Set the default value of the field.
        self.setDefaultValue(pref_item.default)


    def setPrefValue(self):
        ''' Set the value of the preference item bound to the field.
        '''
        self.pref_item.value = self.controlElement.GetValue()
        self.pref_item.start_directory = self.pref_item.value


    def setDefaultValue(self, value):
        ''' Set the value of the field control element.

        Parameters
        ----------
        value : String
            The new value of the filebrowse control element.
        '''
        self.defaultValue = value
        self.controlElement.SetValue(value)
        #self.controlElement.startDirectory = value



# Define the assignment of the field type and the GUI representation.
gui_elements = {}
gui_elements['single_choice'] = SingleChoiceField
gui_elements['multi_choice'] = MultiChoiceField
gui_elements['textedit'] = TextEditField
gui_elements['integer_control'] = IntegerCtrlField
gui_elements['integer_spin'] = IntegerRangeField
gui_elements['float_spin'] = FloatSpinField
gui_elements['filebrowse'] = FileBrowseField
gui_elements['dirbrowse'] = DirBrowseField
gui_elements['datetime_edit'] = TextEditField
gui_elements['checkbox'] = CheckBoxField

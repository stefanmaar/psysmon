from __future__ import print_function
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
import obspy.core.utcdatetime as udt
import wx
import wx.grid
from wx.lib.stattext import GenStaticText as StaticText
import  wx.lib.filebrowsebutton as filebrowse
import wx.lib.intctrl as intctrl
try:
    from agw import floatspin as FS
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.floatspin as FS
#import wx.lib.rcsizer  as rcs
import psysmon.core.preferences_manager as psy_pm
from operator import itemgetter
import wx.lib.mixins.listctrl as listmix



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

    def __del__(self):
        try:
            self.pref_item.remove_gui_element(self)
        except Exception:
            pass


    def addLabel(self, labelElement):
        self.labelElement = labelElement
        self.sizer.Add(labelElement, pos=(0,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border=1)


    def addControl(self, controlElement):
        self.controlElement = controlElement
        if self.pref_item.tool_tip is not None:
            self.controlElement.SetToolTipString(self.pref_item.tool_tip)
        self.sizer.Add(controlElement, pos=(0,1), flag=wx.EXPAND|wx.ALL, border=2)
        self.sizer.AddGrowableCol(1)


    def onValueChange(self, event):
        self.setPrefValue()
        self.call_hook('on_value_change')


    ## Set the corresponding value in the options dictionary.
    #
    # @param self The object pointer.
    # @param options The options dictionary to be changed.
    def setPrefValue(self):
        self.pref_item.value = self.controlElement.GetValue()


    def setControlElementValue(self):
        self.controlElement.SetValue(self.pref_item.value)


    def updateLimit(self):
        pass

    def disable(self):
        self.controlElement.Disable()


    def call_hook(self, hook_name):
        ''' Call the registerd hooks of the pref item.
        '''
        if hook_name in self.pref_item.hooks.iterkeys():
            self.pref_item.hooks[hook_name]()







class PrefPagePanel(wx.Panel):
    ''' A panel representing a page of the preference manager.

    '''
    def __init__(self, parent = None, id = wx.ID_ANY, page = None):
        wx.Panel.__init__(self, parent = parent, id = id)

        self.page = page

        self.init_ui()


    def init_ui(self):
        ''' Build the gui elements required by the preference items.

        '''
        sizer = wx.GridBagSizer(0,0)

        for k, cur_group in enumerate(self.page.groups):
            # Create a static box container for the group.
            cur_container = StaticBoxContainer(parent = self,
                                label = cur_group.name)

            for cur_item in [x for x in cur_group.items if x.visible]:
                if isinstance(cur_item, psy_pm.ActionItem):
                    gui_element = wx.Button(parent = cur_container,
                                            id = wx.ID_ANY,
                                            label = cur_item.label)
                    if cur_item.tool_tip is not None:
                        gui_element.SetToolTipString(cur_item.tool_tip)
                    gui_element.Bind(wx.EVT_BUTTON, cur_item.action)
                    cur_item.set_gui_element(gui_element)
                    cur_container.addActionField(gui_element)
                else:
                    if cur_item.mode in gui_elements.iterkeys():
                        guiclass = gui_elements[cur_item.mode]
                    else:
                        guiclass = cur_item.gui_class

                    gui_element = guiclass(name = cur_item.label,
                                           pref_item = cur_item,
                                           size = (100, -1),
                                           parent = cur_container
                                          )
                    cur_item.set_gui_element(gui_element)
                    cur_container.addField(gui_element)

            if k == 0:
                sizer.Add(cur_container, pos = (k,0), flag = wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.TOP | wx.EXPAND, border = 10)
            else:
                sizer.Add(cur_container, pos = (k,0), flag = wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, border = 10)

        sizer.AddGrowableCol(0)
        self.SetSizer(sizer)



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

        for cur_page in self.pref.pages:
            panel = PrefPagePanel(parent = self.notebook,
                                  id = wx.ID_ANY,
                                  page = cur_page)
            self.notebook.AddPage(panel, cur_page.name)






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

        self.actionFieldList = []

        # Create the static box and it's sizer.
        box = wx.StaticBox(self, id=wx.ID_ANY, label=label.upper(), name=label)
        self.b_sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        # Create the sizer holding the fields.
        self.sizer = wx.GridBagSizer(5)
        self.sizer.AddGrowableCol(0)

        self.b_sizer.Add(self.sizer, 0, flag = wx.EXPAND)

        # Create the sizer holding the static box.        
        self.SetSizer(self.b_sizer)

    def __len__(self):
        ''' The number of fields.
        '''
        return len(self.fieldList) + len(self.actionFieldList)


    def __del__(self):
        '''
        '''
        print("Deleting StaticBoxContainer.")
        for cur_field in self.fieldList:
            cur_field.pref_item.remove_gui_element(cur_field)


    ## Add a field to the container.
    #
    # The field is added to the container and it's fieldlist.
    def addField(self, field):
        # Set the new field parent.
        field.Reparent(self)
        #field.options = self.options

        #self.bSizer.Add(field, 1, wx.EXPAND|wx.LEFT|wx.BOTTOM, 2)
        self.sizer.Add(field, pos = (len(self), 0), flag=wx.EXPAND)

        self.fieldList.append(field)

        self.adjustLabelSize()

        for cur_field in self.fieldList:
            cur_field.SetMinSize(cur_field.GetBestSize())


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


    def addActionField(self, field):
        # Set the new field parent.
        field.Reparent(self)
        #field.options = self.options

        #self.bSizer.Add(field, 1, wx.EXPAND|wx.LEFT|wx.BOTTOM, 2)
        self.sizer.Add(field, pos = (len(self), 0), flag=wx.EXPAND)

        self.actionFieldList.append(field)



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

        # Add the gui elements to the field.
        self.addLabel(self.labelElement)
        self.addControl(self.controlElement)

        # Set the value of the control element.
        self.setControlElementValue()

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

        # Add the gui elements to the field.
        self.addLabel(self.labelElement)
        self.addControl(self.controlElement)

        # Set the value of the control element.
        self.setControlElementValue()

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

        # Add the gui elements to the field.
        self.addLabel(self.labelElement)
        self.addControl(self.controlElement)

        # Set the value of the control element.
        self.setControlElementValue()

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

        # Add the elements to the field sizer.
        self.addLabel(self.labelElement)
        self.addControl(self.controlElement)

        # Set the value of the control element.
        self.setControlElementValue()

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
        self.controlElement.SetFormat(pref_item.spin_format)

        # Add the elements to the field sizer.
        self.addLabel(self.labelElement)
        self.addControl(self.controlElement)

        # Set the value of the control element.
        self.setControlElementValue()

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

        # Set the value of the control element.
        self.setControlElementValue()

        # Bind the events.
        self.Bind(wx.EVT_CHOICE, self.onValueChange, self.controlElement)



    ## Set the corresponding value in the options dictionary.
    #
    # @param self The object pointer.
    # @param options The options dictionary to be changed.
    def setPrefValue(self):
        self.pref_item.value = self.controlElement.GetStringSelection()


    def setControlElementValue(self):
        if self.pref_item.value:
            pos = self.controlElement.FindString(self.pref_item.value)
            self.controlElement.SetSelection(pos)


    def updateLimit(self):
        self.controlElement.SetItems(self.pref_item.limit)
        self.setControlElementValue()


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

        # Set the value of the control element.
        self.setControlElementValue()

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


    def setControlElementValue(self):
        for curValue in self.pref_item.value:
            self.controlElement.SetStringSelection(curValue)


    def updateLimit(self):
        self.controlElement.SetItems(self.pref_item.limit)
        self.setControlElementValue()



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
        if pref_item.tool_tip is None:
            pref_item.tool_tip = 'Type filename or click browse to choose file.'

        self.controlElement = filebrowse.FileBrowseButton(self,
                                                     wx.ID_ANY,
                                                     labelWidth=0,
                                                     labelText='',
                                                     fileMask = pref_item.filemask,
                                                     changeCallback = self.onValueChange,
                                                     toolTip = pref_item.tool_tip)

        # Add the gui elements to the field.
        self.addLabel(self.labelElement)
        self.addControl(self.controlElement)

        # Set the value of the control element.
        self.setControlElementValue()


    def setPrefValue(self):
        ''' Set the value of the preference item bound to the field.
        '''
        self.pref_item.value = self.controlElement.GetValue()




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
        if pref_item.tool_tip is None:
            pref_item.tool_tip = 'Type filename or click browse to choose file.'

        self.controlElement = filebrowse.DirBrowseButton(self,
                                                    wx.ID_ANY,
                                                    labelText='',
                                                    changeCallback=self.onValueChange,
                                                    startDirectory = pref_item.start_directory,
                                                    toolTip = pref_item.tool_tip
                                                   )

        # Add the gui elements to the field.
        self.addLabel(self.labelElement)
        self.addControl(self.controlElement)

        # Set the value of the control element.
        self.setControlElementValue()


    def setPrefValue(self):
        ''' Set the value of the preference item bound to the field.
        '''
        self.pref_item.value = self.controlElement.GetValue()
        self.pref_item.start_directory = self.pref_item.value



class DateTimeEditField(Field):
    ''' A date time edit field.

    A field to edit datetime values.
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

        # Add the gui elements to the field.
        self.addLabel(self.labelElement)
        self.addControl(self.controlElement)

        # Set the value of the control element.
        self.setControlElementValue()

        # Bind the events.
        self.Bind(wx.EVT_TEXT, self.onValueChange, self.controlElement)

    ## Set the corresponding value in the options dictionary.
    #
    # @param self The object pointer.
    # @param options The options dictionary to be changed.
    def setPrefValue(self):
        self.pref_item.value = udt.UTCDateTime(self.controlElement.GetValue())


    def setControlElementValue(self):
        self.controlElement.SetValue(self.pref_item.value.isoformat())



class ListCtrlEditField(Field, listmix.ColumnSorterMixin):
    ''' A field to edit a list using a wx.ListCtrl.
    '''
    def __init__(self, name, pref_item, size, parent=None):
        ''' Initialize the instance.

        '''
        Field.__init__(self, parent=parent, name=name, pref_item = pref_item, size=size)

        # Create the field label.
        self.labelElement = StaticText(parent=self,
                                       ID=wx.ID_ANY,
                                       label=self.label,
                                       style=wx.ALIGN_RIGHT)

        # Create the field text control.
        self.controlElement = SortableListCtrl(parent = self,
                                               id = wx.ID_ANY,
                                               style=wx.LC_REPORT
                                               | wx.BORDER_NONE
                                               #| wx.LC_SINGLE_SEL
                                               | wx.LC_SORT_ASCENDING,
                                               n_columns = len(pref_item.column_labels)
                                              )
        self.controlElement.itemDataMap = {}

        for k, cur_label in enumerate(pref_item.column_labels):
            self.controlElement.InsertColumn(k, cur_label)

        self.fill_listctrl(data = pref_item.limit)

        #listmix.ColumnSorterMixin.__init__(self, len(pref_item.column_labels))

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected, self.controlElement)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_item_deselected, self.controlElement)

        # Add the gui elements to the field.
        self.addLabel(self.labelElement)
        self.addControl(self.controlElement)




    def fill_listctrl(self, data):
        index = 0
        self.controlElement.DeleteAllItems()

        for cur_row in data:
            for k, cur_data in enumerate(cur_row):
                if k == 0:
                    self.controlElement.InsertStringItem(index, str(cur_data))
                else:
                    self.controlElement.SetStringItem(index, k, str(cur_data))

            self.controlElement.itemDataMap[index] = cur_row
            self.controlElement.SetItemData(index, index)

            if cur_row in self.pref_item.value:
                self.controlElement.SetItemState(index, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

            index += 1


    def on_item_selected(self, event):
        '''
        '''
        item_data = self.controlElement.GetItemData(event.GetIndex())
        selected_value = self.controlElement.itemDataMap[item_data]
        if selected_value not in self.pref_item.value:
            self.pref_item.value.append(selected_value)

        self.call_hook('on_value_change')


    def on_item_deselected(self, event):
        '''
        '''
        item_data = self.controlElement.GetItemData(event.GetIndex())
        selected_value = self.controlElement.itemDataMap[item_data]
        self.pref_item.value.remove(selected_value)
        self.call_hook('on_value_change')


    def updateLimit(self):
        '''
        '''
        # Check if the value is still available in the limit.
        # TODO: add a key attribute which sets the fields which should be used
        # to compare the values (e.g. the database id).
        self.pref_item.value = [x for x in self.pref_item.value if x in self.pref_item.limit]

        self.fill_listctrl(data = self.pref_item.limit)


class SortableListCtrl(wx.ListCtrl, listmix.ColumnSorterMixin):

    def __init__(self, parent, id = wx.ID_ANY,
                 pos = wx.DefaultPosition,
                 size = wx.DefaultSize, style = None,
                 n_columns = None):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.ColumnSorterMixin.__init__(self, n_columns)

        # Used by ColumnSorterMixin.
        self.il = wx.ImageList(16, 16)
        self.sm_up = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_OTHER, (16,16)))
        self.sm_dn = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_OTHER, (16,16)))

        # Create the icons for column sorting.
        self.il = wx.ImageList(16, 16)
        self.sm_up = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_OTHER, (16,16)))
        self.sm_dn = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_OTHER, (16,16)))

        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)


    def GetListCtrl(self):
        ''' Used by ColumnSorterMixin.
        '''
        return self

    def GetSortImages(self):
        ''' Used by ColumnSorterMixin.
        '''
        return (self.sm_dn, self.sm_up)



class ListGridEditField(Field):
    ''' A field to edit a list using a wx.grid.Grid.

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
        self.controlElement = FileGrid(parent = self,
                                       data = self.pref_item.value,
                                       column_labels = self.pref_item.column_labels)

        # Add the gui elements to the field.
        self.addLabel(self.labelElement)
        self.addControl(self.controlElement)



class FileGrid(wx.grid.Grid):
    def __init__(self, parent, data, column_labels):
        wx.grid.Grid.__init__(self, parent, wx.ID_ANY)

        table = GridDataTable(data = data,
                              column_labels = column_labels)

        self.SetTable(table, True)

        self.AutoSizeColumns(setAsMin = True)
        self.SetMinSize((100, 100))
        #self.SetMaxSize((-1, 600))

        self.last_selected_row = None

        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.onLabelRightClicked)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.onCellLeftClicked)


    def Reset(self):
        """reset the view based on the data in the table.  Call
        this when rows are added or destroyed"""
        self.GetTable().ResetView()

    def removeRows(self, rows):
        ''' Remove the rows specified by the indexes in rows.
        '''
        for k in rows:
            self.GetTable().data.pop(k)

        self.Reset()


    def clear(self):
        ''' Clear the data from the table.
        '''
        self.GetTable().data = []
        self.Reset()


    def doResize(self, event=None):
            self.GetParent().Freeze()
            self.AutoSize()
            self.GetParent().Layout()

            #the column which will be expanded
            expandCol = 1

            #calculate the total width of the other columns
            otherWidths = 0
            for i in [i for i in range(self.GetNumberCols()) if i != expandCol]:
                colWidth = self.GetColSize(i)
                otherWidths += colWidth

            #add the width of the row label column
            otherWidths += self.RowLabelSize

            descWidth = self.Size[0] - otherWidths

            self.SetColSize(expandCol, descWidth)

            self.GetParent().Layout()

            if event:
                event.Skip()
            self.GetParent().Thaw()


    def onLabelRightClicked(self, evt):
        # Did we click on a row or a column?
        row, col = evt.GetRow(), evt.GetCol()
        if row == -1: self.colPopup(col, evt)
        elif col == -1: self.rowPopup(row, evt)


    def onCellLeftClicked(self, evt):
        if evt.ShiftDown() == True:
            if evt.ControlDown() == False:
                self.ClearSelection()

            selected_row = evt.GetRow()
            if selected_row >= self.last_selected_row:
                for k in range(self.last_selected_row, selected_row + 1):
                    self.SelectRow(k, addToSelected = True)
            else:
                for k in range(selected_row, self.last_selected_row + 1):
                    self.SelectRow(k, addToSelected = True)

        else:
            if evt.ControlDown() == True:
                add_to_selection = True
            else:
                add_to_selection = False
            self.SelectRow(evt.GetRow(), addToSelected = add_to_selection)
            self.last_selected_row = evt.GetRow()


    def colPopup(self, col, evt):
        """(col, evt) -> display a popup menu when a column label is
        right clicked"""
        x = self.GetColSize(col)/2
        menu = wx.Menu()

        xo, yo = evt.GetPosition()
        self.SelectCol(col)
        cols = self.GetSelectedCols()
        self.Refresh()
        sort_asc_menu = menu.Append(wx.ID_ANY, "sort column asc.")
        sort_desc_menu = menu.Append(wx.ID_ANY, "sort column desc.")

        def sort(event, reverse, self=self, col=col):
            self.GetTable().sortColumn(col, reverse = reverse)
            self.Reset()

        self.Bind(wx.EVT_MENU, lambda event: sort(event, reverse=False), sort_asc_menu)
        self.Bind(wx.EVT_MENU, lambda event: sort(event, reverse=True), sort_desc_menu)

        self.PopupMenu(menu)
        menu.Destroy()



class GridDataTable(wx.grid.PyGridTableBase):
    def __init__(self, data, column_labels):
        wx.grid.PyGridTableBase.__init__(self)
        self.data = data
        self.col_labels = column_labels

        self.currentRows = self.GetNumberRows()
        self.currentColumns = self.GetNumberCols()

        self.format_default = wx.grid.GridCellAttr()

    def GetNumberRows(self):
        """Return the number of rows in the grid"""
        if len(self.data) == 0:
            n_rows = 1
        else:
            n_rows = len(self.data)

        return n_rows

    def GetNumberCols(self):
        """Return the number of columns in the grid"""
        return len(self.col_labels)

    def IsEmptyCell(self, row, col):
        """Return True if the cell is empty"""
        return False

    def GetTypeName(self, row, col):
        """Return the name of the data type of the value in the cell"""
        return None

    def GetValue(self, row, col):
        """Return the value of a cell"""
        if len(self.data) == 0:
            return ''
        elif len(self.data) < row:
            return ''
        else:
            return str(self.data[row][col])

    def SetValue(self, row, col, value):
        """Set the value of a cell"""
        pass

    def GetColLabelValue(self, col):
        ''' Get the column label.
        '''
        return self.col_labels[col]

    def GetAttr(self, row, col, kind):
        self.format_default.SetBackgroundColour(self.GetView().GetDefaultCellBackgroundColour())
        attr = self.format_default

        attr.SetReadOnly(True)
        attr.IncRef()
        return attr


    def sortColumn(self, col, reverse = False):
        """
        col -> sort the data based on the column indexed by col
        """
        self.data = sorted(self.data, key = itemgetter(col), reverse = reverse)
        self.UpdateValues()


    def ResetView(self):
        """Trim/extend the control's rows and update all values"""
        self.GetView().BeginBatch()
        for current, new, delmsg, addmsg in [
                (self.currentRows, self.GetNumberRows(), wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED),
                (self.currentColumns, self.GetNumberCols(), wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED, wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED),
        ]:
                if new < current:
                        msg = wx.grid.GridTableMessage(
                                self,
                                delmsg,
                                new,    # position
                                current-new,
                        )
                        self.GetView().ProcessTableMessage(msg)
                elif new > current:
                        msg = wx.grid.GridTableMessage(
                                self,
                                addmsg,
                                new-current
                        )
                        self.GetView().ProcessTableMessage(msg)


        self.UpdateValues()
        self.currentRows = self.GetNumberRows()
        self.currentColumns = self.GetNumberCols()
        self.GetView().EndBatch()

        # The scroll bars aren't resized (at least on windows)
        # Jiggling the size of the window rescales the scrollbars
        h,w = self.GetView().GetSize()
        self.GetView().SetSize((h+1, w))
        self.GetView().SetSize((h, w))
        self.GetView().ForceRefresh()


    def UpdateValues( self ):
            """Update all displayed values"""
            msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
            self.GetView().ProcessTableMessage(msg)


def assign_gui_element(pref_item, parent):
    ''' Assign a GUI field to the preferences item.

    '''
    guiclass = gui_elements[pref_item.mode]
    gui_element = guiclass(name = pref_item.label,
                           pref_item = pref_item,
                           size = (100, -1),
                           parent = parent
                          )
    pref_item.set_gui_element(gui_element)


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
gui_elements['datetime'] = DateTimeEditField
gui_elements['checkbox'] = CheckBoxField
gui_elements['list_ctrl'] = ListCtrlEditField
gui_elements['list_grid'] = ListGridEditField

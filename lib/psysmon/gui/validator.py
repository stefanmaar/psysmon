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

import wx


class NotEmptyValidator(wx.PyValidator):
    '''  A dialog field validator which doesn't allow empty field values.
    '''
    def __init__(self):
        ''' Initialize the instance.
        '''
        wx.PyValidator.__init__(self)

        
    def Clone(self):
        ''' The default clone method. 
        '''
        return NotEmptyValidator()


    ## The method run when validating the field.
    #
    # This method checks if the control has a value. If not, it returns False.
    # @param self The object pointer.
    def Validate(self, win):
        ctrl = self.GetWindow()
        value = ctrl.GetValue()

        if len(value) == 0:
            wx.MessageBox("This field must contain some text!", "Error")
            ctrl.SetBackgroundColour("pink")
            ctrl.SetFocus()
            ctrl.Refresh()
            return False
        else:
            ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            ctrl.Refresh()
            return True

    ## The method called when entering the dialog.      
    def TransferToWindow(self):
        return True

    ## The method called when leaving the dialog.  
    def TransferFromWindow(self):
        return True


class IsEqualValidator(wx.PyValidator):
    ''' A dialog field validator which checks for field entry equality.

    This validator can be used to check if the value entered in the field is 
    equal to another one. It's useful when checking for the correct typing of new
    passwords.
    '''

    ## The constructor.
    #
    # @param self The object pointer.
    # @param ctrl2Compare A wx control to which the value of the validated field should be compared.
    def __init__(self, ctrl2Compare):
        ''' Initialize the instance.
        '''
        wx.PyValidator.__init__(self)

        ## The control to which the field to be validated should be compared to.
        self.ctrl2Compare = ctrl2Compare

    ## The default clone method.    
    def Clone(self):
        return IsEqualValidator(self.ctrl2Compare)

    ## The method run when validating the field.
    #
    # This method checks whether the values entered in the two controls are equal
    # or not. 
    # @param self The object pointer.
    def Validate(self, win):
        ctrl = self.GetWindow()
        value = ctrl.GetValue()
        value2Compare = self.ctrl2Compare.GetValue()

        if value != value2Compare:
            wx.MessageBox("The two passwords don't match!", "Error")
            ctrl.SetBackgroundColour("pink")
            ctrl.SetFocus()
            ctrl.Refresh()
            return False
        else:
            ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            ctrl.Refresh()
            return True

    ## The method called when entering the dialog.    
    def TransferToWindow(self):
        return True

    ## The method called when leaving the dialog.
    def TransferFromWindow(self):
        return True


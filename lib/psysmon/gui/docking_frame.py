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

import operator as op

import wx
import wx.lib.agw.ribbon as ribbon

import psysmon
import psysmon.core
import psysmon.gui.view as psy_view
import psysmon.gui.view.viewport
import psysmon.gui.shortcut as psy_shortcut


class DockingFrame(wx.Frame):
    ''' A base class for a frame holding AUI docks.
    '''

    def __init__(self, parent = None, id = wx.ID_ANY,
                 title = 'docking frame', size = (1000, 600)):
        ''' Initialize the instance.
        '''
        wx.Frame.__init__(self,
                          parent = parent,
                          id = id,
                          title = title,
                          pos = wx.DefaultPosition,
                          style = wx.DEFAULT_FRAME_STYLE)
        self.SetMinSize(size)

        # The docking manager.
        self.mgr = wx.aui.AuiManager(self)

        # Initialize the viewport.
        self.init_viewport()

        # Create the menubar.
        self.init_menu_bar()

        #TODO: Add a status bar.
        self.statusbar = DockingFrameStatusBar(self)
        self.statusbar.set_error_log_msg("Last error message.")
        self.SetStatusBar(self.statusbar)

        # The preferences foldpanels.
        self.foldPanels = {}

        # Create the shortcut manager.
        self.shortcut_manager = psy_shortcut.ShortcutManager()

        # Create the plugins shared information bag, which holds all the
        # information, that's shared by the tracedisplay plugins.
        self.plugins_information_bag = psysmon.core.plugins.SharedInformationBag()

        # Create the hook manager and fill it with the allowed hooks.
        self.hook_manager = psysmon.core.util.HookManager(self)

        self.hook_manager.add_hook(name = 'plugin_activated',
                                   description = 'Called after a plugin was activated.',
                                   passed_args = {'plugin_rid': 'The resource id of the plugin.',})
        self.hook_manager.add_hook(name = 'plugin_deactivated',
                                   description = 'Called after a plugin was deactivated.',
                                   passed_args = {'plugin_rid': 'The resource id of the plugin.',})
        self.hook_manager.add_hook(name = 'shared_information_added',
                                   description = 'Called after a shared information was added by a plugin.',
                                   passed_args = {'origin_rid': 'The resource id of the source of the shared information.',
                                                  'name': 'The name of the shared information.'})
        self.hook_manager.add_hook(name = 'shared_information_updated',
                                   description = 'Called after a shared information was added by a plugin.',
                                   passed_args = {'updated_info': 'The shared information instance which was updated.'})
        self.hook_manager.add_view_hook(name = 'button_press_event',
                                        description = 'The matplotlib button_press_event in the view axes.')
        self.hook_manager.add_view_hook(name = 'button_release_event',
                                        description = 'The matplotlib button_release_event in the view axes.')
        self.hook_manager.add_view_hook(name = 'motion_notify_event',
                                        description = 'The matplotlib motion_notify_event in the view axes.')


        self.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)

        
    def on_set_focus(self, event):
        self.logger.debug("on_set_focus in docking frame. event: %s", event)
        event.ResumePropagation(30)
        event.Skip()


    def on_key_down(self, event):
        self.logger.debug("on_key_down in viewport. event: %s", event)
        event.ResumePropagation(30)
        event.Skip()
        

    def init_viewport(self):
        ''' Initialize the viewport.
        '''
        self.center_panel = wx.Panel(parent = self, id = wx.ID_ANY)
        self.viewport_sizer = wx.GridBagSizer()
        self.viewport = psy_view.viewport.Viewport(parent = self.center_panel)
        self.viewport_sizer.Add(self.viewport,
                                pos = (0, 0),
                                flag = wx.EXPAND|wx.ALL,
                                border = 0)
        self.viewport_sizer.AddGrowableRow(0)
        self.viewport_sizer.AddGrowableCol(0)
        self.center_panel.SetSizer(self.viewport_sizer)

        self.mgr.AddPane(self.center_panel,
                         wx.aui.AuiPaneInfo().Name('viewport').CenterPane())


    def init_menu_bar(self):
        ''' Initialize the menu bar.
        '''
        self.menubar = wx.MenuBar()
        menu = wx.Menu()
        item = menu.Append(wx.ID_EXIT)
        self.Bind(event = wx.EVT_MENU,
                  handler = self.on_close,
                  id = item.GetId())
        self.menubar.Append(menu = menu,
                            title = 'File')
        self.SetMenuBar(self.menubar)


    def add_menu(self, title):
        ''' Add a menu to the menu bar.
        '''
        menu_id = self.menubar.FindMenu(title)

        if menu_id == wx.NOT_FOUND:
            menu = wx.Menu()
            self.menubar.Append(menu = menu,
                                title = title)
        else:
            menu = self.menubar.GetMenu(menu_id)

        return menu


    def add_menu_item(self, parent_menu, title,
                      help_string, handler, accelerator_string = None):
        ''' Add a menu item to the menu bar.

        If the parent menu doesn't exist, it is created.
        '''
        menu_id = self.menubar.FindMenu(parent_menu)
        if menu_id != wx.NOT_FOUND:
            menu = self.menubar.GetMenu(menu_id)
            if accelerator_string:
                title += '\t' + accelerator_string
            item = menu.Append(id = wx.ID_ANY,
                               item = title,
                               helpString = help_string)

            self.Bind(event = wx.EVT_MENU,
                      handler = handler,
                      id = item.GetId())

        return item


    def init_menus(self):
        ''' Initialize the menus in the menu bar.
        '''
        self.logger.debug("Initializing the menus.")
        self.menus = {}
        category_list = list(set([x.category for x in self.plugins]))
        category_list = sorted(category_list)
        
        for k, cur_category in enumerate(category_list):
            menu_title = cur_category.capitalize()
            cur_menu = self.add_menu(title = menu_title)
            plugins = [x for x in self.plugins if x.category == cur_category]
            for m, cur_plugin in enumerate(plugins):
                item_id = k * 100 + m
                item_id = wx.NewId()
                self.create_menu_item(menu = cur_menu,
                                      item_id = item_id,
                                      plugin = cur_plugin)
            last_item_id = item_id

            # Handle the preferences of a plugin.
            plugins_with_pref = [x for x in plugins if len(x.pref_manager) > 0]
            # Don't create the preferences menu for option plugins.
            plugins_with_pref = [x for x in plugins_with_pref if x.mode != 'option']
            if plugins_with_pref:
                # Create the preferences submenu.
                cur_menu.AppendSeparator()
                submenu = wx.Menu()
                cur_menu.AppendSubMenu(text = 'Preferences',
                                       submenu = submenu,
                                       help = 'Toggle plugin preferences.')
                
            for m, cur_plugin in enumerate(plugins_with_pref):
                item_id = last_item_id + m + 1
                item_id = wx.NewId()
                self.create_pref_menu_item(menu = submenu,
                                           item_id = item_id,
                                           plugin = cur_plugin)


    def init_plugin_accelerators(self):
        ''' Initialize the shortcuts not related to menu items. 
        '''
        plugins_with_sc = [x for x in self.plugins if x.shortcuts]

        entries = []
        for plugin in plugins_with_sc:
            for key, sc in plugin.shortcuts.items():
                handler = sc['handler']
                accel_string = sc['accelerator_string']
                log_msg = "Registering shortcut {:s} ({:s}).".format(key,
                                                                     accel_string)
                self.logger.debug(log_msg)
                accel_id = wx.NewId()
                self.Bind(wx.EVT_MENU,
                          handler,
                          id = accel_id)
                entry = wx.AcceleratorEntry(cmd = accel_id)
                entry.FromString(accel_string)
                entries.append(entry)

        plugins_with_mac = [x for x in self.plugins if x.accelerator_string]

        # Add the menu accelerator strings to the accelerator table.
        # If not added, the single character accelerators (e.g. Z) don't work
        # as expected).
        for plugin in plugins_with_mac:
            accel_string = plugin.accelerator_string
            log_msg = "Registering accelerator string {:s}.".format(accel_string)
            self.logger.debug(log_msg)
            menu_name = plugin.category.capitalize()
            item_name = plugin.name
            item_id = self.menubar.FindMenuItem(menu_name, item_name)
            entry = wx.AcceleratorEntry(cmd = item_id)
            entry.FromString(accel_string)
            entries.append(entry)

        accel = wx.AcceleratorTable(entries)
        self.SetAcceleratorTable(accel)


    def create_menu_item(self, menu, item_id, plugin):
        ''' Create a menu item for a plugin.
        '''
        if plugin.mode == 'option':
            self.create_option_menu_item(menu = menu,
                                         item_id = item_id,
                                         plugin = plugin)
        elif plugin.mode == 'view':
            self.create_view_menu_item(menu = menu,
                                       item_id = item_id,
                                       plugin = plugin)

        elif plugin.mode == 'command':
            self.create_command_menu_item(menu = menu,
                                          item_id = item_id,
                                          plugin = plugin)

        elif plugin.mode == 'interactive':
            self.create_interactive_menu_item(menu = menu,
                                              item_id = item_id,
                                              plugin = plugin)
            

            
    def create_pref_menu_item(self, menu, item_id, plugin):
        ''' Create a plugin preferences menu item in a submenu.
        '''
        help_msg = "Preferences for the {:s} plugin.".format(plugin.name)
        title = plugin.name
        if plugin.pref_accelerator_string:
            title += '\t' + plugin.pref_accelerator_string
            
        #menu.Append(id = item_id,
        #            item = title,
        #            helpString = help_msg)

        menu.AppendCheckItem(id = item_id,
                             item = title,
                             help = help_msg)

        self.Bind(event = wx.EVT_MENU,
                  handler = lambda evt, plugin=plugin: self.on_edit_tool_preferences(evt,
                                                                                     plugin),
                  id = item_id)

        
    def create_command_menu_item(self, menu, item_id, plugin):
        ''' Create a commund plugin menu item.
        '''
        help_msg = plugin.name
        title = plugin.name
        if plugin.accelerator_string:
            title += '\t' + plugin.accelerator_string

        menu.Append(id = item_id,
                    item = title,
                    helpString = help_msg)

        self.Bind(event = wx.EVT_MENU,
                  handler = lambda evt, plugin = plugin: self.on_mb_command_tool_clicked(evt,
                                                                                         plugin),
                  id = item_id)
            

    def create_option_menu_item(self, menu, item_id, plugin):
        ''' Create an option menu item.
        '''
        title = plugin.name
        if plugin.accelerator_string:
            title += '\t' + plugin.accelerator_string
        log_msg = ("Creating menu {:s}. item_id: {:d}".format(title,
                                                              item_id))
        self.logger.debug(log_msg)
        menu.AppendCheckItem(id = item_id,
                             item = title,
                             help = plugin.name)
        self.Bind(event = wx.EVT_MENU,
                  handler = lambda evt, plugin = plugin: self.on_mb_option_tool_clicked(evt,
                                                                                        plugin),
                  id = item_id)


    def create_view_menu_item(self, menu, item_id, plugin):
        ''' Create a view plugin menu item.
        '''
        title = plugin.name
        if plugin.accelerator_string:
            title += '\t' + plugin.accelerator_string
        menu.AppendCheckItem(id = item_id,
                             item = title,
                             help = plugin.name)
        self.Bind(event = wx.EVT_MENU,
                  handler = lambda evt, plugin = plugin: self.on_mb_view_tool_clicked(evt,
                                                                                      plugin),
                  id = item_id)


    def create_interactive_menu_item(self, menu, item_id, plugin):
        ''' Create an interactive plugin menu item.
        '''
        title = plugin.name
        if plugin.accelerator_string:
            title += '\t' + plugin.accelerator_string
        help_msg = plugin.name
        menu.AppendCheckItem(id = item_id,
                             item = title,
                             help = help_msg)
        self.Bind(event = wx.EVT_MENU,
                  handler = lambda evt, plugin = plugin: self.on_mb_interactive_tool_clicked(evt,
                                                                                             plugin),
                  id = item_id)


    def init_ribbon_pane(self):
        ''' Initialize the aui manager pane for the ribbon bar.
        '''
        self.mgr.AddPane(self.ribbon,
                         wx.aui.AuiPaneInfo().Top().
                         Name('palette').
                         Caption('palette').
                         Layer(1).
                         Row(0).
                         Position(0).
                         BestSize(wx.Size(-1, 50)).
                         MinSize(wx.Size(-1, 80)).
                         CloseButton(False))



    def init_ribbon_bar(self):
        ''' Initialize the ribbon bar with the plugins.
        '''
        # Build the ribbon bar based on the plugins.
        # First create all the pages according to the category.
        self.ribbonPages = {}
        self.ribbonPanels = {}
        self.ribbonToolbars = {}
        for curGroup, curCategory in sorted([(x.group, x.category) for x in self.plugins], key = op.itemgetter(0, 1)):
            if curGroup not in iter(self.ribbonPages.keys()):
                self.logger.debug('Creating page %s', curGroup)
                self.ribbonPages[curGroup] = ribbon.RibbonPage(self.ribbon, wx.ID_ANY, curGroup)

            if curCategory not in iter(self.ribbonPanels.keys()):
                self.ribbonPanels[curCategory] = ribbon.RibbonPanel(self.ribbonPages[curGroup],
                                                                    wx.ID_ANY,
                                                                    curCategory,
                                                                    wx.NullBitmap,
                                                                    wx.DefaultPosition,
                                                                    wx.DefaultSize,
                                                                    agwStyle=ribbon.RIBBON_PANEL_NO_AUTO_MINIMISE)
                # TODO: Find out what I wanted to do with these lines!?!
                if curCategory == 'interactive':
                    self.ribbonToolbars[curCategory] = ribbon.RibbonToolBar(self.ribbonPanels[curCategory], 1)
                else:
                    self.ribbonToolbars[curCategory] = ribbon.RibbonToolBar(self.ribbonPanels[curCategory], 1)


        # Fill the ribbon bar with the plugin buttons.
        option_plugins = [x for x in self.plugins if x.mode == 'option']
        command_plugins = [x for x in self.plugins if x.mode == 'command']
        interactive_plugins = [x for x in self.plugins if x.mode == 'interactive']
        view_plugins = [x for x in self.plugins if x.mode == 'view']
        id_counter = 0

        for curPlugin in sorted(option_plugins, key = op.attrgetter('position_pref', 'name')):
                # Create a tool.
                curTool = self.ribbonToolbars[curPlugin.category].AddTool(tool_id = id_counter, 
                                                                          bitmap = curPlugin.icons['active'].GetBitmap(), 
                                                                          help_string = curPlugin.name,
                                                                          kind = ribbon.RIBBON_BUTTON_TOGGLE)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED, 
                                                             lambda evt, curPlugin=curPlugin : self.on_option_tool_clicked(evt, curPlugin), id=curTool.id)
                id_counter += 1

        for curPlugin in sorted(command_plugins, key = op.attrgetter('position_pref', 'name')):
                # Create a HybridTool or a normal tool if no preference items
                # are available. The dropdown menu allows to open
                # the tool parameters in a foldpanel.
                if len(curPlugin.pref_manager) == 0:
                    curTool = self.ribbonToolbars[curPlugin.category].AddTool(tool_id = id_counter,
                                                                              bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                              help_string = curPlugin.name)
                else:
                    curTool = self.ribbonToolbars[curPlugin.category].AddHybridTool(tool_id = id_counter,
                                                                                    bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                                    help_string = curPlugin.name)
                    self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_DROPDOWN_CLICKED,
                                                                 lambda evt, curPlugin=curPlugin: self.on_command_tool_dropdown_clicked(evt, curPlugin),
                                                                 id=curTool.id)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED,
                                                             lambda evt, curPlugin=curPlugin : self.on_command_tool_clicked(evt, curPlugin),
                                                             id=curTool.id)
                id_counter += 1


        for curPlugin in sorted(interactive_plugins, key = op.attrgetter('position_pref', 'name')):
                # Create a HybridTool. The dropdown menu allows to open
                # the tool parameters in a foldpanel.
                if len(curPlugin.pref_manager) == 0:
                    curTool = self.ribbonToolbars[curPlugin.category].AddTool(tool_id = id_counter,
                                                                              bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                              help_string = curPlugin.name)
                else:
                    curTool = self.ribbonToolbars[curPlugin.category].AddHybridTool(tool_id = id_counter,
                                                                                    bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                                    help_string = curPlugin.name)
                    self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_DROPDOWN_CLICKED,
                                                                 lambda evt, curPlugin=curPlugin: self.on_interactive_tool_dropdown_clicked(evt, curPlugin),
                                                                 id=curTool.id)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED,
                                                             lambda evt, curPlugin=curPlugin : self.on_interactive_tool_clicked(evt, curPlugin),
                                                             id=curTool.id)
                id_counter += 1

        for curPlugin in sorted(view_plugins, key = op.attrgetter('position_pref', 'name')):
                # Create a HybridTool or a normal tool if no preference items
                # are available. The dropdown menu allows to open
                # the tool parameters in a foldpanel.
                if len(curPlugin.pref_manager) == 0:
                    curTool = self.ribbonToolbars[curPlugin.category].AddTool(tool_id = id_counter,
                                                                              bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                              help_string = curPlugin.name)

                else:
                    curTool = self.ribbonToolbars[curPlugin.category].AddHybridTool(tool_id = id_counter,
                                                                                    bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                                    help_string = curPlugin.name)
                    self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_DROPDOWN_CLICKED,
                                                                 lambda evt, curPlugin=curPlugin: self.on_view_tool_dropdown_clicked(evt, curPlugin),
                                                                 id=curTool.id)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED,
                                                             lambda evt, curPlugin=curPlugin : self.on_view_tool_clicked(evt, curPlugin),
                                                             id=curTool.id)
                id_counter += 1


        self.ribbon.Realize()


    def on_close(self, event):
        ''' Close the window.
        '''
        # deinitialize the frame manager
        self.mgr.UnInit()
        
        # delete the frame
        self.Destroy()
        
        
    def on_mb_command_tool_clicked(self, event, plugin):
        ''' Handle the click of a command plugin toolbar button.

        Activate the tool.
        '''
        self.logger.debug('Clicked the command tool: %s', plugin.name)
        plugin.run()


    def on_mb_option_tool_clicked(self, event, plugin):
        ''' Handle the click of an option plugin toolbar button.

        Show or hide the foldpanel of the plugin.
        '''
        self.logger.debug('Clicked the menubar option tool: %s', plugin.name)

        menu_id = event.GetId()
        menu_item = self.menubar.FindItemById(menu_id)

        # The panel of the option tool does't exist. Create it and add
        # it to the panel manager.
        if plugin.name not in iter(self.foldPanels.keys()):
            self.logger.debug("Creating the foldpanel.")
            curPanel = plugin.buildFoldPanel(self)
            self.mgr.AddPane(curPanel,
                             wx.aui.AuiPaneInfo().Right().
                             Name(plugin.name).
                             Caption(plugin.name).
                             Layer(2).
                             Row(0).
                             Position(0).
                             BestSize(wx.Size(300, -1)).
                             MinSize(wx.Size(200, 100)).
                             MinimizeButton(True).
                             MaximizeButton(True))
            self.Bind(event = wx.aui.EVT_AUI_PANE_CLOSE,
                      handler = lambda evt, plugin = plugin: self.on_optiontool_aui_pane_close(evt,
                                                                                               plugin))
            self.mgr.GetPane(curPanel).Hide()
            # TODO: Add a onOptionToolPanelClose method to handle clicks of
            # the CloseButton in the AUI pane of the option tools. If the
            # pane is closed, the toggle state of the ribbonbar button has
            # be changed. The according event is aui.EVT_AUI_PANE_CLOSE.
            self.mgr.Update()
            self.foldPanels[plugin.name] = curPanel
 
        if not self.foldPanels[plugin.name].IsShown():
            self.logger.debug("Showing the foldpanel.")
            curPanel = self.foldPanels[plugin.name]
            self.mgr.GetPane(curPanel).Show()
            self.mgr.Update()
            plugin.activate()
            self.check_menu_checkitem(plugin)
            self.call_hook('plugin_activated', plugin_rid = plugin.rid)
        else:
            self.logger.debug("Hiding the foldpanel.")
            curPanel = self.foldPanels[plugin.name]
            self.mgr.GetPane(curPanel).Hide()
            self.mgr.Update()
            plugin.deactivate()
            self.uncheck_menu_checkitem(plugin)
            self.call_hook('plugin_deactivated', plugin_rid = plugin.rid)


    def on_mb_view_tool_clicked(self, event, plugin):
        ''' Handle the click of an view plugin toolbar button.

        Activate the tool.
        '''
        self.logger.debug('Clicked the view tool: %s', plugin.name)

        if plugin.active is True:
            plugin.deactivate()
            self.uncheck_menu_checkitem(plugin)
            self.call_hook('plugin_deactivated', plugin_rid = plugin.rid)
            self.unregister_view_plugin(plugin)
        else:
            plugin.activate()
            self.check_menu_checkitem(plugin)
            self.call_hook('plugin_activated', plugin_rid = plugin.rid)
            self.register_view_plugin(plugin)

        self.viewport.Refresh()
        self.viewport.Update()

        self.update_display()


    def on_mb_interactive_tool_clicked(self, event, plugin):
        ''' Handle the click of an interactive plugin toolbar button.

        Activate the tool.
        '''
        menu_id = event.GetId()
        menu_item = self.menubar.FindItemById(menu_id)
        menu_item.Check()
        active_plugin = [x for x in self.plugins if x.active is True and x.mode == 'interactive']
        if len(active_plugin) > 1:
            raise RuntimeError('Only one interactive tool can be active.')
        elif len(active_plugin) == 1:
            active_plugin = active_plugin[0]
            self.uncheck_menu_checkitem(active_plugin)
            self.deactivate_interactive_plugin(active_plugin)
        self.activate_interactive_plugin(plugin)
        self.check_menu_checkitem(plugin)


    def get_menu_item(self, plugin):
        ''' Get the menu item of a plugin. 
        '''
        menu_item = None
        menu_title = plugin.category.capitalize()
        cat_menu_id = self.menubar.FindMenu(menu_title)
        cat_menu = self.menubar.GetMenu(cat_menu_id)

        if cat_menu:
            menu_item_id = cat_menu.FindItem(plugin.name)
            menu_item = cat_menu.FindItemById(menu_item_id)

        return menu_item


    def get_pref_menu_item(self, plugin):
        ''' Get the preferences menu item of a plugin. 
        '''
        menu_item = None
        menu_title = plugin.category.capitalize()
        cat_menu_id = self.menubar.FindMenu(menu_title)
        cat_menu = self.menubar.GetMenu(cat_menu_id)

        if cat_menu:
            pref_title = 'Preferences'
            pref_menu_id = cat_menu.FindItem(pref_title)
            pref_menu_item = cat_menu.FindItemById(pref_menu_id)
            pref_menu = pref_menu_item.GetSubMenu()
            if pref_menu:
                menu_item_id = pref_menu.FindItem(plugin.name)
                menu_item = pref_menu.FindItemById(menu_item_id)

        return menu_item


    def check_menu_checkitem(self, plugin):
        ''' Uncheck a menu checkitem related to a plugin.
        '''
        menu_item = self.get_menu_item(plugin)
        if menu_item:
            menu_item.Check()
            
    def uncheck_menu_checkitem(self, plugin):
        ''' Uncheck a menu checkitem related to a plugin.
        '''
        menu_item = self.get_menu_item(plugin)
        if menu_item:
            menu_item.Check(False)


    def check_pref_menu_checkitem(self, plugin):
        ''' Uncheck a preferences menu checkitem related to a plugin.
        '''
        menu_item = self.get_pref_menu_item(plugin)
        if menu_item:
            menu_item.Check()


    def uncheck_pref_menu_checkitem(self, plugin):
        ''' Uncheck a preferences menu checkitem related to a plugin.
        '''
        menu_item = self.get_pref_menu_item(plugin)
        if menu_item:
            menu_item.Check(False)


    def on_option_tool_clicked(self, event, plugin):
        ''' Handle the click of an option plugin toolbar button.

        Show or hide the foldpanel of the plugin.
        '''
        self.logger.debug('Clicked the option tool: %s', plugin.name)

        cur_toolbar = event.GetEventObject()
        if cur_toolbar.GetToolState(event.GetId()) != ribbon.RIBBON_TOOLBAR_TOOL_TOGGLED:
            if plugin.name not in iter(self.foldPanels.keys()):
                # The panel of the option tool does't exist. Create it and add
                # it to the panel manager.
                curPanel = plugin.buildFoldPanel(self)
                self.mgr.AddPane(curPanel,
                                 wx.aui.AuiPaneInfo().Right().
                                 Name(plugin.name).
                                 Caption(plugin.name).
                                 Layer(2).
                                 Row(0).
                                 Position(0).
                                 BestSize(wx.Size(300, -1)).
                                 MinSize(wx.Size(200, 100)).
                                 MinimizeButton(True).
                                 MaximizeButton(True).
                                 CloseButton(False))
                # TODO: Add a onOptionToolPanelClose method to handle clicks of
                # the CloseButton in the AUI pane of the option tools. If the
                # pane is closed, the toggle state of the ribbonbar button has
                # be changed. The according event is aui.EVT_AUI_PANE_CLOSE.
                self.mgr.Update()
                self.foldPanels[plugin.name] = curPanel
            else:
                if not self.foldPanels[plugin.name].IsShown():
                    curPanel = self.foldPanels[plugin.name]
                    self.mgr.GetPane(curPanel).Show()
                    self.mgr.Update()
            plugin.activate()
            self.call_hook('plugin_activated', plugin_rid = plugin.rid)
        else:
            if self.foldPanels[plugin.name].IsShown():
                curPanel = self.foldPanels[plugin.name]
                self.mgr.GetPane(curPanel).Hide()
                self.mgr.Update()

            plugin.deactivate()
            self.call_hook('plugin_deactivated', plugin_rid = plugin.rid)




    def on_command_tool_clicked(self, event, plugin):
        ''' Handle the click of a command plugin toolbar button.

        Activate the tool.
        '''
        self.logger.debug('Clicked the command tool: %s', plugin.name)
        plugin.run()


    def on_command_tool_dropdown_clicked(self, event, plugin):
        ''' Handle the click on the dropdown button of an command plugin toolbar button.

        '''
        menu = wx.Menu()
        item = menu.Append(wx.ID_ANY, "edit preferences")
        self.Bind(wx.EVT_MENU, lambda evt, plugin=plugin: self.on_edit_tool_preferences(evt, plugin), item)
        event.PopupMenu(menu)



    def on_interactive_tool_clicked(self, event, plugin):
        ''' Handle the click of an interactive plugin toolbar button.

        Activate the tool.
        '''
        active_plugin = [x for x in self.plugins if x.active is True and x.mode == 'interactive']
        if len(active_plugin) > 1:
            raise RuntimeError('Only one interactive tool can be active.')
        elif len(active_plugin) == 1:
            active_plugin = active_plugin[0]
            self.deactivate_interactive_plugin(active_plugin)
        self.activate_interactive_plugin(plugin)


    def on_interactive_tool_dropdown_clicked(self, event, plugin):
        ''' Handle the click on the dropdown button of an interactive plugin toolbar button.

        '''
        menu = wx.Menu()
        item = menu.Append(wx.ID_ANY, "edit preferences")
        self.Bind(wx.EVT_MENU, lambda evt, plugin=plugin: self.on_edit_tool_preferences(evt, plugin), item)
        event.PopupMenu(menu)


    def activate_interactive_plugin(self, plugin):
        ''' Activate an interactive plugin.
        '''
        plugin.activate()
        if plugin.active:
            if plugin.cursor is not None:
                if isinstance(plugin.cursor, wx.lib.embeddedimage.PyEmbeddedImage):
                    image = plugin.cursor.GetImage()
                    # since this image didn't come from a .cur file, tell it where the hotspot is
                    img_size = image.GetSize()
                    image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_X, img_size[0] * plugin.cursor_hotspot[0])
                    image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_Y, img_size[1] * plugin.cursor_hotspot[1])

                    # make the image into a cursor
                    self.viewport.SetCursor(wx.CursorFromImage(image))
                else:
                    try:
                        self.viewport.SetCursor(wx.StockCursor(plugin.cursor))
                    except Exception:
                        pass

            self.logger.debug('Clicked the interactive tool: %s', plugin.name)

            # Get the hooks and register the matplotlib hooks in the viewport.
            hooks = plugin.getHooks()
            allowed_matplotlib_hooks = iter(self.hook_manager.view_hooks.keys())

            for cur_key in [x for x in hooks.keys() if x not in allowed_matplotlib_hooks]:
                del hooks[cur_key]

            # Set the callbacks of the views.
            self.viewport.clear_mpl_event_callbacks()
            self.viewport.register_mpl_event_callbacks(hooks)
            self.call_hook('plugin_activated', plugin_rid = plugin.rid)
            self.statusbar.set_interactive_tool_msg(plugin.name)
            shortcuts = self.shortcut_manager.get_shortcut(origin_rid = plugin.rid)
            status_msg = ','.join(['+'.join(x.key_combination) for x in shortcuts])
            status_msg = 'tool shortcuts: ' + status_msg
            self.statusbar.set_shortcut_tips_msg(status_msg)


    def deactivate_interactive_plugin(self, plugin):
        ''' Deactivate an interactive plugin.
        '''
        if plugin.mode != 'interactive':
            return
        self.viewport.clear_mpl_event_callbacks()
        self.viewport.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        plugin.deactivate()
        self.shortcut_manager.remove_shortcut(origin_rid = plugin.rid)
        self.call_hook('plugin_deactivated', plugin_rid = plugin.rid)
        self.statusbar.set_interactive_tool_msg("no tool active")
        self.statusbar.set_shortcut_tips_msg('')


    def on_edit_tool_preferences(self, event, plugin):
        ''' Handle the edit preferences dropdown click.

        '''
        self.logger.debug('Dropdown clicked -> editing preferences.')

        if plugin.name not in iter(self.foldPanels.keys()):
            #curPanel = plugin.buildFoldPanel(self.foldPanelBar)
            #foldPanel = self.foldPanelBar.addPanel(curPanel, plugin.icons['active'])

            curPanel = plugin.buildFoldPanel(self)
            self.mgr.AddPane(curPanel,
                             wx.aui.AuiPaneInfo().Right().
                                                  Name(plugin.name).
                                                  Caption(plugin.name).
                                                  Layer(2).
                                                  Row(0).
                                                  Position(0).
                                                  BestSize(wx.Size(300, -1)).
                                                  MinSize(wx.Size(200, 100)).
                                                  MinimizeButton(True).
                                                  MaximizeButton(True))
            self.Bind(event = wx.aui.EVT_AUI_PANE_CLOSE,
                      handler = lambda evt, plugin = plugin: self.on_pref_aui_pane_close(evt,
                                                                                         plugin))
            self.mgr.Update()
            self.foldPanels[plugin.name] = curPanel
        else:
            if not self.foldPanels[plugin.name].IsShown():
                curPanel = self.foldPanels[plugin.name]
                self.mgr.GetPane(curPanel).Show()
                self.mgr.Update()


    def on_pref_aui_pane_close(self, event, plugin):
        ''' Handle the closing of a plugins panel.
        '''
        self.uncheck_pref_menu_checkitem(plugin)


    def on_optiontool_aui_pane_close(self, event, plugin):
        ''' Handle the closing of a plugins panel.
        '''
        self.uncheck_menu_checkitem(plugin)


    def on_view_tool_clicked(self, event, plugin):
        ''' Handle the click of an view plugin toolbar button.

        Activate the tool.
        '''
        self.logger.debug('Clicked the view tool: %s', plugin.name)

        if plugin.active == True:
            plugin.deactivate()
            self.call_hook('plugin_deactivated', plugin_rid = plugin.rid)
            self.unregister_view_plugin(plugin)
        else:
            plugin.activate()
            self.call_hook('plugin_activated', plugin_rid = plugin.rid)
            self.register_view_plugin(plugin)

        self.viewport.Refresh()
        self.viewport.Update()

        self.update_display()


    def on_view_tool_dropdown_clicked(self, event, plugin):
        ''' Handle the click on the dropdown button of an view plugin toolbar button.

        '''
        self.logger.debug('Clicked the view tool dropdown button: %s', plugin.name)
        menu = wx.Menu()
        item = menu.Append(wx.ID_ANY, "edit preferences")
        self.Bind(wx.EVT_MENU, lambda evt, plugin=plugin: self.on_edit_tool_preferences(evt, plugin), item)
        event.PopupMenu(menu)


    def call_hook(self, hook_name, **kwargs):
        ''' Call the hook of the plugins.
        '''
        # TODO: Think about calling the hooks of all plugins, even if they are
        # not activated. This would keep track of changes within deactivated
        # plugins. It might cause some troubles with plugins, for which the
        # fold panel was not yet created, check this.
        active_plugins = [x for x in self.plugins if x.active or x.mode == 'command']
        self.hook_manager.call_hook(receivers = active_plugins,
                                    hook_name = hook_name,
                                    **kwargs)


    def add_shared_info(self, origin_rid, name, value):
        ''' Add a shared information.

        Parameters
        ----------
        origin_rid : String
            The resource ID of the origin of the information.

        name : String
            The name of the shared information

        value : Dictionary
            The value of the shared information
        '''
        self.plugins_information_bag.add_info(origin_rid = origin_rid,
                                              name = name,
                                              value = value)
        self.call_hook('shared_information_added',
                       origin_rid = origin_rid,
                       name = name)


    def notify_shared_info_change(self, updated_info):
        ''' Notify tracedisplay, that a shared informtion was changed.
        '''
        self.call_hook('shared_information_updated',
                       updated_info = updated_info)


    def get_shared_info(self, **kwargs):
        ''' Get a shared information.

        Parameters
        ----------
        origin_rid : String
            The resource ID of the origin of the information.

        name : String
            The name of the shared information
        '''
        return self.plugins_information_bag.get_info(**kwargs)


    def register_view_plugin(self, plugin):
        ''' Method to handle plugin requests.

        Overwrite this method to react to special requirements needed by the plugin.
        E.g. create virtual channels in the tracedisplay.
        '''
        self.viewport.register_view_plugin(plugin)


    def unregister_view_plugin(self, plugin):
        ''' Method to handle plugin requests.

        Overwrite this method to react to special requirements needed by the plugin.
        E.g. create virtual channels in the tracedisplay.
        '''
        self.viewport.remove_node(name = plugin.rid, recursive = True)



class DockingFrameStatusBar(wx.StatusBar):

    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent, -1)


        # This status bar has three fields
        self.SetFieldsCount(3)
        # Sets the three fields to be relative widths to each other.
        self.SetStatusWidths([-3, -3, -1])
        # Create sunken fields.
        wx.SB_SUNKEN = 3
        self.SetStatusStyles([wx.SB_SUNKEN, wx.SB_SUNKEN, wx.SB_SUNKEN])

        self.error_log_pos = 0
        self.shortcut_tips_pos = 1
        self.interactive_tool_pos = 2


    def set_error_log_msg(self, msg):
        ''' Set the message of the error log tool area.
        '''
        self.SetStatusText(msg, self.error_log_pos)


    def set_shortcut_tips_msg(self, msg):
        ''' Set the message of the shortcut tips area.
        '''
        self.SetStatusText(msg, self.shortcut_tips_pos)


    def set_interactive_tool_msg(self, msg):
        ''' Set the message of the interactive tool area.
        '''
        self.SetStatusText(msg, self.interactive_tool_pos)

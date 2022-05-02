'''
Created on May 17, 2011

@author: Stefan Mertl
'''
from __future__ import print_function

import logging
import unittest
import nose.plugins.attrib as nose_attrib
import wx

import psysmon
import psysmon.gui.view as psy_view
import psysmon.gui.main.app as psy_app



@nose_attrib.attr('interactive')
class ViewportTestCase(unittest.TestCase):
    '''
    '''

    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel('DEBUG')
        logger.addHandler(psysmon.getLoggerHandler(log_level = 'DEBUG'))


    @classmethod
    def tearDownClass(cls):
        print("....in tearDownClass.\n")


    def setUp(self):
        self.app = psy_app.PsysmonApp()
        self.app.Init()                 # The widget inspection tool can be called using CTRL+ALT+i


    def tearDown(self):
        pass

    def test_simple_viewport(self):
        ''' Test a simple viewport with two containers and one view in each container.
        '''
        frame = wx.Frame(parent = None)

        # Create the first container.
        viewport = psy_view.viewport.Viewport(parent = frame)
        container_node = psy_view.containernode.ContainerNode(name = "Container 1",
                                                             parent = viewport)
        viewport.add_node(container_node)


        # Create the second container.
        view_container_node = psy_view.view_containernode.ViewContainerNode(name = "View Container 2",
                                                             parent = viewport)
        viewport.add_node(view_container_node)

        # Add a view to the container.
        view_node = psy_view.viewnode.ViewNode(name = "View C2",
                                               parent = view_container_node,
                                               color = 'red')
        view_container_node.add_node(view_node)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(viewport, 1, flag = wx.EXPAND|wx.TOP|wx.BOTTOM, border = 1)
        frame.SetSizer(sizer)

        frame.Show(True)
        self.app.MainLoop()


    def test_nested_viewport(self):
        ''' Test the creation of the dialog window.
        '''
        frame = wx.Frame(parent = None)

        # Create a container.
        viewport = psy_view.viewport.Viewport(parent = frame)
        container_node = psy_view.view_containernode.ViewContainerNode(name = "Container 1",
                                                             parent = viewport)
        viewport.add_node(container_node)

        # Add a view to the container.
        view_node = psy_view.viewnode.ViewNode(name = "View C1",
                                               parent = container_node,
                                               color = 'green')
        container_node.add_node(view_node)


        container_node = psy_view.containernode.ContainerNode(name = "Container 2",
                                                             parent = viewport)
        viewport.add_node(container_node)

        child_node = psy_view.view_containernode.ViewContainerNode(name = "Child Container 1",
                                                             parent = container_node,
                                                             color = 'yellow')
        container_node.add_node(child_node)

        # Add a view to the container to the first child node.
        view_node = psy_view.viewnode.ViewNode(name = "View 1 Child C1",
                                               parent = container_node,
                                               color = 'green')
        child_node.add_node(view_node)

        child_node = psy_view.view_containernode.ViewContainerNode(name = "Child Container 2",
                                                             parent = container_node,
                                                             color = 'green')
        container_node.add_node(child_node)

        # Add a view to the container to the second child node.
        view_node = psy_view.viewnode.ViewNode(name = "View 1 Child C2",
                                               parent = container_node,
                                               color = 'green')
        child_node.add_node(view_node)

        # Add a view to the container to the second child node.
        view_node = psy_view.viewnode.ViewNode(name = "View 2 Child C2",
                                               parent = container_node,
                                               color = 'green')
        child_node.add_node(view_node)


        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(viewport, 1, flag = wx.EXPAND|wx.TOP|wx.BOTTOM, border = 1)
        frame.SetSizer(sizer)

        frame.Show(True)
        self.app.MainLoop()



def suite():
    return unittest.makeSuite(ViewportTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')


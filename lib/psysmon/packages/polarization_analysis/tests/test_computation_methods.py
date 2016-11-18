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

import unittest

import logging
import os

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

import psysmon
import psysmon.packages.polarization_analysis.core as core
import psysmon.core.signal

class ComputationMethods(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """

    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        cls.logger = logging.getLogger('psysmon')
        cls.logger.setLevel('DEBUG')
        cls.logger.addHandler(psysmon.getLoggerHandler())

        # Create the test signal.
        sps = 100.
        f = 10.
        t = np.arange(0,5, 1/sps)
        win = psysmon.core.signal.tukey(len(t), 0.3)
        x_linear = np.sin(2 * np.pi * f * t) * win
        y_linear = np.zeros(len(x_linear))
        z_linear = x_linear.copy()

        x_circ = np.sin(2 * np.pi * f * t) * win
        y_circ = np.zeros(x_circ.shape)
        z_circ = np.sin(2 * np.pi * f * t + np.pi/2.) * win

        x_ellip = np.sin(2 * np.pi * f * t + np.pi/4.) * win
        y_ellip = np.zeros(x_ellip.shape)
        z_ellip = np.cos(2 * np.pi * f * t) * win


        x_toro = np.sin(2 * np.pi * f * t) * win
        y_toro = np.cos(2 * np.pi * f * t) * win
        z_toro = np.sin(2 * np.pi * 40. * t) * win

        x_rand = np.random.rand(len(t))
        x_rand = x_rand - np.mean(x_rand)
        x_rand = x_rand / np.abs(x_rand)
        y_rand = np.random.rand(len(t))
        y_rand = y_rand - np.mean(y_rand)
        y_rand = y_rand / np.abs(y_rand)
        z_rand = np.random.rand(len(t))
        z_rand = z_rand - np.mean(z_rand)
        z_rand = z_rand / np.abs(z_rand)

        cls.signal_x = np.hstack((x_linear, x_circ, x_ellip, x_toro, x_rand))
        cls.signal_y = np.hstack((y_linear, y_circ, y_ellip, y_toro, y_rand))
        cls.signal_z = np.hstack((z_linear, z_circ, z_ellip, z_toro, z_rand))
        cls.time = np.arange(0, len(cls.signal_x) / sps, 1/sps)

        #fig = plt.figure()
        #ax = fig.add_subplot(111, projection = '3d')
        #ax.plot(x_circ, y_circ, z_circ)
        #ax.set_xlim(-1,1)
        #ax.set_ylim(-1,1)
        #ax.set_zlim(-1,1)
        #plt.show()


    def setUp(self):
        pass

    def tearDown(self):
        print "Es war sehr schoen - auf Wiederseh'n.\n"


    def test_covariance_matrix(self):
        ''' Test the covariance matrix method.
        '''
        component_data = {}
        component_data['x'] = self.signal_x
        component_data['y'] = self.signal_y
        component_data['z'] = self.signal_z
        component_data['time'] = self.time
        features = core.compute_covariance_matrix(component_data, 30, 0.9)

        fig = plt.figure()
        ax = fig.add_subplot(7,1,1)
        ax.plot(self.time, self.signal_x)
        ax.plot(self.time, self.signal_y)
        ax.plot(self.time, self.signal_z)

        ax = fig.add_subplot(7,1,2)
        ax.plot(features['time'], features['linearity'])
        ax.set_ylabel('linearity')

        ax = fig.add_subplot(7,1,3)
        ax.plot(features['time'], features['planarity'])
        ax.set_ylabel('planarity')

        ax = fig.add_subplot(7,1,4)
        ax.plot(features['time'], features['pol_strength'])
        ax.set_ylabel('pol_strength')

        ax = fig.add_subplot(7,1,5)
        ax.plot(features['time'], features['azimuth'], 'x')
        ax.set_ylabel('azimuth')

        ax = fig.add_subplot(7,1,6)
        ax.plot(features['time'], features['incidence'], 'x')
        ax.set_ylabel('incidence')

        ax = fig.add_subplot(7,1,7)
        ax.plot(features['time'], features['eigenval'][:,0], 'kx-')
        ax.plot(features['time'], features['eigenval'][:,1], 'ro-')
        ax.plot(features['time'], features['eigenval'][:,2], 'gs-')
        ax.set_ylabel('eigenval')
        plt.show()

    def test_complex_covariance_matrix(self):
        ''' Test the complex covariance matrix method.
        '''

        component_data = {}
        component_data['x'] = self.signal_x
        component_data['y'] = self.signal_y
        component_data['z'] = self.signal_z
        component_data['time'] = self.time
        features = core.compute_complex_covariance_matrix_windowed(component_data, 30, 0.9)

        fig = plt.figure()
        ax = fig.add_subplot(6,1,1)
        ax.plot(self.time, self.signal_x)
        ax.plot(self.time, self.signal_y)
        ax.plot(self.time, self.signal_z)

        ax = fig.add_subplot(6,1,2)
        ax.plot(features['time'], features['ellipticity'])
        ax.set_ylabel('ellipticity')

        ax = fig.add_subplot(6,1,3)
        ax.plot(features['time'], features['pol_strength'])
        ax.set_ylabel('pol_strength')

        ax = fig.add_subplot(6,1,4)
        ax.plot(features['time'], features['azimuth'], 'x')
        ax.set_ylabel('azimuth')

        ax = fig.add_subplot(6,1,5)
        ax.plot(features['time'], features['incidence'], 'x')
        ax.set_ylabel('incidence')
        ax.set_ylim([0, np.pi/2.])

        ax = fig.add_subplot(6,1,6)
        ax.plot(features['time'], features['eigenval'][:,0], 'kx-')
        ax.plot(features['time'], features['eigenval'][:,1], 'ro-')
        ax.plot(features['time'], features['eigenval'][:,2], 'gs-')
        ax.set_ylabel('eigenval')
        plt.show()




def suite():
    return unittest.makeSuite(ComputationMethods, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')


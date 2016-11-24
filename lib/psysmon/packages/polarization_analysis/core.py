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


import psysmon.core.signal

import numpy as np
import scipy
import scipy.signal

def compute_covariance_matrix(component_data, window_length, overlap):
    ''' Compute the polarization features using the covariance matrix method.
    '''

    time_array = component_data['time']
    x_data = np.array(component_data['x'])
    y_data = np.array(component_data['y'])
    z_data = np.array(component_data['z'])

    sample_win = psysmon.core.signal.tukey(window_length, 0.01)
    win_step = np.floor(window_length - (window_length * overlap))
    n_win = np.floor( (len(z_data) - window_length) / win_step)

    features = {}
    features['time'] = []
    features['linearity'] = []
    features['planarity'] = []
    features['pol_strength'] = []
    features['azimuth'] = []
    features['incidence'] = []
    features['eigenval'] = []
    for k in np.arange(n_win + 1):
        start_ind = int(k * win_step)
        end_ind = int(start_ind + window_length)

        cur_x_data = x_data[start_ind:end_ind] * sample_win
        cur_y_data = y_data[start_ind:end_ind] * sample_win
        cur_z_data = z_data[start_ind:end_ind] * sample_win

        features['time'].append(time_array[np.floor((start_ind + end_ind)/2.)])

        # Create the data matrix and compute the covariance matrix.
        D = np.vstack((cur_x_data, cur_y_data, cur_z_data))
        M = np.cov(D)

        # Compute the singular values using the singular value decomposition.
        # The columns of U are the eigenvectors.
        # The eigenvalues are sorted in descending order.
        #U, s, V = np.linalg.svd(M)

        # M is a hermitian matrix. User eigh to compute eigenvalues. The
        # eigenvalues are returned in ascending order.
        sv, s_vec = np.linalg.eigh(M)
        sort_ind = np.flipud(np.argsort(sv))
        sv = sv[sort_ind]
        s_vec = s_vec[:, sort_ind]

        #################################################################
        # Compute the polarization features.
        #################################################################

        # Compute the linearity
        # Flinn1965:     L=1-ev2/ev1
        # Hearn1999:     L=1-ev2/ev1
        # Kennett2002:   L=1-(ev2+ev3)/(2*ev1)   decreases more slowly than
        #                                        Hearn1999 if ev3~ev2, i.e. if
        #                                        the signal is neither lineary
        #                                        nor planary polarized.
        # Vidale:        L=1-(ev2+ev3)/ev1       bad: could be negative!
        # -->Using definition by Hearn (=Flinn 1965)
        cur_linearity = 1 - sv[1] / sv[0]

        # Compute the planarity
        # Kennett2002:   P=1-2*ev3/(ev1+ev2)     would give 1 for a linear
        #                                        signal!
        # Vidale:        P=1-ev3/ev2             would possibely! not give 1 for
        #                                        a linear signal! As it is only
        #                                        possibely this definition is
        #                                        confusing -->bad!
        # -->Using definition by Kennett
        cur_planarity = 1 - 2 * sv[2] / (sv[0] + sv[1])


        # Compute the polarization strength.
        # Vidale:       Ps = 1 - (ev2 + ev3) / ev1
        cur_pol_strength = 1 - (sv[1] + sv[2]) / sv[0]

        # Compute the apparent azimuth. Clockwise from the y-axis.
        s_vec_max = s_vec[:, 0]
        cur_azimuth = np.arctan(np.real(s_vec_max[0]) / np.real(s_vec_max[1]))

        # Compute the apparent incidence angle. Measured from the z-axis.
        cur_incidence = np.arccos(np.abs(s_vec_max[2]) / np.linalg.norm(s_vec_max))

        features['linearity'].append(cur_linearity)
        features['planarity'].append(cur_planarity)
        features['pol_strength'].append(cur_pol_strength)
        features['azimuth'].append(cur_azimuth)
        features['incidence'].append(cur_incidence)
        features['eigenval'].append(sv)

    features['time'] = np.array(features['time'])
    features['linearity'] = np.array(features['linearity'])
    features['planarity'] = np.array(features['planarity'])
    features['pol_strength'] = np.array(features['pol_strength'])
    features['eigenval'] = np.array(features['eigenval'])
    features['azimuth'] = np.array(features['azimuth'])
    features['eigenval'] = np.array(features['eigenval'])
    return features



def compute_complex_covariance_matrix_windowed(component_data, window_length = None, overlap = 0.):
    ''' Compute the polarization features using the complex covariance method.

    '''
    time_array = component_data['time']
    x_data = np.array(component_data['x'])
    y_data = np.array(component_data['y'])
    z_data = np.array(component_data['z'])

    if window_length is None:
        window_length = len(x_data)

    win_step = np.floor(window_length - (window_length * overlap))
    n_win = np.floor( (len(z_data) - window_length) / win_step)

    features = {}
    features['time'] = []
    features['ellipticity'] = []
    features['pol_strength'] = []
    features['eigenval'] = []
    features['azimuth'] = []
    features['incidence'] = []

    # Compute the analytical data.
    x_data_comp = scipy.signal.hilbert(x_data)
    y_data_comp = scipy.signal.hilbert(y_data)
    z_data_comp = scipy.signal.hilbert(z_data)

    for k in np.arange(n_win + 1):
        start_ind = int(k * win_step)
        end_ind = int(start_ind + window_length)

        cur_x_data = x_data_comp[start_ind:end_ind]
        cur_y_data = y_data_comp[start_ind:end_ind]
        cur_z_data = z_data_comp[start_ind:end_ind]

        features['time'].append(time_array[int(np.floor((start_ind + end_ind)/2.))])

        D = np.vstack((cur_x_data, cur_y_data, cur_z_data))
        M = np.cov(D)

        # M is a hermitian matrix. User eigh to compute eigenvalues. The
        # eigenvalues are returned in ascending order.
        sv, s_vec = np.linalg.eigh(M)
        sort_ind = np.flipud(np.argsort(sv))
        sv = sv[sort_ind]
        s_vec = s_vec[:, sort_ind]

        # Compute the phase rotation.
        epsilon = 1e-6
        psi0 = 0.5 * np.angle( 0.5 * np.sum(s_vec[:,0]**2) + epsilon * 0.5 * sum(s_vec[:,0]**2))

        # Compute the major and minor semiaxis of the polarization ellipse.
        major = np.real(np.exp(-1j*psi0) * s_vec[:,0])
        minor = np.real(np.exp(-1j*(psi0 + np.pi/2.)) * s_vec[:,0])

        # Compute the polarization features.
        # Use the ellipticity definition from Morozov.
        cur_pol_strength = 1 - (sv[1] + sv[2]) / sv[0]
        cur_ellipticity = np.linalg.norm(minor) / np.linalg.norm(major)

        # Compute the apparent azimuth.
        cur_azimuth = np.arctan(np.real(major[0]) / np.real(major[1]))
        #print "major: %s" % major
        #print "azimuth: %f" % np.rad2deg(cur_azimuth)

        # Compute the apparent incidence angle.
        cur_incidence = np.arccos(np.abs(major[2]) / np.linalg.norm(major))

        #X = np.linalg.norm(major)
        #pe = np.sqrt(1 - X**2) / X
        features['ellipticity'].append(cur_ellipticity)
        features['pol_strength'].append(cur_pol_strength)
        features['eigenval'].append(sv)
        features['azimuth'].append(cur_azimuth)
        features['incidence'].append(cur_incidence)

    features['time'] = np.array(features['time'])
    features['ellipticity'] = np.array(features['ellipticity'])
    features['pol_strength'] = np.array(features['pol_strength'])
    features['eigenval'] = np.array(features['eigenval'])
    features['azimuth'] = np.array(features['azimuth'])
    features['incidence'] = np.array(features['incidence'])
    return features




def compute_instantaneous_attributes(component_data):
    ''' Compute the instantaneous polarization attributes using phase rotation.

    This method follows Morozov(1996).
    '''
    time_array = component_data['time']
    x_data = np.array(component_data['x'])
    y_data = np.array(component_data['y'])
    z_data = np.array(component_data['z'])

    features = {}
    features['time'] = []
    features['pe'] = []
    features['ps'] = []



def compute_complex_covariance_matrix(component_data):
    ''' Compute the polarization features using the complex covariance method.

    '''
    time_array = component_data['time']
    x_data = np.array(component_data['x'])
    y_data = np.array(component_data['y'])
    z_data = np.array(component_data['z'])

    features = {}
    features['time'] = []
    features['pe'] = []
    features['ps'] = []

    # Compute the analytical data.
    x_data_comp = scipy.signal.hilbert(x_data)
    y_data_comp = scipy.signal.hilbert(y_data)
    z_data_comp = scipy.signal.hilbert(z_data)

    # Compute the instantaneous covariance matrix using (x - mean(x)) *
    # np.conj((x - mean(x)) for each combination of x,y,z. 

    # Average the instatntaneous covariance matrix using a window.


    # Compute the polarization attributes.












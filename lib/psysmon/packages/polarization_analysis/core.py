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

def compute_covariance_matrix(component_data, window_length, overlap):
    ''' Compute the polarization features using the covariance matrix method.
    '''

    z_data = np.array(component_data['z'][1])
    n_data = np.array(component_data['ns'][1])
    e_data = np.array(component_data['ew'][1])
    time_array = component_data['z'][0]

    sample_win = psysmon.core.signal.tukey(window_length, 0.1)
    win_step = np.floor(window_length - (window_length * overlap))
    n_win = np.floor( (len(z_data) - window_length) / win_step)

    features = {}
    features['time'] = []
    features['linearity'] = []
    features['planarity'] = []
    for k in np.arange(n_win + 1):
        start_ind = int(k * win_step)
        end_ind = int(start_ind + window_length)

        cur_z_data = z_data[start_ind:end_ind] * sample_win
        cur_n_data = n_data[start_ind:end_ind] * sample_win
        cur_e_data = e_data[start_ind:end_ind] * sample_win

        features['time'].append(time_array[np.floor((start_ind + end_ind)/2.)])

        # Create the data matrix and compute the covariance matrix.
        D = np.vstack((cur_e_data, cur_n_data, cur_z_data))
        M = np.cov(D)

        # Compute the singular values using the singular value decomposition.
        # The columns of U are the eigenvectors.
        # The eigenvalues are sorted in descending order.
        U, s, V = np.linalg.svd(M)

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
        cur_linearity = 1 - s[1] / s[0]

        # Compute the planarity
        # Kennett2002:   P=1-2*ev3/(ev1+ev2)     would give 1 for a linear
        #                                        signal!
        # Vidale:        P=1-ev3/ev2             would possibely! not give 1 for
        #                                        a linear signal! As it is only
        #                                        possibely this definition is
        #                                        confusing -->bad!
        # -->Using definition by Kennett
        cur_planarity = 1 - 2 * s[2] / (s[0] + s[1])

        features['linearity'].append(cur_linearity)
        features['planarity'].append(cur_planarity)

    features['time'] = np.array(features['time'])
    features['linearity'] = np.array(features['linearity'])
    features['planarity'] = np.array(features['planarity'])
    return features


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

import itertools
import os
import csv

import psysmon.core.packageNodes as package_nodes
import psysmon.core.gui_preference_dialog as gui_preference_dialog
import psysmon.core.preferences_manager as pm
import psysmon.core.result as result
import psysmon.packages.sourcemap as sourcemap

import numpy as np
import scipy
import scipy.signal
import matplotlib.pyplot as plt


class ComputeLayers(package_nodes.LooperCollectionChildNode):
    ''' Compute the sourcemap for a given time window.

    '''
    name = 'compute sculpture layers'
    mode = 'looper child'
    category = 'Seismic Sculpture'
    tags = ['stable', 'looper child', 'seismic sculpture']

    def __init__(self, **args):
        ''' The constructor

        '''
        package_nodes.LooperCollectionChildNode.__init__(self, **args)

        item = pm.FileBrowsePrefItem(name = 'img_filename',
                                    value = '',
                                    filemask = 'Portable Network Graphic (*.png)|*.png|' \
                                                'all files (*)|*',
                                    tool_tip = 'Specify the image file.')
        self.pref_manager.add_item(item = item)

        # TODO: Create a method to reset the node data which is used for loop
        # execution.
        self.sculpture_layer = None


    def edit(self):
        ''' Create the preferences edit dialog.
        '''
        # Create the edit dialog.
        dlg = gui_preference_dialog.ListbookPrefDialog(preferences = self.pref_manager)

        # Enable/Disable the gui elements based on the pref_manager settings.
        #self.on_select_individual()

        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, stream, process_limits = None, origin_resource = None):
        ''' Execute the looper child collection node.

        Parameters
        ----------
        stream : :class:`obspy.core.Stream`
            The data to process.
        '''
        # Check if more than one station should be processed.
        if len(stream) != 1:
            self.logger.error("Can't handle more than one trace. The stream you passed contains more: %s.", stream)
            return

        # The number of agents.
        # TODO: Make this a user preference.
        n_agents = 1000

        # Try to load the image file.
        img_filename = self.pref_manager.get_value('img_filename')

        # Compute the pixel histogram. This can be done only once at the first
        # execution of the node. Save the result in a node attribute.


        # Get the trace data.
        trace = stream.traces[0]

        # Get the circle agents from the node. If this is the first execution,
        # create a new set of circle agents.
        if self.sculpture_layer is None:
            self.sculpture_layer = SculptureLayer(n_agents = n_agents)

        # Compute the envelope.
        analytic_trace = scipy.signal.hilbert(trace.data)
        #trace_envelope = np.sqrt(np.real(comp_trace)**2 + np.imag(comp_trace)**2)
        envelope = np.abs(analytic_trace)
        instantaneous_phase = np.unwrap(np.angle(analytic_trace))
        instantaneous_frequency = np.diff(instantaneous_phase) / (2.0*np.pi) * trace.stats.sampling_rate

        # Compute the polarity of the processing window.
        polarity = np.sign(trace.data)


        # Compute the psd.
        n_fft = n_agents * 2
        delta_t = 1 / trace.stats.sampling_rate
        T = (len(trace.data) - 1) * delta_t
        Y = scipy.fft(trace.data, n_fft)
        psd = 2 * delta_t**2 / T * np.abs(Y)**2
        psd = 10 * np.log10(psd)
        frequ = trace.stats.sampling_rate * np.arange(0,n_fft) / float(n_fft)

        left_fft = int(np.ceil(n_fft / 2.))

        self.sculpture_layer.add_psd(psd[:left_fft])

        self.sculpture_layer.move_agents(envelope)

        #for cur_env in self.sculpture_layer.envelope_list:
        #    plt.plot(cur_env)
        #plt.show()

        #plt.semilogx(self.sculpture_layer.mean_psd)
        #plt.show()

        #speed = [x.speed for x in self.sculpture_layer.agents]
        #plt.plot(speed)
        #plt.show()

        #r = 0.0001
        m_psd = self.sculpture_layer.mean_psd
        m_psd = m_psd / np.max(m_psd)
        m_psd = savitzky_golay(m_psd, 51, 3)
        r = 0.1 * m_psd
        agent_scale = 10000
        for cur_history in self.sculpture_layer.full_history:
            theta = np.linspace(0, 2*np.pi, len(cur_history))
            cx = (r + np.array(cur_history) * agent_scale) * np.cos(theta)
            cy = (r + np.array(cur_history) * agent_scale) * np.sin(theta)
            plt.plot(cx, cy)
            #plt.plot(cur_history)

        cx = (r + self.sculpture_layer.dir_limit * agent_scale) * np.cos(theta)
        cy = (r + self.sculpture_layer.dir_limit * agent_scale) * np.sin(theta)
        plt.plot(cx, cy, 'r', linewidth = 2)
        plt.axis('equal')
        plt.show()

        #if len(self.sculpture_layer.agent_history) > 1:
        #    x_diff = np.array(self.sculpture_layer.agent_history[-1]) - np.array(self.sculpture_layer.agent_history[-2])
        #    plt.plot(x_diff)
        #    plt.show()

        # TODO: Add preference items to specify the length of the processing
        # window and the overlap.

        # Loop through the processing windows.

            # Get the envelope of the processing window.

            # Compute the spectrum of the processing window.


            # Modify the agents using the above parameters.




class SculptureLayer(object):

    def __init__(self, n_agents, max_speed = 0.5):
        ''' Initialize the instance.
        '''
        self.max_speed = 0.5    # The maximum allowed speed (m/s).

        self.agents = []

        for k in range(0, n_agents):
            self.agents.append(Agent(self, pos = k, influence = 3))

        self.full_history = []

        self.agent_history = []

        self.psd_list = []

        self.envelope_list = []

        self.uif = None
        self.uof = None
        self.dir_limit = None


    @property
    def mean_psd(self):
        return np.median(np.array(self.psd_list), 0)

    @property
    def mean_envelope(self):
        return np.median(np.array(self.envelope_list), 0)

    @property
    def mean_agent_history(self):
        return np.median(np.array(self.agent_history), 0)

    @property
    def mean_full_history(self):
        return np.median(np.array(self.full_history), 0)

    def add_psd(self, psd):
        '''
        '''
        self.psd_list.append(psd)
        if len(self.psd_list) > 12:
            self.psd_list = self.psd_list[-12:]


    def move_agents(self, envelope):
        '''
        '''
        win_length = int(np.floor(len(envelope) / float(len(self.agents))))

        red_envelope = []
        for k, cur_agent in enumerate(self.agents):
            win_start = k * win_length
            win_end = win_start + win_length - 1
            cur_envelope_val = np.max(envelope[win_start:win_end])
            red_envelope.append(cur_envelope_val)
            cur_agent.change_speed(cur_envelope_val)
            cur_agent.move()

        self.envelope_list.append(red_envelope)
        if len(self.envelope_list) > 12:
            self.envelope_list = self.envelope_list[-12:]

        x = [x.x for x in self.agents]
        self.agent_history.append(x)
        if len(self.agent_history) > 12:
            self.agent_history = self.agent_history[-12:]

        self.full_history.append(x)

        self.compute_outlier_limit()


    def compute_outlier_limit(self):
        '''
        '''
        if len(self.envelope_list) > 0:
            mean_full_history = self.mean_full_history
            self.dir_limit = 4 * np.percentile(mean_full_history, 75)
            mean_envelope = self.mean_envelope
            self.q1 = np.percentile(mean_envelope, 25)
            self.q3 = np.percentile(mean_envelope, 75)
            iq = self.q3 - self.q1
            #self.lif = q1 - 1.5 * iq
            self.uif = self.q3 + 1.5 * iq
            self.uof = self.q3 + 10 * iq

        #if len(self.agent_history) > 0:
        #    mean_agent_history = self.mean_agent_history
        #    self.q1 = np.percentile(mean_agent_history, 25)
        #    self.q3 = np.percentile(mean_agent_history, 75)
        #    iq = self.q3 - self.q1
        #    #self.lif = q1 - 1.5 * iq
        #    self.uif = self.q3 + 1.5 * iq
        #    self.uof = self.q3 + 3 * iq


    def get_neighbours_back(self, pos, count):
        '''
        '''
        if (pos - count) >= 0:
            agents =  self.agents[pos-count:pos+1]
        else:
            agents = self.agents[(pos-count):]
            agents.extend(self.agents[:pos])

        return agents


    def get_neighbours_front(self, pos, count):
        '''
        '''
        if (pos + count) < len(self.agents):
            agents =  self.agents[pos:pos+count]
        else:
            agents = self.agents[pos:]
            agents.extend(self.agents[:count - len(agents)])

        return agents



class Agent(object):

    def __init__(self, parent, pos, influence = 0):
        ''' Initialize the instance.
        '''
        self.parent = parent

        self.pos = pos

        self.speed_list = []

        self.direction = 1

        self.n_speed_mean = 12

        self.influence = influence

        self.x = None

        self.y = None

        self.speed_weight_limit = 1e-5

        self.attractor_speed = 1e-7


    @property
    def speed(self):
        # TODO: Use a weighted mean for the speed value.
        if len(self.speed_list) >= 3:
            win = tukey(len(self.speed_list), 1)
        else:
            win = 1.

        return np.sum(np.array(self.speed_list) * win)/np.sum(win)


    def change_speed(self, speed):
        ''' Change the speed of the agent.
        '''
        self.speed_list.append(speed)
        if len(self.speed_list) > self.n_speed_mean:
            self.speed_list = self.speed_list[-self.n_speed_mean:]


    def move(self, step = 1., weight = 1.):
        ''' Move the agent for the time step.
        '''
        if self.x is not None:
            if self.x > self.speed_weight_limit:
                speed_weight = 1./(self.x / self.speed_weight_limit)
            else:
                speed_weight = 1.
        else:
            speed_weight = 1.
            self.x = 0


        self.x = self.x + (self.speed * self.direction * speed_weight * step)

        if (self.parent.dir_limit is not None) and (self.x > self.parent.dir_limit) and self.direction == 1:
            # TODO: Only switch the direction after a certain amount of switch
            # requests.
            # TODO: Handle strong negative direction velocities.
            self.direction = -1
            print "%d - switched direction: %d" % (self.pos, self.direction)

        if self.influence > 0:
            effect = 0.5
            win = tukey(self.influence * 2 + 1, 1)
            neighbours_back = self.parent.get_neighbours_back(self.pos, self.influence)
            neighbours_front = self.parent.get_neighbours_front(self.pos, self.influence)

            for k, cur_neighbour in enumerate(neighbours_back):
                if cur_neighbour.x is None:
                    cur_neighbour.x = self.x * win[k] * effect
                else:
                    if cur_neighbour.x < self.x:
                        cur_neighbour.x += (self.x - cur_neighbour.x) * win[k] * effect
                    else:
                        cur_neighbour.x -= (cur_neighbour.x - self.x) * win[k] * effect


            for k, cur_neighbour in enumerate(neighbours_front):
                if cur_neighbour.x is None:
                    cur_neighbour.x = self.x * win[k] * effect
                else:
                    if cur_neighbour.x < self.x:
                        cur_neighbour.x += (self.x - cur_neighbour.x) * win[k] * effect
                    else:
                        cur_neighbour.x -= (cur_neighbour.x - self.x) * win[k] * effect




def tukey(N, alpha):

    alpha = float(alpha)
    n = np.arange(0,N).flatten()
    w = np.ones(len(n))

    mask = (n >= 0) & (n <= alpha*(N-1)/2.0)
    w[mask] = 1/2. * (1 + np.cos(np.pi * ( (2*n[mask]) / (alpha * (N-1)) - 1 )))

    #mask = (n > alpha*(N-1)/2.0) & (n <= (N-1)*(1-alpha/2.))
    #w[mask] = 1

    mask = (n > (N-1)*(1-alpha/2)) & (n <= (N-1))
    w[mask] = 1/2. * (1 + np.cos(np.pi * ( (2*n[mask]) / (alpha * (N-1)) - 2/alpha + 1 )))

    return w




def savitzky_golay(y, window_size, order, deriv=0, rate=1):
    r"""Smooth (and optionally differentiate) data with a Savitzky-Golay filter.
    The Savitzky-Golay filter removes high frequency noise from data.
    It has the advantage of preserving the original shape and
    features of the signal better than other types of filtering
    approaches, such as moving averages techniques.
    Parameters
    ----------
    y : array_like, shape (N,)
        the values of the time history of the signal.
    window_size : int
        the length of the window. Must be an odd integer number.
    order : int
        the order of the polynomial used in the filtering.
        Must be less then `window_size` - 1.
    deriv: int
        the order of the derivative to compute (default = 0 means only smoothing)
    Returns
    -------
    ys : ndarray, shape (N)
        the smoothed signal (or it's n-th derivative).
    Notes
    -----
    The Savitzky-Golay is a type of low-pass filter, particularly
    suited for smoothing noisy data. The main idea behind this
    approach is to make for each point a least-square fit with a
    polynomial of high order over a odd-sized window centered at
    the point.
    Examples
    --------
    t = np.linspace(-4, 4, 500)
    y = np.exp( -t**2 ) + np.random.normal(0, 0.05, t.shape)
    ysg = savitzky_golay(y, window_size=31, order=4)
    import matplotlib.pyplot as plt
    plt.plot(t, y, label='Noisy signal')
    plt.plot(t, np.exp(-t**2), 'k', lw=1.5, label='Original signal')
    plt.plot(t, ysg, 'r', label='Filtered signal')
    plt.legend()
    plt.show()
    References
    ----------
    .. [1] A. Savitzky, M. J. E. Golay, Smoothing and Differentiation of
       Data by Simplified Least Squares Procedures. Analytical
       Chemistry, 1964, 36 (8), pp 1627-1639.
    .. [2] Numerical Recipes 3rd Edition: The Art of Scientific Computing
       W.H. Press, S.A. Teukolsky, W.T. Vetterling, B.P. Flannery
       Cambridge University Press ISBN-13: 9780521880688
    """
    import numpy as np
    from math import factorial
    
    try:
        window_size = np.abs(np.int(window_size))
        order = np.abs(np.int(order))
    except ValueError, msg:
        raise ValueError("window_size and order have to be of type int")
    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")
    order_range = range(order+1)
    half_window = (window_size -1) // 2
    # precompute coefficients
    b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
    m = np.linalg.pinv(b).A[deriv] * rate**deriv * factorial(deriv)
    # pad the signal at the extremes with
    # values taken from the signal itself
    firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
    lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))
    return np.convolve( m[::-1], y, mode='valid')

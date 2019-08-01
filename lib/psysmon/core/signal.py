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

import math
import numpy as np

def tukey(N, alpha):

    alpha = float(alpha)
    n = np.arange(0,N).flatten()
    w = np.ones(len(n))

    mask = (n >= 0) & (n <= alpha*(N-1)/2.0)
    w[mask] = 1/2. * (1 + np.cos(np.pi * ( (2*n[mask]) / (alpha * (N-1)) - 1 )))

    #mask = (n > alpha*(N-1)/2.0) & (n <= (N-1)*(1-alpha/2.))
    #w[mask] = 1

    mask = (n > (N-1)*(1-alpha/2)) & (n <= (N-1))
    w[mask] = 1/2 * (1 + np.cos(np.pi * ( (2*n[mask]) / (alpha * (N-1)) - 2/alpha + 1 )))

    return w


def nearest_pow_2(x):
    """ Find power of two nearest to x
    """
    a = math.pow(2, math.ceil(np.log2(x)))
    b = math.pow(2, math.floor(np.log2(x)))
    if abs(a - x) < abs(b - x):
        return a
    else:
        return b

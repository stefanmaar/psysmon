// LICENSE
//
// This file is part of pSysmon.
//
// If you use pSysmon in any program or publication, please inform and
// acknowledge its author Stefan Mertl (stefan@mertl-research.at).
//
// pSysmon is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

// copyright: Stefan Mertl

#include <math.h>

int moving_average(const long n_data, long n_op, const double *data, double *avg)
{
    int i;

    if (n_data == 0) {
        return 0;
    }

    if (n_op == 0) {
        return 0;
    }

    if (n_data < n_op) {
        n_op = n_data;
    }

    avg[0] = data[0] / n_op;

    for (i = 1; i< n_op; i++) {
        avg[i] = avg[i-1] + data[i] / n_op;
    }

    for (i = n_op; i < n_data; i++) {
        avg[i] = (data[i] - data[i-n_op]) / n_op + avg[i-1];
    }

    return 0;
}

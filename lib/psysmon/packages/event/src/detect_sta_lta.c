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


int detect(const long n_sta, const long n_lta, const float thr, const long n_data, const double *data, double *sta, double *lta, double stop_crit)
{
    int k;

    if (n_data == 0) {
        return 0;
    }
    
    sta[0] = data[0] / n_sta;
    lta[0] = data[0] / n_lta;
    
    for (k = 1; k < n_lta; i++) 
    {
        sta[k] = sta[k - 1] + data[k] / n_sta;
        lta[k] = lta[k - 1] + data[k] / n_lta;
    }

    for (k = n_lta; k < n_data; k++)
    {
        sta[k] = (sta[k] - data[k - n_sta]) / n_sta + sta[k - 1];
        lta[k] = (lta[k] - data[k - n_lta]) / n_lta + lta[k - 1];
    }
}


int compute_event_end(const long n_sta, const double *sta, const long n_lta, const double *lta, double stop_value, double *stop_crit)
{
    int k;
    int event_end = n_sta;
    int end_triggered = 0;
    int sta_below_lta_required = 10;
    int sta_below_stop_required = 100;
    int cnt_sta_below_lta = 0;
    int cnt_sta_below_stop = 0;
    double stop_value_orig = stop_value;

    for (k = 0; k < n_sta; k++)
    {
        if (sta[k] < lta[k])
        {
            cnt_sta_below_lta++;
        }
        else
        {
            cnt_sta_below_lta = 0;
            stop_value = stop_value_orig;
        }

        if (cnt_sta_below_lta > sta_below_lta_required)
        {
            stop_value += stop_value_orig * 0.001;
        }

        stop_crit[k] = stop_value;


        if ((sta[k] < stop_value) && (cnt_sta_below_stop <= sta_below_stop_required))
        {
            if (end_triggered == 0)
            {
                event_end = k;
            }
            end_triggered = 1;
            cnt_sta_below_stop++;
        }
        else if ((sta[k] < stop_value) && (cnt_sta_below_stop > sta_below_stop_required))
        {
            break;
        }
        else if (sta[k] > stop_value)
        {
            end_triggered = 0;
            event_end = 0;
            cnt_sta_below_stop = 0;
        }
    }

    return event_end;
}


int compute_event_start(const long n_thrf, const double *thrf, const double thr)
{
    int k;
    long event_start = 0;
    int load_trigger = 0;
    int min_length = 2;
    int cnt_above_thr = 0;

    for (k = 0; k < n_thrf; k++)
    {
        event_start = k;
        if (thrf[k] < thr)
        {
            load_trigger = 1;
            cnt_above_thr = 0;
        }
        
        if (load_trigger == 1)
        {
            if (thrf[k] > thr)
            {
                cnt_above_thr++;
            }
        }

        if (cnt_above_thr > min_length)
        {
            event_start = event_start - min_length;
            break;
        }
    }

    return event_start;
}

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

#include <stdio.h>
#include <math.h>


int compute_event_end(const long n_sta, const double *sta,
                      const long n_lta, const double *lta,
                      double stop_value, double *stop_crit,
                      const double stop_growth, const double stop_growth_exp,
                      const double stop_growth_inc, const long stop_growth_inc_begin,
                      const long init_trigger)
{
    int k;
    int event_end = -1;
    int end_triggered = 0;
    // TODO: Make this a user selectable parameter.
    int sta_below_lta_required = 10;
    // TODO: Make this a user selectable parameter.
    int sta_below_stop_required = 100;
    int cnt_sta_below_lta = 0;
    int cnt_sta_below_stop = 0;
    int cnt_growth_inc = 0;
    double stop_value_orig = stop_value;

    for (k = 0; k < n_sta; k++)
    {
        if (sta[k] < lta[k])
        {
            // Increase the counter only if the index has passed
            // the initial trigger of the detection start.
            if (k > init_trigger) {
                cnt_sta_below_lta++;
            }
        }
        else
        {
            cnt_sta_below_lta = 0;
            cnt_growth_inc = 0;
            stop_value = stop_value_orig;
        }

        if (cnt_sta_below_lta > sta_below_lta_required)
        {
            double cur_stop_growth = stop_growth;
            if (cnt_sta_below_lta >= stop_growth_inc_begin)
            {
                cur_stop_growth = stop_growth + cnt_growth_inc * (stop_growth * stop_growth_inc);
                cnt_growth_inc++;
            }
            stop_value = stop_value_orig + pow(cnt_sta_below_lta * stop_value_orig * cur_stop_growth, stop_growth_exp);
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
            event_end = -1;
            cnt_sta_below_stop = 0;
        }
    }

    return event_end;
}


int compute_event_start(const long n_thrf, const double *thrf, const double thr, const double fine_thr, const double turn_limit, const double fine_thr_win, long *initial_event_start)
{
    int k;
    long event_start = 0;
    int load_trigger = 0;
    int min_length = 2;
    int cnt_above_thr = 0;
    int up_trigger = 0;
    int turn_flag = 0;
    double turn_value = 0;
    int min_k;
    int min_k_value = 0;

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

    // Refine the event start using a lower thr.
    //printf("passed initial_event_start: %ld\n", *initial_event_start);
    *initial_event_start = event_start;
    //printf("event_start before refinement: %ld\n", *initial_event_start);
    min_k = event_start;
    min_k_value = thrf[event_start];
    for (k = event_start; k >= 0; k--)
    {
        // Update the minimum thrf values.
        if (thrf[k] <= min_k_value) {
          min_k = k;
          min_k_value = thrf[k];
        }
      
        if (thrf[k] < fine_thr)
        {
            // The thrf falls below the fine thr.
            //printf("k: %d; thrf below fine_thr. break.\n", k);
            event_start = k;
            break;
        }

        if (up_trigger == 0)
        {
            if (thrf[k] > thrf[k + 1])
            {
                //printf("k: %d; set up_trigger.\n", k);
                up_trigger = 1;
                if (turn_flag == 0)
                {
                    turn_value = thrf[k];
                    turn_flag = 1;
                    //printf("k: %d; initialized the turn_value: %f\n", k, turn_value);
                }
                else if (thrf[k] < turn_value)
                {
                    turn_value = thrf[k];
                    //printf("k: %d; changed turn_value: %f\n", k, turn_value);
                }
            }
        }
        else
        {
            if (thrf[k] < thrf[k + 1])
            {
                //printf("k: %d; clear up_trigger.\n", k);
                up_trigger = 0;
                turn_flag = 0;
            }

        }

        //printf("k: %d; thrf[k]: %f; turn_value: %f\n", k, thrf[k], turn_value);
        if ((turn_flag == 1) && (thrf[k] - turn_value) > turn_limit)
        {
            //printf("turn_value limit reached.\n");
            event_start = min_k;
            break;
        }

        if ((event_start - k) > fine_thr_win) {
           //printf("fine_thr_win reached.\n");
           event_start = min_k;
           break;
        }

        if (k == 0) {
           event_start = min_k;
        }
    }
    //printf("event_start: %ld\n", event_start);

    return event_start;
}

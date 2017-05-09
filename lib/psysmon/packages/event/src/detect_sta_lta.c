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


int compute_event_end(const long n_sta, const double *sta, const long n_lta, const double *lta, double stop_value, double *stop_crit, const double stop_growth)
{
    int k;

    // The detected index of the event end.
    int event_end = -1;

    // A flag indicating, that an event end was triggered.
    int end_triggered = 0;

    // The number of samples of the sta below the lta which are required to
    // start the growth of the stop criterium. 
    int sta_below_lta_required = 10;

    // The number of samples of the sta below the stop value which are
    // required to confirm the triggered event end.
    int sta_below_stop_required = 100;

    // A counter counting the number of samples of the sta below the lta.
    int cnt_sta_below_lta = 0;

    // A counter counting the number of samples of the sta below the stop
    // value.
    int cnt_sta_below_stop = 0;

    // The stop value.
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

        // If the STA was below the LTA for a certain amount of samples start
        // to grow the stop value. This is done to ensure, that the stop value
        // exceeds the STA at some time.
        if (cnt_sta_below_lta > sta_below_lta_required)
        {
            stop_value += stop_value_orig * stop_growth;
        }

        // Store the current stop value in the array for later use as a python
        // array.
        stop_crit[k] = stop_value;



        if ((sta[k] < stop_value) && (end_triggered == 0))
        {
            // The first time that the STA drops below the stop_value and no
            // event end has been triggered yet.
            // Set the index of the event end and set the state to the
            // end_triggered mode.
            event_end = k;
            end_triggered = 1;
        }
        else if ((end_triggered == 1) && (sta[k] < stop_value) && (cnt_sta_below_stop <= sta_below_stop_required))
        {
            // An event end has been triggered. Wait the
            // sta_below_stop_required samples to confirm the correct event
            // end. During this time, another increase of the STA above the
            // stop value resets the end_triggered state. 
            // Increase the STA below the stop value counter.
            cnt_sta_below_stop++;
        }
        else if ((sta[k] < stop_value) && (cnt_sta_below_stop > sta_below_stop_required))
        {
            // The triggered end was confirmed by exceeding the
            // sta_below_stop_required threshold. Leave the loop.
            break;
        }
        else if ((end_triggered == 1) && (sta[k] > stop_value))
        {
            // The STA raises again above the stop value. Reset the
            // end_triggered state.
            end_triggered = 0;
            event_end = -1;
            cnt_sta_below_stop = 0;
        }
    }

    return event_end;
}


int compute_event_start(const long n_thrf, const double *thrf, const double thr, const double fine_thr, const double turn_limit)
{
    int k;
    
    // The index of the detected event start. 
    long event_start = 0;

    // The active state of the trigger.
    int trigger_active = 0;

    int min_length = 2;
    int cnt_above_thr = 0;
    int up_trigger = 0;
    int turn_flag = 0;
    double turn_value = 0;

    for (k = 0; k < n_thrf; k++)
    {
        event_start = k;

        // It may happen, that the thrf is above the thr at the start of the
        // loop. Activate the trigger, when the thrf falls below the thr for
        // the first time.
        if (thrf[k] < thr)
        {
            trigger_active = 1;
            cnt_above_thr = 0;
        }

        if (trigger_active == 1)
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
    //printf("event_start before refinement: %ld\n", event_start);
    for (k = event_start; k > 0; k--)
    {
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
            }

        }

        //printf("k: %d; thrf[k]: %f; turn_value: %f\n", k, thrf[k], turn_value);
        if ((turn_flag == 1) && (thrf[k] - turn_value) > turn_limit)
        {
            //printf("turn_value limit reached.\n");
            event_start = k;
            break;
        }
    }

    return event_start;
}

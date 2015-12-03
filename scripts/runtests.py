#!/usr/bin/env python
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
'''
A utility program to run psysmon tests.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)


Examples
-----------
'''

import argparse
import unittest
from psysmon.external.html_testrunner import HTMLTestRunner


def getsuites(package_names):
    testloader = unittest.TestLoader()
    suites = []

    for cur_name in package_names:
        mod_path = 'psysmon.packages.%s.tests' % cur_name
        print "Searching %s" % mod_path
        cur_suites = testloader.loadTestsFromName(mod_path)
        suites.append(cur_suites)

    return suites


if __name__ == '__main__':
    '''
    Run the script when called from the command line.
    '''
    parser = argparse.ArgumentParser(description = 'runtests')
    parser.add_argument('-p', '--package', help = 'Specify the package(s) for which the tests should be run.',
                        type = str, choices = ['event', 'geometry'], nargs='*', metavar = 'PACKAGE(S)')

    args = parser.parse_args()

    testsuites = []

    if args.package is not None:
        testsuites.extend(getsuites(args.package))

    # Run the testsuites.
    outfile = file('test_report.html', 'wb')
    runner = HTMLTestRunner(stream = outfile,
                            title = 'psysmon testing',
                            description = 'A first test.')
    for cur_suite in testsuites:
        runner.run(cur_suite)






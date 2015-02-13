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
Some setup helper functions.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)
'''

import os
import sys
import re
from textwrap import fill

if sys.version_info[0] < 3:
    import ConfigParser as configparser
else:
    import configparser


# pSysmon build options. These can be altered using setup.cfg
options = {'displayStatus': True,
           'verbose': False}

# Get the setup.cfg file name.
setupCfg = os.environ.get('PSY_SETUPCFG', 'setup.cfg')
# Based on the contents of setup.cfg, determine the build options.
if os.path.exists(setupCfg):
    config = configparser.SafeConfigParser()
    config.read(setupCfg)

    try: options['displayStatus'] = not config.getboolean("status", "suppress")
    except: pass

    try: options['verbose'] = config.getboolean("status", "verbose")
    except: pass


if options['displayStatus']:
    def printLine(char='='):
        print(char * 76)

    def printStatus(package, status):
        initial_indent = "%22s: " % package
        indent = ' ' * 24
        print(fill(str(status), width=76,
                   initial_indent=initial_indent,
                   subsequent_indent=indent))

    def printMessage(message):
        indent = ' ' * 24 + "* "
        print(fill(str(message), width=76,
                   initial_indent=indent,
                   subsequent_indent=indent))

    def printRaw(section):
        print(section)
else:
    def printLine(*args, **kwargs):
        pass
    printStatus = printMessage = printRaw = printLine



def checkForPackage(name, requiredVersion):
    rV = requiredVersion.split('.')
    for k,x in enumerate(rV):
        rV[k] = int(x)

    try:
        if name == 'pillow':
            mod = __import__('PIL', globals(), locals(), ['VERSION'], -1)
            __version__ = mod.PILLOW_VERSION
        elif name == 'cairo':
            mod = __import__('cairo', globals(), locals(), ['version'], -1)
            __version__ = mod.version
        elif name == 'lxml':
            mod = __import__('lxml.etree', globals(), locals(), ['__version__'], -1)
            __version__ = mod.__version__
        else:
            mod = __import__(name, globals(), locals(), ['__version__'], -1)
            __version__ = mod.__version__
    except ImportError:
        printStatus(name, "missing")
        printMessage("You must install %s %s or later to build pSysmon." % (name, requiredVersion))
        return False
    except AttributeError:
        printStatus(name, "missing")
        printMessage("No version string found in package %s." % name)
        return False



    nn = __version__.split('.')
    for k,x in enumerate(nn):
        if x.isdigit():
            nn[k] = int(x)
        else:
            tmp = re.split('[A-Za-z]', x)
            tmp = [x for x in tmp if x.isdigit()]
            if len(tmp) > 0:
                nn[k] = int(tmp[0])
            else:
                nn[k] = 0

    checkPassed = False
    for k, cur_n in enumerate(rV):
        if cur_n > rV[k]:
            checkPassed = True
            break
        elif cur_n == rV[k] and k < len(nn)-1:
            checkPassed = True
        elif cur_n == rV[k] and k == len(nn)-1:
            checkPassed = True
            break
        else:
            checkPassed = False
            break

    #if nn[0] > rV[0]:
    #    checkPassed = True
    #elif nn[0] == rV[0] and nn[1] > rV[1]:
    #    checkPassed = True
    #elif nn[1] == rV[1] and nn[2] > rV[2]:
    #    checkPassed = True
    #elif nn[2] == rV[2]:
    #    checkPassed = True

    if not checkPassed:
        printMessage(
           '%s %s or later is required; you have %s' %
           (name, requiredVersion, __version__))
    else:
        printStatus(name, "%s (%s required)" % (__version__, requiredVersion))

    return checkPassed

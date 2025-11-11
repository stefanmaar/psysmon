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
The pSysmon main program.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)


Examples
-----------

**Starting from the command line**

    To start pSysmon from the command line, change into the psysmon directory 
    where the file pSysmon.py is located and type the following command in your 
    linux shell or your window command prompt:

    >>> psysmon

    or

    >>> python psysmon
'''
import json
import logging
import os

import click
import matplotlib as mpl

import psysmon
import psysmon.core.base as psybase
import psysmon.core.json_util
import psysmon.gui.main.main_window as psy_main
import psysmon.gui.main.app as psy_app

mpl.rcParams['backend'] = 'WXAgg'


@click.command()
@click.option('--config',
              type = str,
              default = None,
              help = 'The psysmon configuration file to use.')
def run(config):
    '''
    Start the psysmon program.
    '''
    config_file = config
    if config_file is None:
        config_file = psysmon.get_config_file()
    else:
        config_file = os.path.abspath(config_file)
    config = load_config(config_file = config_file)

    if 'pref_manager' in config.keys():
        pref_manager = config['pref_manager']
        main_loglevel = pref_manager.get_value('main_loglevel')
        shell_loglevel = pref_manager.get_value('shell_loglevel')
        status_loglevel = pref_manager.get_value('gui_status_loglevel')
    else:
        pref_manager = None
        main_loglevel = 'INFO'
        shell_loglevel = 'INFO'
        status_loglevel = 'INFO'

    logger = logging.getLogger('psysmon')
    logger.setLevel(main_loglevel)

    handler = psysmon.getLoggerHandler(log_level = shell_loglevel)
    handler.set_name('shell')
    logger.addHandler(handler)

    if pref_manager is None:
        logger.warning("Couldn't load the configuration from file %s. Using the default configuration.",
                       config_file)
        logger.info("If this is the first time starting psysmon, the configuration file will be created and the warning should not appear again.")

    psyBaseDir = os.path.abspath(psysmon.__file__)
    psyBaseDir = os.path.dirname(psyBaseDir)
    logger.debug("psyBaseDir: %s", psyBaseDir)

    # Initialize the pSysmon base object.
    psyBase = psybase.Base(psyBaseDir,
                           pref_manager = pref_manager,
                           config_file = config_file)

    # Scan for available pSysmon packages.
    #psyBase.initialize()

    # Create the app and run the GUI.
    app = psy_app.PsysmonApp()
    psysmonMain = psy_main.PsysmonGui(psyBase, None)

    handler = psysmon.getLoggerWxRedirectHandler(psysmonMain.loggingPanel,
                                                 log_level = status_loglevel)
    handler.set_name('gui_status')
    logger.addHandler(handler)

    if 'recent_files' in config.keys():
        for cur_file in reversed(config['recent_files']):
            psysmonMain.filehistory.AddFileToHistory(cur_file)

    psysmonMain.Show()
    psysmonMain.Maximize(True)

    app.MainLoop()

    # Stop the project server.
    psyBase.stop_project_server()


def load_config(config_file):
    ''' Load the configuration data from the config file.
    '''
    config = {}

    if os.path.exists(config_file):
        try:
            file_meta = psysmon.core.json_util.get_file_meta(config_file)
            decoder = psysmon.core.json_util.get_config_decoder(file_meta['file_version'])
            with open(config_file, 'r') as fid:
                config = json.load(fid,
                                   cls = decoder)
        except Exception:
            config = {}

    return config


if __name__ == '__main__':
    run()

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
'''

import logging
import os
import pprint
import sys
import shelve


#class ExecutionFrame(wx.Frame):
#
#    def __init__(self, collection):
#        wx.Frame.__init__(self, None, wx.ID_ANY, 'Execution frame')
#        #wx.CallAfter(collection.execute, 'halloooo')


if __name__ == "__main__":

    # The process name and the temp. file are passes as arguments. 
    filename = sys.argv[1]
    proc_name = sys.argv[2]
    backend = sys.argv[3]

    import matplotlib as mpl
    mpl.rcParams['backend'] = backend

    import psysmon
    from psysmon.core.waveclient import PsysmonDbWaveClient
    from psysmon.core.waveclient import EarthwormWaveClient
    from psysmon.core.waveclient import SeedlinkWaveClient
    import psysmon.core.base as psybase

    filename = filename
    proc_name = proc_name

    # Get the execution parameters from the ced file.
    db = shelve.open(filename)
    package_directories = db['package_directories']
    sys.path.extend(package_directories)
    project = db['project']
    collection = db['collection']
    waveclients = db['waveclient']
    project_server = db['project_server']
    pref_manager = db['pref_manager']
    db.close()

    #logfileName = os.path.join(tempfile.gettempdir(), proc_name + '.log')
    logfileName = os.path.join(project.logDir, proc_name + '.log')

    logger = logging.getLogger('psysmon')
    # Don't propagete the messages to the root logger to avoid logging
    # using the default console logger.
    logger.propagate = False
    logger.setLevel(pref_manager.get_value('main_loglevel'))
    file_handler = psysmon.getLoggerFileHandler(logfileName)
    file_handler.setLevel(pref_manager.get_value('collection_loglevel'))
    logger.addHandler(file_handler)

    logger.info('Starting process %s', proc_name)
    logger.info('Loading data from file %s', filename)

    logger.info('Project: %s', project)
    logger.info('Collection: %s', collection)

    logger.info('Executing collection %s of project %s.', collection, project)

    try:
        psyBaseDir = os.path.abspath(psysmon.__file__)
        psyBaseDir = os.path.dirname(psyBaseDir)
        psyBase = psybase.Base(psyBaseDir,
                               project_server = project_server,
                               pref_manager = pref_manager)
        psyBase.project = project
        psyBase.process_meta['name'] = proc_name
        psyBase.process_meta['pid'] = os.getpid()


        # Reinitialize the project.
        project.connect2Db()
        project.loadDatabaseStructure(psyBase.packageMgr.packages)
        project.load_geometry_inventory()

        for curName, curMode, curAttributes in waveclients:
            if curMode == 'PsysmonDbWaveClient':
                waveclient = PsysmonDbWaveClient(curName, project)
            elif curMode == 'EarthwormWaveClient':
                waveclient = EarthwormWaveClient(curName, **curAttributes)
            elif curMode == 'SeedlinkWaveClient':
                waveclient = SeedlinkWaveClient(curName, project = project, **curAttributes)
            else:
                waveclient = None

            if waveclient != None:
                project.addWaveClient(waveclient)

        collection.set_project(project)
        collection.createNodeLoggers()
        # Replace the collection in the project with the copied collection.
        # This makes the use of the activeCollection attribute valid.
        project.activeUser.collection[collection.name] = collection
        project.setActiveCollection(collection.name)

        project.psybase = psyBase
        logger.debug('psyBase: %s', project.psybase)

        # Write the collection settings to the log file.
        pp = pprint.PrettyPrinter(indent = 2)
        logger.info('The collection settings used:\n%s', pp.pformat(collection.get_settings()))

        returncode = 0
        collection.setDataShelfFile(filename)
        try:
            if collection.runtime_att.start_time:
                logger.info('global start time: %s', collection.runtime_att.start_time.isoformat())
            if collection.runtime_att.end_time:
                logger.info('global end time: %s', collection.runtime_att.end_time.isoformat())
            exec_success = collection.execute()
            if type(exec_success) == bool and not exec_success:
                return_code = 5
                logger.error('The collection execution was not successful. There have been some errors which have been handled by the collection. Check the log file for the error messages.')
            logger.info('Finished the execution. Cleaning up....')
        except:
            logger.exception("Failed to execute the collection.")
            # An error happened during the execution of the collection.
            returncode = 2
    except:
        # An error happened while preparing the execution of the collection.
        logger.exception("Failed to prepare to exectute the collection.")
        returncode = 3
    finally:
        try:
            logger.info('Unregistering the exported data from the project server.')
            # TODO: Reactivate the project server again.
            #psyBase.project_server.unregister_data(uri = collection.rid, recursive = True)
        except:
            # An error happened because basic variables couldn't be accessed.
            returncode = 4
            logger.exception("Error when unregistering the project server data.")
        logger.info('Deleting data file %s.', filename)
        os.remove(filename)

        sys.exit(returncode)

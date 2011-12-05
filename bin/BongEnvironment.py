"""
Initialize and check settings and resources for the Bong Download Manager


"""
import sys
import re
import logging
import logging.handlers
import os.path
import ConfigParser
from BongLibrary import alignMultipleTextLines


logger = None
settings = None

def _dumpSettings():
    keys = settings.keys()
    keys.sort()
    for k in keys:
        logger.info("{} = {!s}".format(k, settings[k]))


def ConfigureLogging(logfile, verbose):

    global logger
    
    # Set up a specific logger with our desired output level
    logger = logging.getLogger('Bong')
    logger.setLevel(logging.DEBUG)

    # create rotating file handler capturing all messages
    filehandler = logging.handlers.RotatingFileHandler(logfile, maxBytes=10000000, backupCount=3, encoding='utf-8')
    if verbose:
        filehandler.setLevel(logging.DEBUG)
    else:
        filehandler.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    fileformatter = logging.Formatter('%(asctime)s - %(levelname)8s - %(message)s')
    filehandler.setFormatter(fileformatter)
    # add the handler to logger
    logger.addHandler(filehandler)

    # create console handler displaying critical messages
    streamhandler = logging.StreamHandler()
    streamhandler.setLevel(logging.ERROR)
    # create formatter and add it to the handlers
    streamformatter = logging.Formatter('%(levelname)s: %(message)s')
    streamhandler.setFormatter(streamformatter)
    # add the handler to logger
    logger.addHandler(streamhandler)


def initializeEnvironment(mainScript):
    """
    conducts initialization activities provides a valid environment for further execution execution 
    
    The script is terminated if initialization encounters critical errors which prevent normal operations
    """

    # initialize the global settings variable
    global settings
    settings = {}
    
    # relative path are based on the mainScripts path
    scriptfilepath, scriptextension = os.path.splitext(os.path.abspath(mainScript))
    scriptpath, scriptname = os.path.split(scriptfilepath)
    settings['scriptpath'] = scriptpath
    settings['scriptname'] = scriptname

    # data directory ../dta must exist
    datadir = os.path.normpath(os.path.join(scriptpath, '../dta'))
    if not os.path.isdir(datadir):
        print "Terminating because data directory is missing ({})".format(datadir)
        sys.exit(1)
    else:
        # set path to cache files 
        settings['getRecordingsCache'] = os.path.join(datadir, 'getRecordings.cache')
        settings['checkCredentialsCache'] = os.path.join(datadir, 'checkCredentials.cache')
        
    # configuration file ../dta/Settings.ini must exist
    settings['inifile'] = os.path.join(datadir, 'Settings.ini')
    if not os.path.isfile(settings['inifile']):
        print "Terminating because configuration file is missing ({})".format(settings['inifile'])
        sys.exit(1)

    # recordings database ../dta/Recordings.db must exist
    settings['dbfile'] = os.path.join(datadir, 'Recordings.db')
    if not os.path.isfile(settings['dbfile']):
        print "Terminating because recordings database is missing ({})".format(settings['dbfile'])
        sys.exit(1)
    
    # log directory ../log must exist
    logdir = os.path.normpath(os.path.join(scriptpath, '../log'))
    if not os.path.isdir(logdir):
        print "Terminating because logging directory is missing ({})".format(logdir)
        sys.exit(1)
    else:
        settings['logfile'] = os.path.join(logdir, '{}.log'.format(scriptname))
    
    # recording directoy ../rec must exist
    settings['recdir'] = os.path.normpath(os.path.join(scriptpath, '../rec'))
    if not os.path.isdir(settings['recdir']):
        print "Terminating because recordings directory is missing ({})".format(settings['recdir'])
        sys.exit(1)
    
    config = ConfigParser.SafeConfigParser()
    config.read(settings['inifile'])
    settings['bong_username'] = config.get('bong.tv', 'username')
    settings['bong_password'] = config.get('bong.tv', 'password')
    settings['bong_server'] = config.get('bong.tv', 'server')

    if config.get('options', 'verbose').strip().lower() in ('true', 't', 'yes', 'y', 1):
        settings['verbose'] = True
    else:
        settings['verbose'] = False
       
    clim = config.get('options', 'cacheLifeInMinutes')
    pattern = re.compile("^[0-9]{1,3}$")
    if pattern.match(clim):
        settings['cacheLifeSpan'] = int(clim) * 60
    else:
        settings['cacheLifeSpan'] = 0

    ConfigureLogging(settings['logfile'], settings['verbose'])
    
def LogScriptStart():
    sk = ( 'scriptname'
         , 'scriptpath'
         , 'recdir'
         , 'inifile'
         , 'logfile'
         , 'dbfile'
         , 'getRecordingsCache'
         , 'checkCredentialsCache'
         , 'verbose'
         , 'cacheLifeSpan'
         , 'bong_username'
         , 'bong_password'
         , 'bong_server'
         )

    s = u"===== Script starting " + "="*58 + "\n\n"
    for k in sk:
        s = s + "settings[{!r}] = {!r}".format(k, settings[k]) + '\n'
    logger.info(s)
    
def LogScriptTermination():
    logger.info("Script terminating\n\n\n\n\n")

#!/usr/bin/env python

import logging
import glob
import logging.handlers
#from constants import logfilename

my_logger = logging.getLogger('MyLogger')
my_logger.setLevel(logging.DEBUG)
logfilename = 'events.log'

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s','%Y-%m-%d %H:%M:%S')
filehandler = logging.handlers.RotatingFileHandler(logfilename, maxBytes = 1000000, backupCount = 4)

filehandler.setFormatter(formatter)
my_logger.addHandler(filehandler)

def logmessage(loglevel, processname, message):
    if loglevel == 'debug':
        my_logger.debug('[%%s] %s', processname, message)
    elif loglevel == 'warning':
        my_logger.warning('[%s] %s', processname, message)
    elif loglevel == 'critical':
        my_logger.critical('[%s] %s', processname, message)
    elif loglevel == 'error':
        my_logger.error('[%s] %s', processname, message)
    elif loglevel == 'info':
        my_logger.info('[%s] %s', processname, message)

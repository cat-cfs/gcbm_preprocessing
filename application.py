from regionclipper import RegionClipper
from pathregistry import PathRegistry
import logging

def start_logging(fn=".\\script.log",fmode='w', use_console=True):
    #set up logging to print to console window and to log file
    #
    # From http://docs.python.org/2/howto/logging-cookbook.html#logging-cookbook
    #
    rootLogger = logging.getLogger()

    logFormatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', datefmt='%m-%d %H:%M')

    fileHandler = logging.FileHandler(fn, fmode)
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)
    if use_console:
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        rootLogger.addHandler(consoleHandler)

    rootLogger.setLevel(logging.INFO)

start_logging("log.txt")

class Application(object):
    def __init__(self, region_name, pathData):
        self.PathRegistry = PathRegistry(region_name, pathData)



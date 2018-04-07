import logging
import os


def start_logging(fn=".\\script.log", fmode='w', use_console=True):
    """
    Set up logging to print to console window and to log file
    From http://docs.python.org/2/howto/logging-cookbook.html#logging-cookbook
    """
    rootLogger = logging.getLogger()
    logFormatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M'
    )
    fileHandler = logging.FileHandler(fn, fmode)
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)
    if use_console:
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        rootLogger.addHandler(consoleHandler)

    rootLogger.setLevel(logging.INFO)
    return rootLogger


def create_script_log(scriptPath):
    """
    creates a log file in the current working directory where the script name
    is the name of the script file (with extension changed to .log)
    """
    s = os.path.basename(scriptPath)
    s = os.path.splitext(s)[0]
    s = "{0}.log".format(s)
    start_logging(s)

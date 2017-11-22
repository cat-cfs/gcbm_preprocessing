import arcpy
import logging
import time
import os
from contextlib import contextmanager

# Fixes interaction between time and multiprocessing modules.
os.environ["FOR_DISABLE_CONSOLE_CTRL_HANDLER"] = "1"
os.environ["FOR_IGNORE_EXCEPTIONS"] = "1"

GEOSTATS = "GeoStats"

@contextmanager
def arc_license(extension):
    try:
        while True:
            try:
                arcpy.CheckOutExtension(extension)
                break
            except:
                logging.info("Waiting for {} license...".format(extension))
                time.sleep(10)
        yield
    finally:
        arcpy.CheckInExtension(extension)

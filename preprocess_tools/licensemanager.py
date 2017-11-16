import arcpy
import logging
import time
from contextlib import contextmanager

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

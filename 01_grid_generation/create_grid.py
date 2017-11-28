import inspect
import math
import time
import logging
from preprocess_tools.licensemanager import *

class Fishnet(object):
    def __init__(self, inventory, resolution_degrees, ProgressPrinter):
        logging.info("Initializing class {}".format(self.__class__.__name__))
        self.ProgressPrinter = ProgressPrinter
        self.inventory = inventory
        self.resolution_degrees = resolution_degrees

        self.XYgrid = "XYgrid"
        self.XYgrid_temp = "XYgrid_temp"

    def createFishnet(self):
        with arc_license(Products.ARC) as arcpy:
            arcpy.env.workspace = self.inventory.getWorkspace()
            arcpy.env.overwriteOutput=True
            self.inventory.refreshBoundingBox()

            oCorner = self.inventory.getBottomLeftCorner()
            tCorner = self.inventory.getTopRightCorner()
            self.blc_x, self.blc_y = self.roundCorner(oCorner[0], oCorner[1], -1, self.resolution_degrees)
            self.trc_x, self.trc_y = self.roundCorner(tCorner[0], tCorner[1], 1, self.resolution_degrees)

            self.inventory_template = self.inventory.getLayerName()

            self.origin_coord = "{} {}".format(self.blc_x, self.blc_y)
            self.y_axis_coord = "{} {}".format(self.blc_x, self.blc_y+1)
            self.corner_coord = "{} {}".format(self.trc_x, self.trc_y)
            logging.info('Creating fishnet grid with {0}x{0} degree cell size in box bounded by ({1},{2})({3},{4})'.format(
                self.resolution_degrees, self.blc_x, self.blc_y, self.trc_x, self.trc_y))
            tasks = [
                lambda:arcpy.CreateFishnet_management(self.XYgrid_temp, self.origin_coord, self.y_axis_coord, self.resolution_degrees, self.resolution_degrees,
                    "", "", self.corner_coord, "NO_LABELS", self.inventory_template, "POLYGON"),
                lambda:self._createFields(),
                lambda:self._calculateFields()
            ]
            pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], len(tasks)).start()
            for t in tasks:
                t()
                pp.updateProgressV()
        pp.finish()

    def roundCorner(self, x, y, ud, res):
        if ud==1:
            rx = math.ceil(float(x)/res)*res
            ry = math.ceil(float(y)/res)*res
        elif ud==-1:
            rx = math.floor(float(x)/res)*res
            ry = math.floor(float(y)/res)*res
        else:
            raise Exception("Invalid value for 'ud'. Provide 1 (Round up) or -1 (Round down).")
        logging.info('Rounded bounding box corner coord ({0},{1}) to ({2},{3})'.format(x,y,rx,ry))
        return rx, ry

    def _createFields(self):
        field_name_types = {
            "CELL_ID":"LONG",
            "Shape_Area_Ha":"DOUBLE"
        }

        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], len(field_name_types), 1)
        pp.start()

        with arc_license(Products.ARC) as arcpy:
            for field_name in field_name_types:
                field_type = field_name_types[field_name]
                field_length = "10" if field_type.upper()=="TEXT" else ""
                arcpy.AddField_management(self.XYgrid_temp, field_name, field_type, "", "", field_length, "", "NULLABLE", "NON_REQUIRED", "")
                pp.updateProgressP()

        pp.finish()

    def _calculateFields(self):
        with arc_license(Products.ARC) as arcpy:
            functions = [
                lambda:arcpy.MakeFeatureLayer_management(self.XYgrid_temp, 'XYgrid_intersect'),
                # Only calculates grid cells that are intersecting with inventory
                lambda:arcpy.SelectLayerByLocation_management('XYgrid_intersect', 'INTERSECT', self.inventory.getFilter(), "", "NEW_SELECTION", "NOT_INVERT"),
                lambda:arcpy.CalculateField_management('XYgrid_intersect', "CELL_ID", "!OID!", "PYTHON_9.3"),
                lambda:arcpy.CalculateField_management('XYgrid_intersect', "Shape_Area_Ha", "!shape.area@hectares!", "PYTHON_9.3"),
                lambda:arcpy.CopyFeatures_management('XYgrid_intersect', self.XYgrid)
            ]

            pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], len(functions), 1).start()
            for f in functions:
                f()
                pp.updateProgressP()

        pp.finish()

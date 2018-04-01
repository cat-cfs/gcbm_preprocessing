import inspect
import math
import time
import logging


class Fishnet(object):
    def __init__(self, arcpy, resolution_degrees):
        self.arcpy = arcpy
        self.resolution_degrees = resolution_degrees

        self.XYgrid = "XYgrid"
        self.XYgrid_temp = "XYgrid_temp"

    def getBoundingBox(self, workspace, filter):
        self.arcpy.env.workspace = workspace
        desc = self.arcpy.Describe(filter)
        e = desc.extent
        return (e.XMin, e.YMin), (e.XMax, e.YMax)

    def createFishnet(self, workspace, workspace_filter):
        self.arcpy.env.workspace = workspace
        self.arcpy.env.overwriteOutput=True

        oCorner, tCorner = self.getBoundingBox(workspace, workspace_filter)

        self.blc_x, self.blc_y = self.roundCorner(oCorner[0], oCorner[1], -1, self.resolution_degrees)
        self.trc_x, self.trc_y = self.roundCorner(tCorner[0], tCorner[1], 1, self.resolution_degrees)

        self.inventory_template = workspace_filter

        self.origin_coord = "{} {}".format(self.blc_x, self.blc_y)
        self.y_axis_coord = "{} {}".format(self.blc_x, self.blc_y+1)
        self.corner_coord = "{} {}".format(self.trc_x, self.trc_y)
        logging.info('Creating fishnet grid with {0}x{0} degree cell size in box bounded by ({1},{2})({3},{4})'.format(
            self.resolution_degrees, self.blc_x, self.blc_y, self.trc_x, self.trc_y))
            
        self.arcpy.CreateFishnet_management(self.XYgrid_temp, self.origin_coord, self.y_axis_coord, self.resolution_degrees, self.resolution_degrees,
                "", "", self.corner_coord, "NO_LABELS", self.inventory_template, "POLYGON"),
        self._createFields(),
        self._calculateFields(workspace_filter)


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
        logging.info("creating fields")
        for field_name in field_name_types:
            field_type = field_name_types[field_name]
            field_length = "10" if field_type.upper()=="TEXT" else ""
            self.arcpy.AddField_management(self.XYgrid_temp, field_name, field_type, "", "", field_length, "", "NULLABLE", "NON_REQUIRED", "")


    def _calculateFields(self, workspace_filter):
        logging.info("calculating fields")
        self.arcpy.MakeFeatureLayer_management(self.XYgrid_temp, 'XYgrid_intersect'),
        # Only calculates grid cells that are intersecting with inventory
        self.arcpy.SelectLayerByLocation_management('XYgrid_intersect', 'INTERSECT', workspace_filter, "", "NEW_SELECTION", "NOT_INVERT"),
        self.arcpy.CalculateField_management('XYgrid_intersect', "CELL_ID", "!OID!", "PYTHON_9.3"),
        self.arcpy.CalculateField_management('XYgrid_intersect', "Shape_Area_Ha", "!shape.area@hectares!", "PYTHON_9.3"),
        self.arcpy.CopyFeatures_management('XYgrid_intersect', self.XYgrid)

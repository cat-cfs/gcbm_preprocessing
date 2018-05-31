'''
Author: Byron Smiley
Date: 2017_02_28

Description:
  1) Spatially joins the grid with the inventory polygon with the largest area
     within each grid cell
  
  2) Takes the combined stand-replacing disturbances layer and intersects
     it with the gridded inventory. Output is all polygons in the inventory that would have been
     established during the rollup period intersect with the disturbances that occurred on
     those areas for disturbances that occured between inventory date and rollback start year.
'''
import inspect
import logging
from preprocess_tools.licensemanager import *

class IntersectDisturbancesInventory(object):
    def __init__(self, inventory, spatialBoundaries, rollback_range, ProgressPrinter):
        logging.info("Initializing class {}".format(self.__class__.__name__))
        self.ProgressPrinter = ProgressPrinter
        self.inventory = inventory
        self.spatialBoundaries = spatialBoundaries
        self.rollback_start = rollback_range[0]

        # Temp Layers
        self.disturbances_layer = r"in_memory\disturbances_layer"
        self.disturbances_layer2 = r"in_memory\disturbances_layer2"
        self.inventory_layer3 = r"in_memory\inventory_layer3"
        self.SpBoundary_layer = r"in_memory\SpBoundary_layer"

    def runIntersectDisturbancesInventory(self):
        self.StudyArea = self.spatialBoundaries.getAreaFilter()["code"]
        self.studyAreaOperator = self.spatialBoundaries.getAreaFilter()["operator"]
        self.invVintage = self.inventory.getYear()
        self.rolledback_years = self.invVintage - self.rollback_start
        self.inv_workspace = self.inventory.getWorkspace()
        self.invAge_fieldName = self.inventory.getFieldNames()['age']

        # Field Names
        self.disturbance_fieldName = "DistYEAR"
        self.studyArea_fieldName = self.spatialBoundaries.getAreaFilter()["field"]
        self.establishmentDate_fieldName = self.inventory.getFieldNames()["establishment_date"]
        self.inv_dist_dateDiff = self.inventory.getFieldNames()['dist_date_diff']
        self.preDistAge = self.inventory.getFieldNames()['pre_dist_age']
        self.dist_type_field = self.inventory.getFieldNames()['dist_type']
        self.regen_delay_field = self.inventory.getFieldNames()['regen_delay']
        self.rollback_age_field = self.inventory.getFieldNames()['rollback_age']
        self.new_disturbance_field = self.inventory.getFieldNames()['new_disturbance_yr']

        self.gridded_inventory = r"{}\inventory_gridded".format(self.inv_workspace)
        self.disturbances = r"{}\MergedDisturbances".format(self.inv_workspace)
        self.temp_overlay = r"{}\temp_DisturbedInventory".format(self.inv_workspace)
        self.output = r"{}\DisturbedInventory".format(self.inv_workspace)

        tasks = [
            lambda:self.addFields(),
            lambda:self.selectInventoryRecords(),
            lambda:self.makeFeatureLayer(),
            lambda:self.selectDisturbanceRecords(),
            lambda:self.intersectLayers(),
            lambda:self.removeNonConcurring()
        ]
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], len(tasks)).start()
        for t in tasks:
            t()
            pp.updateProgressV()
        pp.finish()

    def addFields(self):
        field_names = [
            self.establishmentDate_fieldName,
            self.inv_dist_dateDiff,
            self.preDistAge,
            self.dist_type_field,
            self.regen_delay_field,
            self.rollback_age_field,
            self.new_disturbance_field
        ]
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], len(field_names), 1).start()
        with arc_license(Products.ARCINFO) as arcpy:
            for field_name in field_names:
                arcpy.AddField_management(self.gridded_inventory, field_name, "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                pp.updateProgressP()
        pp.finish()

    def selectInventoryRecords(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        with arc_license(Products.ARCINFO) as arcpy:
            inv_whereClause = '{} < {}'.format(arcpy.AddFieldDelimiters(self.inv_workspace, self.invAge_fieldName), self.rolledback_years)
            logging.info('Selecting inventory records where {}'.format(inv_whereClause))
            arcpy.Select_analysis(self.gridded_inventory, self.inventory_layer3, inv_whereClause)
        pp.finish()

    def clipMergedDisturbances(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        with arc_license(Products.ARCINFO) as arcpy:
            StudyArea_whereClause = '{} {} {}'.format(arcpy.AddFieldDelimiters(self.spatial_boundaries, self.studyArea_fieldName),
                self.studyAreaOperator, self.StudyArea)
            # Selecting Study area..."
            arcpy.Select_analysis(self.spatial_boundaries, self.SpBoundary_layer, StudyArea_whereClause)
            # Clipping merged disturbance to study area...
            arcpy.MakeFeatureLayer_management(self.disturbances, self.disturbances_layer)
        pp.finish()

    def makeFeatureLayer(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        with arc_license(Products.ARCINFO) as arcpy:
            arcpy.MakeFeatureLayer_management(self.disturbances, self.disturbances_layer)
        pp.finish()

    def selectDisturbanceRecords(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        with arc_license(Products.ARCINFO) as arcpy:
            #Select disturbance records that occur before inventory vintage
            dist_whereClause = '{} < {}'.format(arcpy.AddFieldDelimiters(self.disturbances, self.disturbance_fieldName), self.invVintage)
            logging.info('Selecting disturbance records that occur before inventory vintage: {}'.format(dist_whereClause))
            arcpy.Select_analysis(self.disturbances_layer, self.disturbances_layer2, dist_whereClause)
        pp.finish()

    def intersectLayers(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        with arc_license(Products.ARCINFO) as arcpy:
            # Intersecting disturbance and Inventory layers...
            logging.info('Intersecting disturbance and inventory layers')
            arcpy.Union_analysis([self.inventory_layer3,self.disturbances_layer2], self.temp_overlay, "ALL")
        pp.finish()

    def removeNonConcurring(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        with arc_license(Products.ARCINFO) as arcpy:
            nonConcurrence_whereClause = "{} > 0".format(arcpy.AddFieldDelimiters(self.output, "CELL_ID"))
            # Removing disturbance polygons where inventory doesnt spatially concur that a disturbance took place...
            logging.info("Removing stand-replacing disturbance polygons with {} where inventory doesn't spatially concur that a disturbance took place".format(nonConcurrence_whereClause))
            arcpy.Select_analysis(self.temp_overlay, self.output, nonConcurrence_whereClause)
            arcpy.RepairGeometry_management(self.output, "DELETE_NULL")
        pp.finish()

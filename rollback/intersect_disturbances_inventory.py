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
    def __init__(self, inventory_workspace, inventory_year,
                 inventory_field_names, spatial_boundaries_area_filter,
                 rollback_start):

        self.inventory_workspace = inventory_workspace
        self.inventory_year = inventory_year
        self.inventory_field_names = inventory_field_names
        self.spatial_boundaries_area_filter = spatial_boundaries_area_filter
        self.rollback_start = rollback_start

        # Temp Layers
        self.disturbances_layer = r"in_memory\disturbances_layer"
        self.disturbances_layer2 = r"in_memory\disturbances_layer2"
        self.inventory_layer3 = r"in_memory\inventory_layer3"
        self.SpBoundary_layer = r"in_memory\SpBoundary_layer"

    def runIntersectDisturbancesInventory(self):
        self.StudyArea = self.spatial_boundaries_area_filter["code"]
        self.studyAreaOperator = "="
        self.rolledback_years = self.inventory_year - self.rollback_start
        self.invAge_fieldName = self.inventory_field_names['age']

        # Field Names
        self.disturbance_fieldName = "DistYEAR"
        self.studyArea_fieldName = self.spatial_boundaries_area_filter["field"]
        self.establishmentDate_fieldName = self.inventory_field_names["establishment_date"]
        self.inv_dist_dateDiff = self.inventory_field_names['dist_date_diff']
        self.preDistAge = self.inventory_field_names['pre_dist_age']
        self.dist_type_field = self.inventory_field_names['dist_type']
        self.regen_delay_field = self.inventory_field_names['regen_delay']
        self.rollback_age_field = self.inventory_field_names['rollback_age']
        self.new_disturbance_field = self.inventory_field_names['new_disturbance_yr']

        self.gridded_inventory = r"{}\inventory_gridded".format(self.inventory_workspace)
        self.disturbances = r"{}\MergedDisturbances".format(self.inventory_workspace)
        self.temp_overlay = r"{}\temp_DisturbedInventory".format(self.inventory_workspace)
        self.output = r"{}\DisturbedInventory".format(self.inventory_workspace)

        self.addFields()
        self.selectInventoryRecords(self.inventory_workspace, invAge_fieldName, rolledback_years)
        self.makeFeatureLayer()
        self.selectDisturbanceRecords()
        self.intersectLayers()
        self.removeNonConcurring()


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
        with arc_license(Products.ARC) as arcpy:
            for field_name in field_names:
                arcpy.AddField_management(self.gridded_inventory, field_name, "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    def selectInventoryRecords(self):
        with arc_license(Products.ARC) as arcpy:
            inv_whereClause = '{} < {}'.format(arcpy.AddFieldDelimiters(self.inventory_workspace, self.invAge_fieldName), self.rolledback_years)
            logging.info('Selecting inventory records where {}'.format(inv_whereClause))
            arcpy.Select_analysis(self.gridded_inventory, self.inventory_layer3, inv_whereClause)


    def makeFeatureLayer(self):
        with arc_license(Products.ARC) as arcpy:
            arcpy.MakeFeatureLayer_management(self.disturbances, self.disturbances_layer)


    def selectDisturbanceRecords(self):
        with arc_license(Products.ARC) as arcpy:
            #Select disturbance records that occur before inventory vintage
            dist_whereClause = '{} < {}'.format(arcpy.AddFieldDelimiters(self.disturbances, self.disturbance_fieldName), self.inventory_year)
            logging.info('Selecting disturbance records that occur before inventory vintage: {}'.format(dist_whereClause))
            arcpy.Select_analysis(self.disturbances_layer, self.disturbances_layer2, dist_whereClause)

    def intersectLayers(self):
        with arc_license(Products.ARC) as arcpy:
            # Intersecting disturbance and Inventory layers...
            logging.info('Intersecting disturbance and inventory layers')
            arcpy.Union_analysis([self.inventory_layer3,self.disturbances_layer2], self.temp_overlay, "ALL")

    def removeNonConcurring(self):
        with arc_license(Products.ARC) as arcpy:
            nonConcurrence_whereClause = "{} > 0".format(arcpy.AddFieldDelimiters(self.output, "CELL_ID"))
            # Removing disturbance polygons where inventory doesnt spatially concur that a disturbance took place...
            logging.info("Removing stand-replacing disturbance polygons with {} where inventory doesn't spatially concur that a disturbance took place".format(nonConcurrence_whereClause))
            arcpy.Select_analysis(self.temp_overlay, self.output, nonConcurrence_whereClause)
            arcpy.RepairGeometry_management(self.output, "DELETE_NULL")

import os
import logging
import inspect

import pgdata


class IntersectDisturbancesInventory(object):
    def __init__(
        self,
        inventory_workspace, inventory_year,
        inventory_field_names,
        rollback_start
    ):
        self.inventory_workspace = inventory_workspace
        self.inventory_year = inventory_year
        self.inventory_field_names = inventory_field_names
        self.rollback_start = rollback_start
        # point to the sql folder within rollback module
        sql_path = os.path.join(os.path.dirname(inspect.stack()[0][1]), 'sql')
        self.db = pgdata.connect(sql_path=sql_path)

    def intersect_disturbances_inventory(self):
        logging.info("Intersecting rollback disturbances and inventory")
        self.rolledback_years = self.inventory_year - self.rollback_start
        self.age_field = self.inventory_field_names['age']
        self.disturbance_field = "year"

        self.establishment_date_field = self.inventory_field_names["establishment_date"]
        self.inv_dist_date_diff_field = self.inventory_field_names['dist_date_diff']
        self.pre_dist_age_field = self.inventory_field_names['pre_dist_age']
        self.dist_type_field = self.inventory_field_names['dist_type']
        self.regen_delay_field = self.inventory_field_names['regen_delay']
        self.rollback_age_field = self.inventory_field_names['rollback_age']
        self.new_disturbance_field = self.inventory_field_names['new_disturbance_yr']
        self.grid = 'preprocessing.grid'

        self.run_intersect()

        #self.addFields()
        #self.selectInventoryRecords()
        #self.makeFeatureLayer()
        #self.selectDisturbanceRecords()
        #self.intersectLayers()
        #self.removeNonConcurring()

    def run_intersect(self):
        blocks = [b for b in self.db['preprocessing.blocks'].distinct('block_id')]
        for block in blocks[0]:
            self.db.execute(
                self.db.queries['intersect_disturbances_inventory'], (block,)
            )

    def selectInventoryRecords(self):
        inv_whereClause = '{} < {}'.format(self.arcpy.AddFieldDelimiters(self.inventory_workspace, self.invAge_fieldName), self.rolledback_years)
        logging.info('Selecting inventory records where {}'.format(inv_whereClause))
        self.arcpy.Select_analysis(self.gridded_inventory, self.inventory_layer3, inv_whereClause)

    def makeFeatureLayer(self):
        logging.info("make feature layer")
        self.arcpy.MakeFeatureLayer_management(self.disturbances, self.disturbances_layer)

    def selectDisturbanceRecords(self):
        #Select disturbance records that occur before inventory vintage
        dist_whereClause = '{} < {}'.format(self.arcpy.AddFieldDelimiters(self.disturbances, self.disturbance_fieldName), self.inventory_year)
        logging.info('Selecting disturbance records that occur before inventory vintage: {}'.format(dist_whereClause))
        self.arcpy.Select_analysis(self.disturbances_layer, self.disturbances_layer2, dist_whereClause)

    def intersectLayers(self):
        # Intersecting disturbance and Inventory layers...
        logging.info('Intersecting disturbance and inventory layers')
        self.arcpy.Union_analysis([self.inventory_layer3,self.disturbances_layer2], self.temp_overlay, "ALL")

    def removeNonConcurring(self):
        nonConcurrence_whereClause = "{} > 0".format(self.arcpy.AddFieldDelimiters(self.output, "CELL_ID"))
        # Removing disturbance polygons where inventory doesnt spatially concur that a disturbance took place...
        logging.info("Removing stand-replacing disturbance polygons with {} where inventory doesn't spatially concur that a disturbance took place".format(nonConcurrence_whereClause))
        self.arcpy.Select_analysis(self.temp_overlay, self.output, nonConcurrence_whereClause)
        self.arcpy.RepairGeometry_management(self.output, "DELETE_NULL")

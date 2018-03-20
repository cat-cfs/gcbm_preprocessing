import csv
import random
import numpy as np
import os
import sys
import inspect
import logging
from dbfread import DBF

class CalculateDistDEdifference(object):
    def __init__(self, arcpy, inventory_workspace, inventory_year, inventory_field_names):
        self.arcpy = arcpy
        self.inventory_workspace = inventory_workspace
        self.inventory_year = inventory_year
        self.inventory_field_names = inventory_field_names

        # VARIABLES:
        self.disturbedInventory = "DisturbedInventory"
        self.disturbedInventory_layer = "disturbedInventory_layer"

    def calculateDistDEdifference(self):
        logging.info("computing disturbance/date of establishment differences")
        self.arcpy.env.workspace = self.inventory_workspace
        self.arcpy.env.overwriteOutput = True
        #local variables

        self.inv_dist_dateDiff = self.inventory_field_names['dist_date_diff']

        self.makeLayers()
        self.calculateFields()

    def makeLayers(self):
        logging.info("creating working layer")
        self.arcpy.MakeFeatureLayer_management(self.disturbedInventory, self.disturbedInventory_layer)

    def calculateFields(self):
        logging.info("computing fields")

        #Calculate date of establishment and difference between date of establishment (inventory) and date of stand-replacing disturbance
        logging.info('Calculating date of establishment and difference between date of establishment (inventory) and date of disturbance')
        cur = self.arcpy.UpdateCursor(self.disturbedInventory_layer)
        for row in cur:
            # The variable 'age' will get the value from the column
            age = row.getValue(self.inventory_field_names['age'])
            DE = (self.inventory_year - age)
            row.setValue(self.inventory_field_names['establishment_date'], DE)
            DistDate = row.getValue(self.inventory_field_names['disturbance_yr'])
            yearDiff = (DE - DistDate)
            inv_dist_dateDiff = self.inventory_field_names['dist_date_diff']
            if DistDate > 0:
                row.setValue(inv_dist_dateDiff, yearDiff)
            else:
                row.setValue(inv_dist_dateDiff, 0)
            cur.updateRow(row)
 

class CalculateNewDistYr(object):
    def __init__(self, arcpy, inventory_workspace, inventory_year,
                 inventory_field_names, rollback_start,
                 harv_yr_field, dist_age_prop_file_path):
        self.arcpy = arcpy
        self.inventory_workspace = inventory_workspace
        self.inventory_field_names = inventory_field_names
        self.rollback_start = rollback_start
        self.inv_vintage = inventory_year
        self.harv_yr_field = harv_yr_field
        self.dist_age_prop_file_path = dist_age_prop_file_path
        #Constants
        self.DisturbedInventory = "DisturbedInventory"
        self.disturbedInventory_layer = "disturbedInventory_layer"

    def calculateNewDistYr(self):
        logging.info("computing new disturbance years")
        self.arcpy.env.workspace = self.inventory_workspace
        self.arcpy.env.overwriteOutput = True
        #local variables
        self.inv_age_field = self.inventory_field_names['age']
        self.establishment_date_field = self.inventory_field_names['establishment_date']
        self.disturbance_yr = self.inventory_field_names['disturbance_yr']
        self.new_disturbance_field = self.inventory_field_names['new_disturbance_yr']
        self.inv_dist_date_diff_field = self.inventory_field_names['dist_date_diff']
        self.dist_type_field = self.inventory_field_names['dist_type']
        self.regen_delay_field = self.inventory_field_names['regen_delay']
        self.preDistAge = self.inventory_field_names['pre_dist_age']
        self.rollback_vintage_field = self.inventory_field_names['rollback_age']

        self.makeLayers()
        self.calculateDistType()
        self.calculateRegenDelay()
        self.calculatePreDistAge(self.dist_age_prop_file_path)
        self.calculateRolledBackInvAge()

    def makeLayers(self):
        logging.info("making layers")
        self.arcpy.MakeFeatureLayer_management(self.DisturbedInventory, self.disturbedInventory_layer)

    def calculateDistType(self):
        logging.info("calculating disturbance type")
        cur = self.arcpy.UpdateCursor(self.disturbedInventory_layer)
        for row in cur:
            dist_year = row.getValue(self.disturbance_yr)
            harv_year = row.getValue(self.harv_yr_field)
            if dist_year == harv_year:
                row.setValue(self.dist_type_field, "2")
            else:
                row.setValue(self.dist_type_field, "1")
            cur.updateRow(row)

    def calculateRegenDelay(self):
        logging.info("calculating regen delay")

        cur = self.arcpy.UpdateCursor(self.disturbedInventory_layer)
        for row in cur:
            age_diff = row.getValue(self.inv_dist_date_diff_field)
            est_year = row.getValue(self.establishment_date_field)
            dist_year = row.getValue(self.disturbance_yr)
            inv_derived_disturbance = est_year #removed -1
            if age_diff > 0:
                row.setValue(self.regen_delay_field, age_diff)
                row.setValue(self.new_disturbance_field, dist_year)
            elif age_diff <= 0:
                # Disturbance can't occur after establishment year - set to year before establishment.
                row.setValue(self.regen_delay_field, 0)
                row.setValue(self.new_disturbance_field, inv_derived_disturbance)

            cur.updateRow(row)

    def calculatePreDistAge(self, dist_age_prop_path):
        logging.info("Calculating pre disturbance age using '{}' to select age"
                     .format(dist_age_prop_path))
        dist_age_props = {}
        with open(dist_age_prop_path, "r") as age_prop_file:
            reader = csv.reader(age_prop_file)
            reader.next() # skip header
            for dist_type, age, prop in reader:
                dist_type = int(dist_type)
                dist_ages = dist_age_props.get(dist_type)
                if not dist_ages:
                    dist_age_props[dist_type] = {}
                    dist_ages = dist_age_props[dist_type]
                dist_ages[age] = float(prop)

        age_distributors = {}
        for dist_type, age_props in dist_age_props.iteritems():
            age_distributors[dist_type] = RollbackDistributor(**age_props)

        cur = self.arcpy.UpdateCursor(self.disturbedInventory_layer)
        for row in cur:
            dist_type = int(row.getValue(self.dist_type_field))
            age_distributor = age_distributors.get(dist_type)
            if not age_distributor:
                print "No age distributor for layer disturbance type {} - skipping.".format(dist_type)
                continue

            row.setValue(self.preDistAge, age_distributor.next())
            cur.updateRow(row)

        for dist_type, age_distributor in age_distributors.iteritems():
            logging.info("Age picks for disturbance type {}:{}".format(dist_type,str(age_distributor)))

    def calculateRolledBackInvAge(self):
        logging.info("calculating rollback inventory age")
        cur = self.arcpy.UpdateCursor(self.disturbedInventory_layer)
        for row in cur:
            pre_DistAge = row.getValue(self.preDistAge)
            dist_yearNew = row.getValue(self.new_disturbance_field)
            row.setValue(self.rollback_vintage_field, (pre_DistAge + self.rollback_start - dist_yearNew))

            cur.updateRow(row)
        # print self.arcpy.GetMessages()


class RollbackDistributor(object):
    def __init__(self, **age_proportions):
        self._rand = random.Random()
        self._ages = []
        for age, proportion in age_proportions.iteritems():
            self._ages.extend([age] * int(100.00 * proportion))

        self._rand.shuffle(self._ages)
        self._choices = {age: 0 for age in age_proportions.keys()}

    def __str__(self):
        return str(self._choices)

    def next(self):
        age = self._rand.choice(self._ages)
        self._choices[age] += 1
        return int(age)


class updateInvRollback(object):
    def __init__(self, arcpy, inventory_workspace, inventory_year, inventory_field_names,
                 inventory_classifiers, rollbackInvOut, rollbackDisturbancesOutput, rollback_range,
                 resolution, sb_percent, reporting_classifiers):
        self.arcpy = arcpy
        self.inventory_workspace = inventory_workspace
        self.inventory_year = inventory_year
        self.inventory_field_names = inventory_field_names
        self.inventory_classifiers = inventory_classifiers

        self.rollbackDisturbanceOutput = rollbackDisturbancesOutput
        self.rasterOutput = rollbackInvOut
        self.resolution = resolution
        self.slashburn_percent = sb_percent
        self.reporting_classifiers = reporting_classifiers

        #data
        self.gridded_inventory = "inventory_gridded"
        self.disturbedInventory = "DisturbedInventory"
        self.RolledBackInventory = "inventory_gridded_1990"
        self.rollback_range = rollback_range
        self.inv_vintage = inventory_year
        self.rollback_start = rollback_range[0]

        #layers
        self.RolledBackInventory_layer = "RolledBackInventory_layer"
        self.gridded_inventory_layer = "gridded_inventory_layer"
        self.disturbedInventory_layer = "disturbedInventory_layer"

    def updateInvRollback(self):
        logging.info("updating rollback inventory")
        self.arcpy.env.workspace = self.inventory_workspace
        self.arcpy.env.overwriteOutput = True
        #local variables
        #fields
        self.inv_age_field = self.inventory_field_names['age']
        self.new_disturbance_field = self.inventory_field_names['new_disturbance_yr']
        self.dist_type_field = self.inventory_field_names['dist_type']
        self.regen_delay_field = self.inventory_field_names['regen_delay']
        self.rollback_vintage_field = self.inventory_field_names['rollback_age']
        self.CELL_ID = "CELL_ID"

        self.makeLayers1()
        self.remergeDistPolyInv()
        self.makeLayers2()
        self.rollbackAgeNonDistStands()
        self.generateSlashburn()
        self.exportRollbackDisturbances()
        return self.exportRollbackInventory()

    def makeLayers1(self):
        logging.info("making layers")
        self.arcpy.MakeFeatureLayer_management(self.gridded_inventory, self.gridded_inventory_layer)
        self.arcpy.MakeFeatureLayer_management(self.disturbedInventory, self.disturbedInventory_layer)

    def remergeDistPolyInv(self):
        logging.info("re-merging layers")
        self.arcpy.Update_analysis(self.gridded_inventory_layer, self.disturbedInventory_layer,
            self.RolledBackInventory, "BORDERS", "0.25 Meters")

    def makeLayers2(self):
        logging.info("making layers")
        self.arcpy.MakeFeatureLayer_management(self.RolledBackInventory, self.RolledBackInventory_layer)

    def rollbackAgeNonDistStands(self):
        logging.info('Rolling back ages for age{}'.format(self.rollback_start))
        
        cur = self.arcpy.UpdateCursor(self.RolledBackInventory_layer)
        for row in cur:
            rolledBackAge = row.getValue(self.rollback_vintage_field)
            RegenDelay = row.getValue(self.regen_delay_field)
            invAge = row.getValue(self.inv_age_field)
            if rolledBackAge is None:
                row.setValue(self.rollback_vintage_field, (invAge - (self.inv_vintage - self.rollback_start)))
                row.setValue(self.regen_delay_field, 0)
            cur.updateRow(row)

    def generateSlashburn(self):
        logging.info("generating rollback slashburn")
        year_range = range(self.rollback_range[0], self.rollback_range[1]+1)
        # print "Start of slashburn processing..."
        PercSBofCC = self.slashburn_percent
        
        self.arcpy.MakeFeatureLayer_management(self.RolledBackInventory_layer, "temp_rollback")
        expression1 = '{} = {}'.format(self.arcpy.AddFieldDelimiters("temp_rollback", self.dist_type_field), 2)
        logging.info('Making slashburn for the range {}-{}'.format(self.rollback_range[0],self.rollback_range[1]))
        logging.info('Selecting {}% of the harvest area in each year as slashburn and adding it to the rollback disturbances...'.format(PercSBofCC))
        # Create SB records for each timestep
        for year in range(self.rollback_range[0], self.rollback_range[1] + 1):
            expression2 = '{} = {}'.format(self.arcpy.AddFieldDelimiters("temp_rollback", self.new_disturbance_field), year)
            self.arcpy.SelectLayerByAttribute_management("temp_rollback", "NEW_SELECTION", expression2)
            self.arcpy.SelectLayerByAttribute_management("temp_rollback", "SUBSET_SELECTION", expression1)
            if int(self.arcpy.GetCount_management("temp_rollback").getOutput(0)) > 0:
                number_features = [row[0] for row in self.arcpy.da.SearchCursor("temp_rollback", "OBJECTID")]
                temp_rollback_count = int(self.arcpy.GetCount_management("temp_rollback").getOutput(0))
                features2Bselected = random.sample(number_features,(int(np.ceil(round(float(temp_rollback_count * PercSBofCC)/100)))))
                features2Bselected.append(0)
                features2Bselected = str(tuple(features2Bselected)).rstrip(',)') + ')'
                selectExpression = '{} IN {}'.format(self.arcpy.AddFieldDelimiters("temp_rollback", "OBJECTID"), features2Bselected)
                self.arcpy.SelectLayerByAttribute_management("temp_rollback","NEW_SELECTION", selectExpression)
                self.arcpy.CopyFeatures_management("temp_rollback","temp_SB")
                self.arcpy.CalculateField_management("temp_SB", "DistType", 13, "PYTHON", "")
                self.arcpy.Append_management("temp_SB", self.RolledBackInventory_layer)
            self.arcpy.SelectLayerByAttribute_management("temp_rollback", "CLEAR_SELECTION")

    def exportRollbackDisturbances(self):

        #Export rollback disturbances

        logging.info('Exporting rollback disturbances to {}'.format(self.rollbackDisturbanceOutput))
        dirname =  os.path.dirname(self.rollbackDisturbanceOutput)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        dissolveFields = [self.dist_type_field, self.new_disturbance_field,self.regen_delay_field, self.CELL_ID]
        selectClause =  "{} IS NOT NULL".format(self.new_disturbance_field)

        self.arcpy.SelectLayerByAttribute_management(self.RolledBackInventory_layer, "NEW_SELECTION", selectClause)
        self.arcpy.Dissolve_management(self.RolledBackInventory_layer, self.rollbackDisturbanceOutput, dissolveFields,
            "","SINGLE_PART","DISSOLVE_LINES")

    def exportRollbackInventory(self):

        logging.info('Exporting rolled back inventory rasters to {}'.format(self.rasterOutput))
        rasterMeta = []
        self.arcpy.env.overwriteOutput = True

        fields = {
            "age": self.inventory_field_names["rollback_age"],
            "species": self.inventory_field_names["species"]
        }

        for classifierName, fieldName in self.reporting_classifiers.items():
            if not classifierName in fields:
                fields.update({classifierName:fieldName})
            else:
                raise KeyError("duplicated reporting classifier: '{}'".format(classifierName))

        if not os.path.exists(self.rasterOutput):
            os.makedirs(self.rasterOutput)
        for classifier_name, classifier_attribute in self.inventory_classifiers.items():
            logging.info('Exporting classifer {} from {}'.format(classifier_name, os.path.join(self.inventory_workspace,self.RolledBackInventory)))
            field_name = classifier_attribute
            file_path = os.path.join(self.rasterOutput, "{}.tif".format(classifier_name))
            attribute_table_path = os.path.join(self.rasterOutput, "{}.tif.vat.dbf".format(classifier_name))
            self.arcpy.FeatureToRaster_conversion(self.RolledBackInventory, field_name, file_path, self.resolution)
            rasterMeta.append(
                {
                    "file_path": file_path,
                    "attribute": classifier_name,
                    "attribute_table": self.createAttributeTable(attribute_table_path, field_name)
                }
            )
        for attr in fields:
            logging.info('Exporting field {} from {}'.format(attr, os.path.join(self.inventory_workspace,self.RolledBackInventory)))
            field_name = fields[attr]
            file_path = os.path.join(self.rasterOutput,"{}.tif".format(attr))
            attribute_table_path = os.path.join(self.rasterOutput, "{}.tif.vat.dbf".format(attr))
            self.arcpy.FeatureToRaster_conversion(self.RolledBackInventory, field_name, file_path, self.resolution)
            rasterMeta.append(
                {
                    "file_path": file_path,
                    "attribute": attr,
                    "attribute_table": self.createAttributeTable(attribute_table_path, field_name)
                })

        return rasterMeta

    def createAttributeTable(self, dbf_path, field_name):
        # Creates an attribute table with the field name given
        # to be used in the tiler along with the tif. This is
        # necessary for fields that are not integers.
        attr_table = {}
        for row in DBF(dbf_path):
            if len(row)<3:
                return None
            attr_table.update({row.items()[0][1]: [row.items()[-1][1]]})
        return attr_table

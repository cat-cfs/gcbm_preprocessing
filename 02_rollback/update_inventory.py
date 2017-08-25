import archook
archook.get_arcpy()
import arcpy
import csv
import random
import os
import sys
import inspect
import logging
from dbfread import DBF

class CalculateDistDEdifference(object):
    def __init__(self, inventory, ProgressPrinter):
        logging.info("Initializing class {}".format(self.__class__.__name__))
        self.ProgressPrinter = ProgressPrinter
        self.inventory = inventory

        # VARIABLES:
        self.disturbedInventory = "DisturbedInventory"
        self.disturbedInventory_layer = "disturbedInventory_layer"

    def calculateDistDEdifference(self):
        arcpy.env.workspace = self.inventory.getWorkspace()
        arcpy.env.overwriteOutput = True
        #local variables
        self.invAge_fieldName = self.inventory.getFieldNames()['age']
        self.invVintage = self.inventory.getYear()
        self.establishmentDate_fieldName = self.inventory.getFieldNames()['establishment_date']
        self.disturbance_fieldName = self.inventory.getFieldNames()['disturbance_yr']
        self.inv_dist_dateDiff = self.inventory.getFieldNames()['dist_date_diff']

        tasks = [
            lambda:self.makeLayers(),
            lambda:self.calculateFields()
        ]
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], len(tasks)).start()
        for t in tasks:
            t()
            pp.updateProgressV()
        pp.finish()

    def makeLayers(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        arcpy.MakeFeatureLayer_management(self.disturbedInventory, self.disturbedInventory_layer)
        pp.finish()

    def calculateFields(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        #Calculate date of establishment and difference between date of establishment (inventory) and date of stand-replacing disturbance
        logging.info('Calculating date of establishment and difference between date of establishment (inventory) and date of disturbance')
        cur = arcpy.UpdateCursor(self.disturbedInventory_layer)
        for row in cur:
            # The variable 'age' will get the value from the column
            age = row.getValue(self.invAge_fieldName)
            DE = (self.invVintage - age)
            row.setValue(self.establishmentDate_fieldName, DE)
            DistDate = row.getValue(self.disturbance_fieldName)
            yearDiff = (DE - DistDate)
            if DistDate > 0:
                row.setValue(self.inv_dist_dateDiff, yearDiff)
            else:
                row.setValue(self.inv_dist_dateDiff, 0)
            cur.updateRow(row)
        pp.finish()

class CalculateNewDistYr(object):
    def __init__(self, inventory, rollback_range, harv_yr_field, ProgressPrinter):
        logging.info("Initializing class {}".format(self.__class__.__name__))
        self.ProgressPrinter = ProgressPrinter
        self.inventory = inventory
        self.rollback_start = rollback_range[0]
        self.inv_vintage = inventory.getYear()
        self.harv_yr_field = harv_yr_field

        #Constants
        self.DisturbedInventory = "DisturbedInventory"
        self.disturbedInventory_layer = "disturbedInventory_layer"

    def calculateNewDistYr(self):
        arcpy.env.workspace = self.inventory.getWorkspace()
        arcpy.env.overwriteOutput = True
        #local variables
        self.inv_age_field = self.inventory.getFieldNames()['age']
        self.establishment_date_field = self.inventory.getFieldNames()['establishment_date']
        self.disturbance_yr = self.inventory.getFieldNames()['disturbance_yr']
        self.new_disturbance_field = self.inventory.getFieldNames()['new_disturbance_yr']
        self.inv_dist_date_diff_field = self.inventory.getFieldNames()['dist_date_diff']
        self.dist_type_field = self.inventory.getFieldNames()['dist_type']
        self.regen_delay_field = self.inventory.getFieldNames()['regen_delay']
        self.preDistAge = self.inventory.getFieldNames()['pre_dist_age']
        self.rollback_vintage_field = self.inventory.getFieldNames()['rollback_age']

        tasks = [
            lambda:self.makeLayers(),
            lambda:self.calculateDistType(),
            lambda:self.calculateRegenDelay(),
            lambda:self.calculatePreDistAge(),
            lambda:self.calculateRolledBackInvAge()
        ]
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], len(tasks)).start()
        for t in tasks:
            t()
            pp.updateProgressV()
        pp.finish()

    def makeLayers(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        arcpy.MakeFeatureLayer_management(self.DisturbedInventory, self.disturbedInventory_layer)
        # print(arcpy.GetMessages())
        pp.finish()

    def calculateDistType(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        cur = arcpy.UpdateCursor(self.disturbedInventory_layer)
        for row in cur:
            dist_year = row.getValue(self.disturbance_yr)
            harv_year = row.getValue(self.harv_yr_field)
            if dist_year == harv_year:
                row.setValue(self.dist_type_field, "2")
            else:
                row.setValue(self.dist_type_field, "1")
            cur.updateRow(row)
        pp.finish()

    def calculateRegenDelay(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        cur = arcpy.UpdateCursor(self.disturbedInventory_layer)
        for row in cur:
            age_diff = row.getValue(self.inv_dist_date_diff_field)
            est_year = row.getValue(self.establishment_date_field)
            dist_year = row.getValue(self.disturbance_yr)
            inv_derived_disturbance = est_year - 1
            if age_diff > 0:
                row.setValue(self.regen_delay_field, age_diff)
                row.setValue(self.new_disturbance_field, dist_year)
            elif age_diff <= 0:
                # Disturbance can't occur after establishment year - set to year before establishment.
                row.setValue(self.regen_delay_field, 0)
                row.setValue(self.new_disturbance_field, inv_derived_disturbance)

            cur.updateRow(row)
        pp.finish()

    def calculatePreDistAge(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        logging.info('Calculating pre disturbance age using {}\\02_rollback\\DistAgeProp.csv to select age'.format(sys.path[0]))
        dist_age_props = {}
        with open("{}\\02_rollback\\DistAgeProp.csv".format(sys.path[0]), "r") as age_prop_file:
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

        cur = arcpy.UpdateCursor(self.disturbedInventory_layer)
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
        pp.finish()

    def calculateRolledBackInvAge(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        cur = arcpy.UpdateCursor(self.disturbedInventory_layer)
        for row in cur:
            pre_DistAge = row.getValue(self.preDistAge)
            dist_yearNew = row.getValue(self.new_disturbance_field)
            row.setValue(self.rollback_vintage_field, (pre_DistAge + self.rollback_start - dist_yearNew))
            # if dist_yearNew == rollback_year:
                # row.setValue(rollback_vintage_field, (pre_DistAge + rollback_year - dist_yearNew))
            # else:
                # row.setValue(rollback_vintage_field, (pre_DistAge + rollback_year - dist_yearNew + 1))

            cur.updateRow(row)
        # print arcpy.GetMessages()
        pp.finish()


class RollbackDistributor(object):
    def __init__(self, **age_proportions):
        logging.info("Initializing class {}".format(self.__class__.__name__))
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
    def __init__(self, inventory, rollbackInvOut, rollbackDisturbances, rollback_range, resolution, ProgressPrinter):
        logging.info("Initializing class {}".format(self.__class__.__name__))
        self.ProgressPrinter = ProgressPrinter
        self.inventory = inventory
        self.rollbackDisturbanceOutput = rollbackDisturbances
        self.rasterOutput = rollbackInvOut
        self.resolution = resolution

        #data
        self.gridded_inventory = "inventory_gridded"
        self.disturbedInventory = "DisturbedInventory"
        self.RolledBackInventory = "inventory_gridded_1990"
        self.rollback_range = rollback_range
        self.inv_vintage = rollback_range[1]
        self.rollback_start = rollback_range[0]

        #layers
        self.RolledBackInventory_layer = "RolledBackInventory_layer"
        self.gridded_inventory_layer = "gridded_inventory_layer"
        self.disturbedInventory_layer = "disturbedInventory_layer"

    def updateInvRollback(self):
        arcpy.env.workspace = self.inventory.getWorkspace()
        arcpy.env.overwriteOutput = True
        #local variables
        #fields
        self.inv_age_field = self.inventory.getFieldNames()['age']
        self.new_disturbance_field = self.inventory.getFieldNames()['new_disturbance_yr']
        self.dist_type_field = self.inventory.getFieldNames()['dist_type']
        self.regen_delay_field = self.inventory.getFieldNames()['regen_delay']
        self.rollback_vintage_field = self.inventory.getFieldNames()['rollback_age']
        self.CELL_ID = "CELL_ID"

        tasks = [
            lambda:self.makeLayers1(),
            lambda:self.remergeDistPolyInv(),
            lambda:self.makeLayers2(),
            lambda:self.rollbackAgeNonDistStands(),
            lambda:self.makeSlashburn(),
            lambda:self.exportRollbackDisturbances(),
            lambda:self.exportRollbackInventory()
        ]
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], len(tasks)).start()
        for t in tasks:
            t()
            pp.updateProgressV()
        pp.finish()

    def makeLayers1(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        arcpy.MakeFeatureLayer_management(self.gridded_inventory, self.gridded_inventory_layer)
        arcpy.MakeFeatureLayer_management(self.disturbedInventory, self.disturbedInventory_layer)
        pp.finish()

    def remergeDistPolyInv(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        arcpy.Update_analysis(self.gridded_inventory_layer, self.disturbedInventory_layer,
            self.RolledBackInventory, "BORDERS", "0.25 Meters")
        self.inventory.setLayerName(self.RolledBackInventory)
        pp.finish()

    def makeLayers2(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        arcpy.MakeFeatureLayer_management(self.RolledBackInventory, self.RolledBackInventory_layer)
        pp.finish()

    def rollbackAgeNonDistStands(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        logging.info('Rolling back ages for age{}'.format(self.rollback_start))
        cur = arcpy.UpdateCursor(self.RolledBackInventory_layer)
        for row in cur:
            rolledBackAge = row.getValue(self.rollback_vintage_field)
            RegenDelay = row.getValue(self.regen_delay_field)
            invAge = row.getValue(self.inv_age_field)
            if rolledBackAge is None:
                row.setValue(self.rollback_vintage_field, (invAge - (self.inv_vintage - self.rollback_start)))
                row.setValue(self.regen_delay_field, 0)
            cur.updateRow(row)
        pp.finish()

    def makeSlashburn(self):
        year_range = range(self.rollback_range[0], self.rollback_range[1]+1)
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], len(year_range), 1).start()
        # print "Start of slashburn processing..."
        arcpy.CheckOutExtension("GeoStats")
        PercSBofCC = 50
        arcpy.MakeFeatureLayer_management(self.RolledBackInventory_layer, "temp_rollback")
        expression1 = '{} = {}'.format(arcpy.AddFieldDelimiters("temp_rollback", self.dist_type_field), 2)
        logging.info('Making slashburn for the range {}-{}'.format(self.rollback_range[0],self.rollback_range[1]))
        logging.info('Selecting {}% of the harvest area in each year as slashburn and adding it to the rollback disturbances...'.format(PercSBofCC))
        # Create SB records for each timestep
        for year in range(self.rollback_range[0], self.rollback_range[1]+1):
            expression2 = '{} = {}'.format(arcpy.AddFieldDelimiters("temp_rollback", self.new_disturbance_field), year)
            arcpy.SelectLayerByAttribute_management("temp_rollback", "NEW_SELECTION", expression2)
            arcpy.SelectLayerByAttribute_management("temp_rollback", "SUBSET_SELECTION", expression1)
            if int(arcpy.GetCount_management("temp_rollback").getOutput(0)) > 0:
                arcpy.SubsetFeatures_ga(in_features="temp_rollback", out_training_feature_class="temp_SB", out_test_feature_class="", size_of_training_dataset=PercSBofCC, subset_size_units="PERCENTAGE_OF_INPUT")
                arcpy.CalculateField_management("temp_SB", "DistType", 13, "PYTHON", "")
                arcpy.Append_management("temp_SB", self.RolledBackInventory_layer)
            arcpy.SelectLayerByAttribute_management("temp_rollback", "CLEAR_SELECTION")
            pp.updateProgressP()

        arcpy.CheckInExtension("GeoStats")
        pp.finish()

    def exportRollbackDisturbances(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()

        #Export rollback disturbances
        print "\tExporting Rollback Disturbances..."
        logging.info('Exporting rollback disturbances to {}'.format(self.rollbackDisturbanceOutput.getPath()))
        dissolveFields = [self.dist_type_field, self.new_disturbance_field,self.regen_delay_field, self.CELL_ID]
        selectClause =  "{} IS NOT NULL".format(self.new_disturbance_field)

        arcpy.SelectLayerByAttribute_management(self.RolledBackInventory_layer, "NEW_SELECTION", selectClause)
        arcpy.Dissolve_management(self.RolledBackInventory_layer, self.rollbackDisturbanceOutput.getPath(),dissolveFields,
            "","SINGLE_PART","DISSOLVE_LINES")

        pp.finish()

    def exportRollbackInventory(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        print "\tExporting rolled back inventory to rasters..."
        logging.info('Exporting rolled back inventory rasters to {}'.format(self.rasterOutput))
        arcpy.env.overwriteOutput = True
        classifier_names = self.inventory.getClassifiers()
        fields = {
            "age": self.inventory.getFieldNames()["rollback_age"],
            "species": self.inventory.getFieldNames()["species"],
            "THLB": self.inventory.getFieldNames()["THLB"]
        }
        for classifier_name in classifier_names:
            logging.info('Exporting classifer {} from {}'.format(classifier_name, os.path.join(self.inventory.getWorkspace(),self.RolledBackInventory)))
            field_name = self.inventory.getClassifierAttr(classifier_name)
            file_path = os.path.join(self.rasterOutput, "{}.tif".format(classifier_name))
            arcpy.FeatureToRaster_conversion(self.RolledBackInventory, field_name, file_path, self.resolution)
            self.inventory.addRaster(file_path, classifier_name, self.createAttributeTable(
                os.path.join(os.path.dirname(file_path), "{}.tif.vat.dbf".format(classifier_name)), field_name))
        for attr in fields:
            logging.info('Exporting field {} from {}'.format(attr, os.path.join(self.inventory.getWorkspace(),self.RolledBackInventory)))
            field_name = fields[attr]
            file_path = os.path.join(self.rasterOutput,"{}.tif".format(attr))
            arcpy.FeatureToRaster_conversion(self.RolledBackInventory, field_name, file_path, self.resolution)
            self.inventory.addRaster(file_path, attr, self.createAttributeTable(
                os.path.join(os.path.dirname(file_path), "{}.tif.vat.dbf".format(attr)), field_name))
        pp.finish()

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


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
## Old Script
'''
## 03_CalculateDist_DE_difference

import arcpy
from arcpy import env
arcpy.env.workspace = r"H:\Nick\GCBM\00_Testing\05_working\02_layers\01_external_spatial_data\00_Workspace.gdb"
env.overwriteOutput = True
print "Start time: " +(time.strftime('%a %H:%M:%S'))
# VARIABLES:
disturbedInventory = "DisturbedInventory"
disturbedInventory_layer = "disturbedInventory_layer"

#local variables
invAge_fieldName = "Age2011"
establishmentDate_fieldName = "DE_2011"
invVintage = 2011
disturbance_fieldName = "DistYEAR"
inv_dist_dateDiff = "Dist_DE_DIFF"

print "Making layers..."
arcpy.MakeFeatureLayer_management(disturbedInventory, disturbedInventory_layer)
print(arcpy.GetMessages())

print "Calculating establishment and date difference fields..."
#Calculate date of establishment and difference between date of establishment (inventory) and date of stand-replacing disturbance
cur = arcpy.UpdateCursor(disturbedInventory_layer)
for row in cur:
    # The variable 'age' will get the value from the column
    age = row.getValue(invAge_fieldName)
    DE = (invVintage - age)
    row.setValue(establishmentDate_fieldName, DE)
    DistDate = row.getValue(disturbance_fieldName)
    yearDiff = (DE - DistDate)
    if DistDate > 0:
        row.setValue(inv_dist_dateDiff, yearDiff)
    else:
        row.setValue(inv_dist_dateDiff, 0)
    cur.updateRow(row)

print(arcpy.GetMessages())
print "End time: " +(time.strftime('%a %H:%M:%S'))
print "COMPLETE"

## 04_CalculateNewDistYr_Age1990

import csv
import random
import arcpy
from arcpy import env

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

arcpy.env.workspace = r"H:\Nick\GCBM\00_Testing\05_working\02_layers\01_external_spatial_data\00_Workspace.gdb"
env.overwriteOutput = True
print "Start time: {}".format(time.strftime("%a %H:%M:%S"))

#local variables
DisturbedInventory = "DisturbedInventory"
disturbedInventory_layer = "disturbedInventory_layer"
inv_age_field = "Age2011"
establishment_date_field = "DE_2011"
inv_vintage = 2011
rollback_year = 1990
disturbance_yr = "DistYEAR"
new_disturbance_field = "DistYEAR_new"
inv_dist_date_diff_field = "Dist_DE_DIFF"
dist_type_field = "DistType"
harv_yr_field = "HARV_YR"
regen_delay_field = "RegenDelay"
preDistAge = "preDistAge"
rollback_vintage_field = "Age1990"

print "Making layers..."
arcpy.MakeFeatureLayer_management(DisturbedInventory, disturbedInventory_layer)
print(arcpy.GetMessages())

print "Calculating disturbance type field..."
cur = arcpy.UpdateCursor(disturbedInventory_layer)
for row in cur:
    dist_year = row.getValue(disturbance_yr)
    harv_year = row.getValue(harv_yr_field)
    if dist_year == harv_year:
        row.setValue(dist_type_field, "2")
    else:
        row.setValue(dist_type_field, "1")
    cur.updateRow(row)

print "Calculating regen delay field..."
cur = arcpy.UpdateCursor(disturbedInventory_layer)
for row in cur:
    age_diff = row.getValue(inv_dist_date_diff_field)
    est_year = row.getValue(establishment_date_field)
    dist_year = row.getValue(disturbance_yr)
    inv_derived_disturbance = est_year - 1
    if age_diff > 0:
        row.setValue(regen_delay_field, age_diff)
        row.setValue(new_disturbance_field, dist_year)
    elif age_diff <= 0:
        # Disturbance can't occur after establishment year - set to year before establishment.
        row.setValue(regen_delay_field, 0)
        row.setValue(new_disturbance_field, inv_derived_disturbance)

    cur.updateRow(row)

print "Calculating pre-disturbance age field..."
dist_age_props = {}
with open("distageprop.csv", "r") as age_prop_file:
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
    print dist_type
    age_distributors[dist_type] = RollbackDistributor(**age_props)

cur = arcpy.UpdateCursor(disturbedInventory_layer)
for row in cur:
    dist_type = int(row.getValue(dist_type_field))
    age_distributor = age_distributors.get(dist_type)
    if not age_distributor:
        print "No age distributor for layer disturbance type {} - skipping.".format(dist_type)
        continue

    row.setValue(preDistAge, age_distributor.next())
    cur.updateRow(row)

for dist_type, age_distributor in age_distributors.iteritems():
    print "Age picks for disturbance type {}:".format(dist_type)
    print str(age_distributor)

print "Calculating Rolledback inventory age..."
cur = arcpy.UpdateCursor(disturbedInventory_layer)
for row in cur:
    pre_DistAge = row.getValue(preDistAge)
    dist_yearNew = row.getValue(new_disturbance_field)
    row.setValue(rollback_vintage_field, (pre_DistAge + rollback_year - dist_yearNew))
    # if dist_yearNew == rollback_year:
        # row.setValue(rollback_vintage_field, (pre_DistAge + rollback_year - dist_yearNew))
    # else:
        # row.setValue(rollback_vintage_field, (pre_DistAge + rollback_year - dist_yearNew + 1))

    cur.updateRow(row)
print arcpy.GetMessages()
print "End time: {}".format(time.strftime("%a %H:%M:%S"))
print "COMPLETE"


## 05_Update_inv_rollBack_nonDistStandAgess

import csv
import random
import arcpy
from arcpy import env
import os

arcpy.env.workspace = r"H:\Nick\GCBM\00_Testing\05_working\02_layers\01_external_spatial_data\00_Workspace.gdb"
rollbackDisturbanceOutput = r"H:\Nick\GCBM\00_Testing\05_working\02_layers\01_external_spatial_data\03_disturbances\03_rollbackDisturbances\rollbackDist.shp"
#TilerInputInventory = r"C:\Byron\01_Kamloops_TSA\05_working\03_layers\01_external_spatial_data\02_inventory\KamTSA_inv1990"
shapefileOutput = r"H:\Nick\GCBM\00_Testing\05_working\02_layers\01_external_spatial_data\02_inventory"
env.overwriteOutput = True
print "Start time: {}".format(time.strftime("%a %H:%M:%S"))

#local variables
#data
gridded_inventory = "inventory_gridded"
disturbedInventory = "DisturbedInventory"
RolledBackInventory = "inv_gridded_1990"
inv_vintage = 2011
rollback_year = 1990
#layers
RolledBackInventory_layer = "RolledBackInventory_layer"
gridded_inventory_layer = "gridded_inventory_layer"
disturbedInventory_layer = "disturbedInventory_layer"
#fields
inv_age_field = "Age2011"
establishment_date_field = "DE_2011"
disturbance_yr = "DistYEAR"
new_disturbance_field = "DistYEAR_new"
inv_dist_date_diff_field = "Dist_DE_DIFF"
dist_type_field = "DistType"
harv_yr_field = "HARV_YR"
regen_delay_field = "RegenDelay"
preDistAge = "preDistAge"
rollback_vintage_field = "Age1990"
speciesFieldName = "LeadSpp"
GY_linkField = "FEATURE_ID"
CELL_ID = "CELL_ID"

#field selection
dissolveFields = [dist_type_field, new_disturbance_field,regen_delay_field, CELL_ID]
selectClause = new_disturbance_field + " IS NOT NULL"

print "Making layers..."
arcpy.MakeFeatureLayer_management(gridded_inventory, gridded_inventory_layer)
arcpy.MakeFeatureLayer_management(disturbedInventory, disturbedInventory_layer)

print "Re-merging disturbed polygons with non-disturbed inventory..."
# Process: Update
arcpy.Update_analysis(gridded_inventory_layer, disturbedInventory_layer, RolledBackInventory, "BORDERS", "0.25 Meters")

print "Adding Field Maps..."
#Add field map
fm1 = arcpy.FieldMap()
fm2 = arcpy.FieldMap()
fm3 = arcpy.FieldMap()
fm4 = arcpy.FieldMap()
fms1 = arcpy.FieldMappings()
fms2 = arcpy.FieldMappings()
fms3 = arcpy.FieldMappings()
fms4 = arcpy.FieldMappings()
fm1.addInputField(RolledBackInventory, speciesFieldName)
fm2.addInputField(RolledBackInventory, rollback_vintage_field)
fm3.addInputField(RolledBackInventory, inv_age_field)
fm4.addInputField(RolledBackInventory, GY_linkField)

fms1.addFieldMap(fm1)
fms2.addFieldMap(fm2)
fms3.addFieldMap(fm3)
fms4.addFieldMap(fm4)

print "Making layers..."
arcpy.MakeFeatureLayer_management(RolledBackInventory, RolledBackInventory_layer)

print "Rolling back age of non-disturbed stands..."
cur = arcpy.UpdateCursor(RolledBackInventory_layer)
for row in cur:
    rolledBackAge = row.getValue(rollback_vintage_field)
    RegenDelay = row.getValue(regen_delay_field)
    invAge = row.getValue(inv_age_field)
    if rolledBackAge is None:
        row.setValue(rollback_vintage_field, (invAge - (inv_vintage - rollback_year)))
        row.setValue(regen_delay_field, 0)
    cur.updateRow(row)

print "Exporting rolledback inventory to shape file..."
#print "Exporting rolledback species shape file..."
arcpy.FeatureClassToFeatureClass_conversion(RolledBackInventory, shapefileOutput, "inv_gridded_1990.shp")

#-------------------------------------- Used to export individual inventory values if shape file exceeds 2gb -------------------------------------
# arcpy.PolygonToRaster_conversion (RolledBackInventory, speciesFieldName, os.path.join(shapefileOutput, "KamTSA_species.tif"), "CELL_CENTER","", 100)
# print "Exporting rolledback age shape file..."
# #arcpy.FeatureClassToFeatureClass_conversion(RolledBackInventory, shapefileOutput, "KamTSA_Age1990.shp", field_mapping = fms2)
# arcpy.PolygonToRaster_conversion (RolledBackInventory, rollback_vintage_field, os.path.join(shapefileOutput, "KamTSA_Age1990.tif"), "CELL_CENTER", "",100)
# print "Exporting original Age shape file..."
# #arcpy.FeatureClassToFeatureClass_conversion(RolledBackInventory, shapefileOutput, "KamTSA_Age2015.shp", field_mapping = fms3)
# arcpy.PolygonToRaster_conversion (RolledBackInventory, inv_age_field, os.path.join(shapefileOutput, "KamTSA_Age2015.tif"), "CELL_CENTER", "",100)
# print "Exporting FEATURE_ID shape file..."
# #arcpy.FeatureClassToFeatureClass_conversion(RolledBackInventory, shapefileOutput, "KamTSA_FEATUREID.shp", field_mapping = fms4)
# arcpy.PolygonToRaster_conversion (RolledBackInventory, GY_linkField, os.path.join(shapefileOutput, "KamTSA_FEATUREID.tif"), "CELL_CENTER", "",100)

#Export rollback disturbances
arcpy.SelectLayerByAttribute_management(RolledBackInventory_layer, "NEW_SELECTION", selectClause)
print "Exporting Rollback Disturbances..."
arcpy.Dissolve_management(RolledBackInventory_layer, rollbackDisturbanceOutput,dissolveFields,"","SINGLE_PART","DISSOLVE_LINES")

print arcpy.GetMessages()
print "End time: {}".format(time.strftime("%a %H:%M:%S"))
print "COMPLETE"

'''

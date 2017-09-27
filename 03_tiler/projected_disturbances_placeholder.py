import archook
archook.get_arcpy()
import arcpy
import shutil
import inspect
import os
import glob
import logging
import numpy as np
import random
from itertools import count, groupby, izip_longest

class ProjectedDisturbancesPlaceholder(object):
    def __init__(self, inventory, rollbackDisturbances, future_range, rollback_range, activity_start_year, ProgressPrinter, output_dir=None):
        self.ProgressPrinter = ProgressPrinter
        self.inventory = inventory
        self.rollbackDisturbances = rollbackDisturbances
        self.future_range = future_range
        self.rollback_range = rollback_range
        self.activity_start_year = activity_start_year
        if output_dir==None:
            self.output_dir = os.path.abspath(r'{}\..\01a_pretiled_layers\03_disturbances\02_future\outputs'.format(os.getcwd()))
        else:
            self.output_dir = output_dir

    def copyRollbackDistAsFuture(self,scenario):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        output_directory = os.path.join(self.output_dir,'SCEN_{}'.format(scenario))
        name = 'projectedDist'
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        for file in self.scan_for_files_all_ext(self.rollbackDisturbances.getPath()):
            ext = file.split('.')[-1]
            shutil.copyfile(file, os.path.join(output_directory,'{}.{}'.format(name,ext)))
        projectedDistDBF = os.path.join(output_directory,'{}.dbf'.format(name))
        arcpy.AddField_management(projectedDistDBF, 'dist_year')
        arcpy.CalculateField_management(projectedDistDBF, 'dist_year', '!{}!+26'.format(self.inventory.getFieldNames()['new_disturbance_yr'][:10]),"PYTHON_9.3", "")
        projectedDistShp = os.path.join(output_directory,'{}.shp'.format(name))
        pp.finish()
        return projectedDistShp

    def scan_for_files_all_ext(self, file_path):
        return sorted(glob.glob('{}*'.format(file_path.split('.')[0])), key=os.path.basename)

    def generateProjectedDisturbances(self, scenario, slashburn_percent, actv_slashburn_percent, actv_harvest_percent):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        arcpy.CheckOutExtension("GeoStats")

        self.outLocation = os.path.abspath(r'{}\..\01a_pretiled_layers\03_disturbances\02_future\outputs\projectedDist.gdb'.format(os.getcwd()))
        if not os.path.exists(self.outLocation):
            arcpy.CreateFileGDB_management(os.path.dirname(self.outLocation), os.path.basename(self.outLocation))
        arcpy.env.workspace = self.outLocation
        arcpy.env.overwriteOutput=True

        #editable variables - dist types of future variables
        # projScenBase_lookuptable = {
        #     11: "Base CC",
        #     7: "Wild Fires",
        #     13: "SlashBurning",
        #     10: "Partial Cut",
        #     6: "Base Salvage",
        #     2: "Wild Fire",
        #     1: "Clearcut harvesting with salvage"

        self.fire_code = 7
        self.SB_code = 13
        self.BASE_salvage_code = 6
        self.distYr_field = self.inventory.getFieldNames()["new_disturbance_yr"]
        self.distType_field = self.inventory.getFieldNames()["dist_type"]
        self.regen_delay_field = self.inventory.getFieldNames()["regen_delay"]
        self.year_range = range(self.future_range[0],self.future_range[1]+1)

        fire_areaValue, harvest_areaValue = self.calculateFireAndHarvestArea(actv_harvest_percent)

        projected_disturbances = "proj_dist"
        if arcpy.Exists(os.path.join(self.outLocation, projected_disturbances)):
            arcpy.Delete_management(projected_disturbances)
        arcpy.CreateFeatureclass_management(self.outLocation, projected_disturbances, "", "inventory_gridded_1990","","","inventory_gridded_1990")

        self.generateFire(fire_areaValue, projected_disturbances)
        self.generateHarvest(harvest_areaValue, projected_disturbances, actv_harvest_percent)
        self.generateSlashburn(harvest_areaValue, projected_disturbances, slashburn_percent, actv_slashburn_percent)

        if arcpy.Exists(os.path.join(os.path.dirname(self.outLocation), "{}.shp".format(projected_disturbances))):
            arcpy.Delete_management(os.path.join(os.path.dirname(self.outLocation), "{}.shp".format(projected_disturbances)))

        outShpDir = os.path.join(os.path.dirname(self.outLocation),'SCEN_{}'.format(scenario))
        if not os.path.exists(outShpDir):
            os.makedirs(outShpDir)
        outShp = os.path.join(outShpDir, "{}.shp".format(projected_disturbances))
        if os.path.exists(outShp):
            arcpy.Delete_management(outShp)
        arcpy.FeatureClassToShapefile_conversion(projected_disturbances, outShpDir)
        logging.info('Projected disturbances generated for scenario {} at {}'.format(scenario, outShpDir))
        arcpy.CheckInExtension("GeoStats")
        pp.finish()
        return outShp


    def calculateFireAndHarvestArea(self, harvest_percent):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 2).start()
        # Local variables:
        rollback_stats = r"{}\rollbackDist_Statistics".format(self.outLocation)

        # add area field to rolled back distubances
        rollback_dist = self.rollbackDisturbances.getPath()

        # add the layer to the working gdb
        if arcpy.Exists(os.path.join(self.outLocation, "rollbackDist")):
            arcpy.Delete_management("rollbackDist")
        arcpy.FeatureClassToGeodatabase_conversion(rollback_dist,self.outLocation)

        # # how many pixels is this? inventory is gridded, so areas should be compatible
        # # bring in the inventory and select pixels
        arcpy.CopyFeatures_management(r"{}\inventory_gridded_1990".format(self.inventory.getWorkspace()), "inventory_gridded_1990")

        # make it more like the disturbance layer

        keep = ["CELL_ID", "shape", self.distType_field, self.regen_delay_field, self.distYr_field, "Shape_Area","Shape_Length"]
        discard = []
        for field in [f.name for f in arcpy.ListFields("inventory_gridded_1990")
        	if f.type != 'OID' and f.type != 'Geometry']:
        		if field not in keep:
        			discard.append(field)
        arcpy.DeleteField_management("inventory_gridded_1990", discard)

        fire_areaValue = 0
        harvest_areaValue = 0

        self.rollback_fire_code = 1
        self.rollback_harvest_code = 2
        harvest_where = '{} = {}'.format(arcpy.AddFieldDelimiters(rollback_stats, self.distType_field), self.rollback_harvest_code)
        arcpy.Select_analysis("rollbackDist", "harv", harvest_where)
        fire_where = '{} = {}'.format(arcpy.AddFieldDelimiters(rollback_stats, self.distType_field), self.rollback_fire_code)
        arcpy.Select_analysis("rollbackDist", "fire", fire_where)
        total_harv_records = int(arcpy.GetCount_management("harv").getOutput(0))
        yearly_harv_records = total_harv_records/(self.rollback_range[1]-self.rollback_range[0]+1)
        total_fire_records = int(arcpy.GetCount_management("fire").getOutput(0))
        yearly_fire_records = total_fire_records/(self.rollback_range[1]-self.rollback_range[0]+1)

        logging.info("Fire annual area is:{}".format(yearly_fire_records))
        logging.info("Harvest annual area is:{}".format(yearly_harv_records))

        pp.finish()
        return yearly_fire_records, yearly_harv_records

    def generateFire(self, fire_areaValue, projected_disturbances):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], len(self.year_range), 2).start()
        # process fire-----------------------
        logging.info("Start of projected fire processing...")
        if fire_areaValue>0:
            fire_proj_dist_temp = "fire_proj_dist_temp"
            for year in self.year_range:
            	arcpy.SubsetFeatures_ga(in_features="inventory_gridded_1990", out_training_feature_class=r"{}\fire_proj_dist_temp".format(self.outLocation), out_test_feature_class="", size_of_training_dataset=fire_areaValue, subset_size_units="ABSOLUTE_VALUE")
            	arcpy.Append_management(fire_proj_dist_temp, projected_disturbances)
                pp.updateProgressP()

            # update the dist type and regen delay
            arcpy.CalculateField_management(projected_disturbances, field=self.distType_field, expression=self.fire_code, expression_type="PYTHON", code_block="")
            arcpy.CalculateField_management(projected_disturbances, field=self.regen_delay_field, expression="0", expression_type="PYTHON", code_block="")

            # add dist year
            arcpy.AddField_management(projected_disturbances, field_name=self.distYr_field, field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")

            #Populate disturbance year
            count = int(arcpy.GetCount_management(projected_disturbances).getOutput(0))
            events_per_year = count / len(self.year_range)
            cursor = arcpy.UpdateCursor(projected_disturbances)
            year = self.future_range[0]
            i = 1
            for row in cursor:
            	row.setValue(self.distYr_field, year)
            	cursor.updateRow(row)
            	i = i + 1
            	if i > events_per_year:
            		i = 1
            		year = year + 1
            arcpy.Delete_management(fire_proj_dist_temp)
        else:
            logging.info("No projected fire was generated because no historic fire was found.")
        pp.finish()

    def generateHarvest(self, harvest_areaValue, projected_disturbances, actv_harvest_percent):
        pp1 = self.ProgressPrinter.newProcess("generateHarvest", len(self.year_range), 2).start()
        # process harvest-----------------------
        logging.info("Start of projected harvest processing...")
        logging.info("Generating projected harvest with a {}% reduction after the activity start year of {}".format((100-actv_harvest_percent),self.activity_start_year))
        if harvest_areaValue>0:
            # update the dist type and regen delay
            harvest_proj_dist_temp = "harvest_proj_dist_temp"
            harvest_proj_dist_temp1 = "harvest_proj_dist_temp1"
            arcpy.CreateFeatureclass_management(self.outLocation, harvest_proj_dist_temp, "", "inventory_gridded_1990","","","inventory_gridded_1990")
            for year in self.year_range:
                if year>=self.activity_start_year:
                    harvest_records = harvest_areaValue * (actv_harvest_percent/100.0)
                else:
                    harvest_records = harvest_areaValue
            	arcpy.SubsetFeatures_ga(in_features="inventory_gridded_1990", out_training_feature_class="{}/{}".format(self.outLocation,harvest_proj_dist_temp1), out_test_feature_class="", size_of_training_dataset=harvest_records, subset_size_units="ABSOLUTE_VALUE")
            	arcpy.Append_management(harvest_proj_dist_temp1, harvest_proj_dist_temp)
                pp1.updateProgressP()

            arcpy.CalculateField_management(harvest_proj_dist_temp, field=self.distType_field, expression=self.BASE_salvage_code, expression_type="PYTHON", code_block="")
            arcpy.CalculateField_management(harvest_proj_dist_temp, field=self.regen_delay_field, expression="0", expression_type="PYTHON", code_block="")

            # add dist year
            arcpy.AddField_management(harvest_proj_dist_temp, field_name=self.distYr_field, field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")

            #Populate disturbance year
            count = int(arcpy.GetCount_management(harvest_proj_dist_temp).getOutput(0))
            events_per_year = count / len(self.year_range)

            cursor = arcpy.UpdateCursor(harvest_proj_dist_temp)
            year = self.future_range[0]
            i = 1
            for row in cursor:
            	row.setValue(self.distYr_field, year)
            	cursor.updateRow(row)
            	i = i + 1
            	if i > events_per_year:
            		i = 1
            		year = year + 1

            #append disturbances
            arcpy.Append_management(harvest_proj_dist_temp, projected_disturbances)
            arcpy.Delete_management(harvest_proj_dist_temp1)
        else:
            logging.info("No projected harvest was generated because no historic harvest was found.")
        pp1.finish()


    def generateSlashburn(self, harvest_areaValue, projected_disturbances, slashburn_percent, actv_slashburn_percent):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], len(self.year_range), 2).start()
        #Make slashburn-----------------------
        logging.info('Start of projected slashburn processing...')
        logging.info("Generating projected slashburn with a {}% reduction after the activity start year of {}".format((slashburn_percent-actv_slashburn_percent)*100/(slashburn_percent),self.activity_start_year))
        if harvest_areaValue>0:
            harvest_proj_dist_temp = "harvest_proj_dist_temp"
            slasburn_proj_dist_temp = "slasburn_proj_dist_temp"
            arcpy.MakeFeatureLayer_management(projected_disturbances, harvest_proj_dist_temp)
            expression1 = '{} = {}'.format(arcpy.AddFieldDelimiters(harvest_proj_dist_temp, self.distType_field), self.BASE_salvage_code)
            # Create SB records for each timestep
            for year in self.year_range:
                if year>=self.activity_start_year:
                    PercSBofCC = actv_slashburn_percent
                else:
                    PercSBofCC = slashburn_percent
                if PercSBofCC > 0:
                	expression2 = '{} = {}'.format(arcpy.AddFieldDelimiters(harvest_proj_dist_temp, self.distYr_field), year)
                	arcpy.SelectLayerByAttribute_management(harvest_proj_dist_temp, "NEW_SELECTION", expression2)
                	arcpy.SelectLayerByAttribute_management(harvest_proj_dist_temp, "SUBSET_SELECTION", expression1)
                	arcpy.SubsetFeatures_ga(in_features=harvest_proj_dist_temp, out_training_feature_class=r"{}\{}".format(self.outLocation,slasburn_proj_dist_temp), out_test_feature_class="", size_of_training_dataset=PercSBofCC, subset_size_units="PERCENTAGE_OF_INPUT")
                	arcpy.CalculateField_management(slasburn_proj_dist_temp, self.distType_field, self.SB_code, "PYTHON", )
                	arcpy.Append_management(slasburn_proj_dist_temp, projected_disturbances)
                	arcpy.SelectLayerByAttribute_management(harvest_proj_dist_temp, "CLEAR_SELECTION")
                	pp.updateProgressP()
            arcpy.Delete_management(harvest_proj_dist_temp)
            arcpy.Delete_management(slasburn_proj_dist_temp)
        else:
            logging.info("No projected slashburn was generated because of no projected harvest.")
        pp.finish()

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
## Old Script
'''
import arcpy
import time
import os
import numpy as np
import random
from itertools import izip_longest
from itertools import count, groupby

arcpy.env.overwriteOutput=True
arcpy.CheckOutExtension("GeoStats")
# Working location:
arcpy.CreateFileGDB_management("G:\\GCBM\\17_BC_ON_1ha\\05_working\\TSA_11_Kamloops_TSA\\01a_pretiled_layers\\03_disturbances\\02_future\\outputs", "projectedDist.gdb")
arcpy.env.workspace = "G:\\GCBM\\17_BC_ON_1ha\\05_working\\TSA_11_Kamloops_TSA\\01a_pretiled_layers\\03_disturbances\\02_future\\outputs\\projectedDist.gdb"

outLocation = "G:\\GCBM\\17_BC_ON_1ha\\05_working\\TSA_11_Kamloops_TSA\\01a_pretiled_layers\\03_disturbances\\02_future\\outputs\\projectedDist.gdb"

#editable variables - dist types of future variables
fire_code = 7
SB_code = 13
BASE_salvage_code=6
distYr_field="DistYear_new"
start_yr = 2016
year_range = range(2016,2071) # not inclusive of last year

    # projScenBase_lookuptable = {
    #     11: "Base CC",
    #     7: "Wild Fires",
    #     13: "SlashBurning",
    #     10: "Partial Cut",
    #     6: "Base Salvage",
    #     2: "Wild Fire",
    #     1: "Clearcut harvesting with salvage"
# Local variables:
PercSBofCC = 50
annual_area = "annual_area"
# fire_area = 0
# harvest_area = 0
SUM_Area = "SUM_area"
DistYear_n = "DistYear_n"
fc="fc"
j="j"

# add area field to rolled back distubances
fc = "G:\\GCBM\\17_BC_ON_1ha\\05_working\\TSA_11_Kamloops_TSA\\01a_pretiled_layers\\03_disturbances\\03_rollback\\rollbackDist.shp"
arcpy.AddField_management(fc,"area","Double")
expression1 = "{0}".format("!SHAPE.area@SQUAREKILOMETERS!")
arcpy.CalculateField_management(fc, "area", expression1, "PYTHON", )

# add the layer to the working gdb
arcpy.FeatureClassToGeodatabase_conversion(fc,outLocation)

# get the statistics and add the table to the gdb
print(time.strftime('%a %H:%M:%S'))
arcpy.Statistics_analysis(in_table="rollbackDist", out_table="G:\\GCBM\\17_BC_ON_1ha\\05_working\\TSA_11_Kamloops_TSA\\01a_pretiled_layers\\03_disturbances\\02_future\\outputs\\projectedDist.gdb\\rollbackDist_Statistics", statistics_fields="area SUM", case_field="DistType")

# estimate the area burned as the area divided by 26 years, multiplied by 100 to put into hectares | DO NOT as the pixels will be in resolution above
arcpy.AddField_management(in_table="rollbackDist_Statistics", field_name="annual_area", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")

arcpy.CalculateField_management(in_table="rollbackDist_Statistics", field="annual_area", expression="!SUM_area!/(2015-1990+1)", expression_type="PYTHON", code_block="")
# how many pixels is this? inventory is gridded, so areas should be compatible
# bring in the inventory and select pixels
arcpy.CopyFeatures_management("G:\\GCBM\\17_BC_ON_1ha\\05_working\\TSA_11_Kamloops_TSA\\01a_pretiled_layers\\00_Workspace.gdb\\inventory_gridded_1990", "inventory_gridded_1990")

# make it more like the disturbance layer

keep = ["CELL_ID", "shape", "DistType", "RegenDelay", "DistYear_new","Shape_Area","Shape_Length"]
discard = []
for field in [f.name for f in arcpy.ListFields("inventory_gridded_1990")
	if f.type <> 'OID' and f.type <> 'Geometry']:
		if field not in keep:
			discard.append(field)
arcpy.DeleteField_management("inventory_gridded_1990", discard)


# the subset needs to be set to rollbackDist_Statistics\SUM_area
fc = "G:\\GCBM\\17_BC_ON_1ha\\05_working\\TSA_11_Kamloops_TSA\\01a_pretiled_layers\\03_disturbances\\02_future\\outputs\\projectedDist.gdb\\rollbackDist_Statistics"
fire_area =[]
harvest_area=[]
distType_field = "DistType"
regen_delay_field = "RegenDelay"
areaField = "annual_area"
# delimfield = arcpy.AddFieldDelimiters(fc, distType_field)
# print delimfield
rollback_fire_code = 1
rollback_harvest_code = 2
#Fire area
print "Finding annual areas from rollback disturbances..."
expression = '{} = {}'.format(arcpy.AddFieldDelimiters(fc, distType_field), rollback_fire_code)
with arcpy.da.SearchCursor(fc, [distType_field, areaField],
                           where_clause=expression) as cursor:
    for row in cursor:
	fire_areaValue = (row[1])
#Harvest area
expression = '{} = {}'.format(arcpy.AddFieldDelimiters(fc, distType_field), rollback_harvest_code)
with arcpy.da.SearchCursor(fc, [distType_field, areaField],
                           where_clause=expression) as cursor:
    for row in cursor:
	harvest_areaValue = (row[1])

print "Fire annual area is:"
print fire_areaValue
print "Harvest annual area is:"
print harvest_areaValue

# process fire-----------------------
print "Start of slashburn processing..."
# but that will be zero for this test dataset
proj_dist = "proj_dist"
fire_proj_dist_temp = "fire_proj_dist_temp"
arcpy.CreateFeatureclass_management("G:/GCBM/17_BC_ON_1ha/05_working/TSA_11_Kamloops_TSA/01a_pretiled_layers/03_disturbances/02_future/outputs/projectedDist.gdb", proj_dist, "", "inventory_gridded_1990","","","inventory_gridded_1990")

for year in year_range:
	arcpy.SubsetFeatures_ga(in_features="inventory_gridded_1990", out_training_feature_class="G:/GCBM/17_BC_ON_1ha/05_working/TSA_11_Kamloops_TSA/01a_pretiled_layers/03_disturbances/02_future/outputs/projectedDist.gdb/fire_proj_dist_temp", out_test_feature_class="", size_of_training_dataset=fire_areaValue, subset_size_units="ABSOLUTE_VALUE")
	arcpy.Append_management(fire_proj_dist_temp, "proj_dist")

# update the dist type and regen delay
fc="G:/GCBM/17_BC_ON_1ha/05_working/TSA_11_Kamloops_TSA/01a_pretiled_layers/03_disturbances/02_future/outputs/projectedDist.gdb/proj_dist"

arcpy.CalculateField_management(fc, field="DistType", expression=fire_code, expression_type="PYTHON", code_block="")
arcpy.CalculateField_management(fc, field="RegenDelay", expression="0", expression_type="PYTHON", code_block="")

# add dist year
arcpy.AddField_management(fc, field_name="DistYear_new", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")

#Populate disturbance year
count = int(arcpy.GetCount_management(fc).getOutput(0))
events_per_year = count / len(year_range)

cursor = arcpy.UpdateCursor(fc)
year = start_yr
i = 1
for row in cursor:
	row.setValue(distYr_field, year)
	cursor.updateRow(row)
	i = i + 1
	if i > events_per_year:
		i = 1
		year = year + 1


# process harvest-----------------------
print "Start of harvest processing..."
# update the dist type and regen delay
harvest_proj_dist_temp = "harvest_proj_dist_temp"
harvest_proj_dist_temp1 = "harvest_proj_dist_temp1"
arcpy.CreateFeatureclass_management("G:/GCBM/17_BC_ON_1ha/05_working/TSA_11_Kamloops_TSA/01a_pretiled_layers/03_disturbances/02_future/outputs/projectedDist.gdb", harvest_proj_dist_temp, "", "inventory_gridded_1990","","","inventory_gridded_1990")
for year in year_range:
	arcpy.SubsetFeatures_ga(in_features="inventory_gridded_1990", out_training_feature_class="G:/GCBM/17_BC_ON_1ha/05_working/TSA_11_Kamloops_TSA/01a_pretiled_layers/03_disturbances/02_future/outputs/projectedDist.gdb/harvest_proj_dist_temp1", out_test_feature_class="", size_of_training_dataset=harvest_areaValue, subset_size_units="ABSOLUTE_VALUE")
	arcpy.Append_management(harvest_proj_dist_temp1, "harvest_proj_dist_temp")

fc=harvest_proj_dist_temp
arcpy.CalculateField_management(fc, field="DistType", expression=BASE_salvage_code, expression_type="PYTHON", code_block="")
arcpy.CalculateField_management(fc, field="RegenDelay", expression="0", expression_type="PYTHON", code_block="")

# add dist year
arcpy.AddField_management(fc, field_name="DistYear_new", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")

#Populate disturbance year
count = int(arcpy.GetCount_management(fc).getOutput(0))
events_per_year = count / len(year_range)

cursor = arcpy.UpdateCursor(fc)
year = start_yr
i = 1
for row in cursor:
	row.setValue(distYr_field, year)
	cursor.updateRow(row)
	i = i + 1
	if i > events_per_year:
		i = 1
		year = year + 1

#append disturbances
arcpy.Append_management(harvest_proj_dist_temp, "proj_dist")

#Make slashburn-----------------------
year = start_yr
slasburn_proj_dist_temp = "slasburn_proj_dist_temp"

print "Start of slashburn processing..."

arcpy.MakeFeatureLayer_management(proj_dist, fc)
expression1 = '{} = {}'.format(arcpy.AddFieldDelimiters(fc, distType_field), BASE_salvage_code)
print expression1
print year_range
# expression = '{} = {}'.format(arcpy.AddFieldDelimiters(fc, year), SB_code)
for year in year_range:
	expression2 = '{} = {}'.format(arcpy.AddFieldDelimiters(fc, distYr_field), year)
	print expression2
	arcpy.SelectLayerByAttribute_management(fc, "NEW_SELECTION", expression2)
	arcpy.SelectLayerByAttribute_management(fc, "SUBSET_SELECTION", expression1)
	arcpy.SubsetFeatures_ga(in_features=fc, out_training_feature_class="G:/GCBM/17_BC_ON_1ha/05_working/TSA_11_Kamloops_TSA/01a_pretiled_layers/03_disturbances/02_future/outputs/projectedDist.gdb/slasburn_proj_dist_temp", out_test_feature_class="", size_of_training_dataset=PercSBofCC, subset_size_units="PERCENTAGE_OF_INPUT")
	arcpy.CalculateField_management(slasburn_proj_dist_temp, "DistType", SB_code, "PYTHON", )
	#arcpy.CalculateField_management(slasburn_proj_dist_temp, "DistType", SB_code, "VB", "")
	arcpy.Append_management(slasburn_proj_dist_temp, "proj_dist")
	arcpy.SelectLayerByAttribute_management(fc, "CLEAR_SELECTION")

arcpy.FeatureClassToShapefile_conversion("proj_dist", "G:/GCBM/17_BC_ON_1ha/05_working/TSA_11_Kamloops_TSA/01a_pretiled_layers/03_disturbances/02_future/outputs")
# Create SB records for each timestep

#for fc in fcs:
#    print str(fc)
#	 arcpy.Append_management(fc, all_fire, "NO TEST", "", ""
#    arcpy.MakeFeatureLayer_management(fc, fc1)
#    if fc == 'disturbance_events_1':
#		arcpy.Select_analysis(fc1, CC_1, "\"dist_type_id\" = 1")
#    elif fc == 'disturbance_events_2':
#		arcpy.Select_analysis(fc1, CC_1, "\"dist_type_id\" = 1")
#    elif fc == 'disturbance_events_3':
#		arcpy.Select_analysis(fc1, CC_1, "\"dist_type_id\" = 1")
#    else:
#		arcpy.Select_analysis(fc1, CC_1, "\"dist_type_id\" = 6 OR \"dist_type_id\" = 11")
#    arcpy.SubsetFeatures_ga(CC_1, SB_1, Output_test_feature_class, PercSBofCC, "PERCENTAGE_OF_INPUT")
#    arcpy.CalculateField_management(SB_1, "dist_type_id", SB_code, "VB", "")
#    arcpy.CalculateField_management(SB_1, "timestep", "[timestep]+1", "VB", "")
#    arcpy.Append_management([SB_1, fc1], MasterDist, "TEST", "", "")
####
#    print(time.strftime('%a %H:%M:%S'))
#arcpy.AddField_management(MasterDist, "TimeStepTXT", "TEXT", field_length = FieldLength)
#arcpy.CalculateField_management(MasterDist, TimeStepTXT, "\"TS_\" & [timestep]", "VB", "")
#
##Parse out each timestep into indivdual layers for loading into Recliner
#rows = arcpy.SearchCursor(MasterDist)
#row = rows.next()
#attribute_types = set([])
#
#while row:
#    attribute_types.add(row.TimeStepTXT)
#    row = rows.next()
#
## Output a feature class for each different attribute
#for each_attribute in attribute_types:
#    outfile = each_attribute
#    print outfile
#    arcpy.Select_analysis (MasterDist, outfile, "\"TimeStepTXT\" = '" + each_attribute + "'")
#
#del rows, row, attribute_types
arcpy.CheckInExtension("GeoStats")
print "done "+ (time.strftime('%a %H:%M:%S'))
'''

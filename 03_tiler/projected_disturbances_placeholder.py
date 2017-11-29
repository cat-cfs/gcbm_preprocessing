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
from preprocess_tools.licensemanager import arc_license

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
		arcpy.CopyFeatures_management(projected_disturbances, outShp)
		logging.info('Projected disturbances generated for scenario {} at {}'.format(scenario, outShpDir))

		pp.finish()
		return outShp


    def calculateFireAndHarvestArea(self, harvest_percent):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 2).start()
        rollback_stats = r"{}\rollbackDist_Statistics".format(self.outLocation)

        # add area field to rolled back distubances
        rollback_dist = self.rollbackDisturbances.getPath()

        # add the layer to the working gdb
        if arcpy.Exists(os.path.join(self.outLocation, "rollbackDist")):
            arcpy.Delete_management("rollbackDist")
        arcpy.FeatureClassToFeatureClass_conversion(rollback_dist,self.outLocation,"rollbackDist")

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
        total_harv_records = float(arcpy.GetCount_management("harv").getOutput(0))
        yearly_harv_records = total_harv_records/(self.rollback_range[1]-self.rollback_range[0]+1)
        total_fire_records = float(arcpy.GetCount_management("fire").getOutput(0))
        yearly_fire_records = total_fire_records/(self.rollback_range[1]-self.rollback_range[0]+1)

        logging.info("Fire annual area is:{}".format(yearly_fire_records))
        logging.info("Harvest annual area is:{}".format(yearly_harv_records))

        pp.finish()
        return yearly_fire_records, yearly_harv_records

    def generateFire(self, fire_areaValue, projected_disturbances):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], len(self.year_range), 2).start()
        # process fire-----------------------
        logging.info("Start of projected fire processing...")
        fire_areaValue = round(fire_areaValue)
        if fire_areaValue>0:
            fire_proj_dist_temp = "fire_proj_dist_temp"
            fire_proj_dist_temp1 = "fire_proj_dist_temp1"
            arcpy.CreateFeatureclass_management(self.outLocation, fire_proj_dist_temp, "", "inventory_gridded_1990","","","inventory_gridded_1990")
            arcpy.MakeFeatureLayer_management("inventory_gridded_1990", "inventory_gridded_1990_layer")
            for year in self.year_range:
            	# beginning of GA replace
                number_features = [row[0] for row in arcpy.da.SearchCursor("inventory_gridded_1990_layer", "OBJECTID")]
                temp_inventory_count = int(arcpy.GetCount_management("inventory_gridded_1990_layer").getOutput(0))
                features2Bselected = random.sample(number_features,int(round(fire_areaValue)))
                features2Bselected.append(0)
                features2Bselected = str(tuple(features2Bselected)).rstrip(',)') + ')'
                selectExpression = '{} IN {}'.format(arcpy.AddFieldDelimiters("inventory_gridded_1990_layer", "OBJECTID"), features2Bselected)
                arcpy.SelectLayerByAttribute_management("inventory_gridded_1990_layer","NEW_SELECTION", selectExpression)
                arcpy.CopyFeatures_management("inventory_gridded_1990_layer",r"{}\{}".format(self.outLocation,fire_proj_dist_temp1))
                arcpy.AddField_management(fire_proj_dist_temp1, field_name=self.distYr_field, field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
                arcpy.CalculateField_management(fire_proj_dist_temp1, field=self.distYr_field, expression=year, expression_type="PYTHON", code_block="")
                arcpy.Append_management(fire_proj_dist_temp1, fire_proj_dist_temp)
                pp.updateProgressP()

            # update the dist type and regen delay
            arcpy.CalculateField_management(fire_proj_dist_temp, field=self.distType_field, expression=self.fire_code, expression_type="PYTHON", code_block="")
            arcpy.CalculateField_management(fire_proj_dist_temp, field=self.regen_delay_field, expression="0", expression_type="PYTHON", code_block="")

            arcpy.Append_management(fire_proj_dist_temp, projected_disturbances)
            arcpy.Delete_management(fire_proj_dist_temp1)
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
            harvest_proj_dist_temp = "harvest_proj_dist_temp"
            harvest_proj_dist_temp1 = "harvest_proj_dist_temp1"
            arcpy.CreateFeatureclass_management(self.outLocation, harvest_proj_dist_temp, "", "inventory_gridded_1990","","","inventory_gridded_1990")
            arcpy.MakeFeatureLayer_management("inventory_gridded_1990", "inventory_gridded_1990_layer")
            for year in self.year_range:
                if year>=self.activity_start_year:
                    harvest_records = round(harvest_areaValue * (actv_harvest_percent/100.0))
                else:
                    harvest_records = round(harvest_areaValue)
                if harvest_records>=1:
					number_features = [row[0] for row in arcpy.da.SearchCursor("inventory_gridded_1990_layer", "OBJECTID")]
					temp_inventory_count = int(arcpy.GetCount_management("inventory_gridded_1990_layer").getOutput(0))
					features2Bselected = random.sample(number_features,int(round(harvest_records)))
					features2Bselected.append(0)
					features2Bselected = str(tuple(features2Bselected)).rstrip(',)') + ')'
					selectExpression = '{} IN {}'.format(arcpy.AddFieldDelimiters("inventory_gridded_1990_layer", "OBJECTID"), features2Bselected)
					arcpy.SelectLayerByAttribute_management("inventory_gridded_1990_layer","NEW_SELECTION", selectExpression)
					arcpy.CopyFeatures_management("inventory_gridded_1990_layer","{}/{}".format(self.outLocation,harvest_proj_dist_temp1))
					arcpy.AddField_management(harvest_proj_dist_temp1, field_name=self.distYr_field, field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
					arcpy.CalculateField_management(harvest_proj_dist_temp1, field=self.distYr_field, expression=year, expression_type="PYTHON", code_block="")
					arcpy.Append_management(harvest_proj_dist_temp1, harvest_proj_dist_temp)
					arcpy.SelectLayerByAttribute_management("inventory_gridded_1990_layer", "CLEAR_SELECTION")
					pp1.updateProgressP()

            # update the dist type and regen delay
            arcpy.CalculateField_management(harvest_proj_dist_temp, field=self.distType_field, expression=self.BASE_salvage_code, expression_type="PYTHON", code_block="")
            arcpy.CalculateField_management(harvest_proj_dist_temp, field=self.regen_delay_field, expression="0", expression_type="PYTHON", code_block="")

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
                        number_features = [row[0] for row in arcpy.da.SearchCursor(harvest_proj_dist_temp, "OBJECTID")]
                        temp_harvest_count = int(arcpy.GetCount_management(harvest_proj_dist_temp).getOutput(0))
                        features2Bselected = random.sample(number_features,(int(np.ceil(round(float(temp_harvest_count * PercSBofCC)/100)))))
                        features2Bselected.append(0)
                        features2Bselected = str(tuple(features2Bselected)).rstrip(',)') + ')'
                        selectExpression = '{} IN {}'.format(arcpy.AddFieldDelimiters(harvest_proj_dist_temp, "OBJECTID"), features2Bselected)
                        arcpy.SelectLayerByAttribute_management(harvest_proj_dist_temp,"NEW_SELECTION", selectExpression)
                        arcpy.CopyFeatures_management(harvest_proj_dist_temp,r"{}\{}".format(self.outLocation,slasburn_proj_dist_temp))
                	arcpy.CalculateField_management(slasburn_proj_dist_temp, self.distType_field, self.SB_code, "PYTHON", )
                	arcpy.Append_management(slasburn_proj_dist_temp, projected_disturbances)
                	arcpy.SelectLayerByAttribute_management(harvest_proj_dist_temp, "CLEAR_SELECTION")
                	pp.updateProgressP()
            arcpy.Delete_management(harvest_proj_dist_temp)
            arcpy.Delete_management(slasburn_proj_dist_temp)
        else:
            logging.info("No projected slashburn was generated because of no projected harvest.")
        pp.finish()

import numpy as np

class GenerateSlashburn(object):
    
    def __init__(self, arcpy):
        self.arcpy = arcpy

    def generateSlashburn(self, inventory_workspace, 
                          inventory_disturbance_year_fieldname, harvest_shp, harvest_shp_year_field, year_range, sb_percent):
        logging.info("generating slashburn")
        PercSBofCC = sb_percent

        logging.info('Prepping temporary workspace')
        temp_gdb = os.path.join(os.path.dirname(harvest_shp),"slashburn_temp.gdb")
        if os.path.exists(temp_gdb):
            self.arcpy.Delete_management(temp_gdb)
        self.arcpy.CreateFileGDB_management(os.path.dirname(harvest_shp), "slashburn_temp.gdb")
        self.arcpy.env.workspace = os.path.join(os.path.dirname(harvest_shp),"slashburn_temp.gdb")
        self.arcpy.env.overwriteOutput = True

        logging.info('Copying MergedDisturbances from inventory workspace')
        self.arcpy.FeatureClassToFeatureClass_conversion(os.path.join(inventory_workspace,"MergedDisturbances"),
            self.arcpy.env.workspace, "MergedDisturbances")
        self.arcpy.MakeFeatureLayer_management("MergedDisturbances", "temp_harvest")
        if "DistType" not in [f.name for f in self.arcpy.ListFields("temp_harvest")]:
            self.arcpy.AddField_management("temp_harvest", "DistType", "SHORT")
        self.arcpy.CreateFeatureclass_management(self.arcpy.env.workspace, "slashburn", "POLYGON", "temp_harvest", "SAME_AS_TEMPLATE", "SAME_AS_TEMPLATE", "temp_harvest")
        logging.info('Making slashburn for the range {}-{}'.format(year_range[0],year_range[-1]))
        logging.info('Selecting {}% of the harvest area in each year as slashburn...'.format(PercSBofCC))
        # Create SB records for each timestep
        for year in year_range:
            # Select only records corresponding to the current year being processed
            expression2 = '{} = {}'.format(self.arcpy.AddFieldDelimiters("temp_harvest", year_field), year)
            self.arcpy.SelectLayerByAttribute_management("temp_harvest", "NEW_SELECTION", expression2)
            # Select only records that intersect with the inventory and are harvest disturbances
            # Note assumption: Harvest disturbance if the harvest year field value = disturbance year field value
            # This assumption is used in the rollback update_inventory as well
            filter = "CELL_ID > 0 AND {} = {}".format(year_field, inventory_disturbance_year_fieldname)
            self.arcpy.SelectLayerByAttribute_management("temp_harvest", "SUBSET_SELECTION", filter)
            if int(self.arcpy.GetCount_management("temp_harvest").getOutput(0)) > 0:
                number_features = [row[0] for row in self.arcpy.da.SearchCursor("temp_harvest", "OBJECTID")]
                temp_harvest_count = int(self.arcpy.GetCount_management("temp_harvest").getOutput(0))
                features2Bselected = random.sample(number_features,(int(np.ceil(round(float(temp_harvest_count * PercSBofCC)/100)))))
                features2Bselected.append(0)
                features2Bselected = str(tuple(features2Bselected)).rstrip(',)') + ')'
                selectExpression = '{} IN {}'.format(self.arcpy.AddFieldDelimiters("temp_harvest", "OBJECTID"), features2Bselected)
                self.arcpy.SelectLayerByAttribute_management("temp_harvest","NEW_SELECTION", selectExpression)
                self.arcpy.CopyFeatures_management("temp_harvest","temp_SB")
                self.arcpy.CalculateField_management("temp_SB", "DistType", 13, "PYTHON", "")
                self.arcpy.Append_management("temp_SB", "slashburn")
            self.arcpy.SelectLayerByAttribute_management("temp_harvest", "CLEAR_SELECTION")
            pp.updateProgressP()

        sb_shp = os.path.join(os.path.dirname(harvest_shp), "slashburn.shp")
        if self.arcpy.Exists(sb_shp):
            self.arcpy.Delete_management(sb_shp)
        logging.info('Saving slashburn to {}'.format(sb_shp))
        self.arcpy.CopyFeatures_management("slashburn", sb_shp)

        logging.info('Deleting temporary workspace')
        self.arcpy.Delete_management("slashburn")
        self.arcpy.Delete_management("temp_harvest")
        self.arcpy.Delete_management("temp_SB")
        self.arcpy.Delete_management(temp_gdb)

        return sb_shp

# ---------------------------------------------------------------------------
# 02_Grid&Intersect_inventory.py
#
#Author: Byron Smiley
#Date: 2017_02_28
#
# Description:
#   1) Spatially joins the grid with the inventory polygon with the largest area
# within each grid cell
#   2) Takes the combined stand-replacing disturbances layer and intersects
# it with the gridded inventory. Output is all polygons in the inventory that would have been
# established during the rollup period intersect with the disturbances that occurred on
# those areas for disturbances that occured between inventory date and rollback start year.
#
#
#Processing time: 4 hrs 10 min 05 sec on A105338
# ---------------------------------------------------------------------------

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
## New

# Imports
import archook
archook.get_arcpy()
import arcpy
import inspect

class IntersectDisturbancesInventory(object):
    def __init__(self, inventory, spatialBoundaries, rollback_range, ProgressPrinter):
        self.ProgressPrinter = ProgressPrinter
        self.inventory = inventory
        self.spatialBoundaries = spatialBoundaries
        self.rollback_start = rollback_range[0]

        # Temp Layers
        self.disturbances_layer = r"in_memory\disturbances_layer"
        self.disturbances_layer2 = r"in_memory\disturbances_layer2"
        self.inventory_layer3 = r"in_memory\inventory_layer3"
        self.TSABoundary_layer = r"in_memory\TSABoundary_layer"

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
        self.spatial_boundaries = self.spatialBoundaries.getPathTSA()

        tasks = [
            lambda:self.addFields(),
            lambda:self.selectInventoryRecords(),
            lambda:self.clipMergedDisturbances(),
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
        for field_name in field_names:
            arcpy.AddField_management(self.gridded_inventory, field_name, "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            pp.updateProgressP()
        pp.finish()

    def selectInventoryRecords(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        inv_whereClause = '{} < {}'.format(arcpy.AddFieldDelimiters(self.inv_workspace, self.invAge_fieldName), self.rolledback_years)
        arcpy.Select_analysis(self.gridded_inventory, self.inventory_layer3, inv_whereClause)
        pp.finish()

    def clipMergedDisturbances(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        StudyArea_whereClause = '{} {} {}'.format(arcpy.AddFieldDelimiters(self.spatial_boundaries, self.studyArea_fieldName),
            self.studyAreaOperator, self.StudyArea)
        # Selecting Study area..."
        arcpy.Select_analysis(self.spatial_boundaries, self.TSABoundary_layer, StudyArea_whereClause)
        # Clipping merged disturbance to study area...
        arcpy.MakeFeatureLayer_management(self.disturbances, self.disturbances_layer)
        pp.finish()

    def selectDisturbanceRecords(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        #Select disturbance records that occur before inventory vintage
        dist_whereClause = '{} < {}'.format(arcpy.AddFieldDelimiters(self.disturbances, self.disturbance_fieldName), self.invVintage)
        arcpy.Select_analysis(self.disturbances_layer, self.disturbances_layer2, dist_whereClause)
        pp.finish()

    def intersectLayers(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        # Intersecting disturbance and Inventory layers...
        arcpy.Union_analysis([self.inventory_layer3,self.disturbances_layer2], self.temp_overlay, "ALL")
        pp.finish()

    def removeNonConcurring(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        nonConcurrence_whereClause = "{} <> ' '".format(arcpy.AddFieldDelimiters(self.output, "CELL_ID"))
        # Removing disturbance polygons where inventory doesnt spatially concur that a disturbance took place...
        # print nonConcurrence_whereClause
        arcpy.Select_analysis(self.temp_overlay, self.output, nonConcurrence_whereClause)
        # Repairing Geometry...
        arcpy.RepairGeometry_management(self.output, "DELETE_NULL")
        # print(arcpy.GetMessages())
        pp.finish()



# --------------------------------------------------------------------------------------------------------------------------------------------------------------
## Old Script
'''
# Import arcpy module
import arcpy
from arcpy import env
import os
arcpy.env.workspace = r"C:\Nick\GCBM\03_Cranbrook\05_working\02_layers\01_external_spatial_data\00_TSA05.gdb"
env.overwriteOutput = True
print "Start time: " +(time.strftime('%a %H:%M:%S'))

# Spatial Join tool--------------------------------------------------------------------
# Main function, all functions run in SpatialJoinOverlapsCrossings
def SpatialJoinLargestOverlap(target_features, join_features, out_fc, keep_all, spatial_rel):
    if spatial_rel == "largest_overlap":
        # Calculate intersection between Target Feature and Join Features
        intersect = arcpy.analysis.Intersect([target_features, join_features], "in_memory/intersect", "ONLY_FID")
        # Find which Join Feature has the largest overlap with each Target Feature
        # Need to know the Target Features shape type, to know to read the SHAPE_AREA oR SHAPE_LENGTH property
        geom = "AREA" if arcpy.Describe(target_features).shapeType.lower() == "polygon" and arcpy.Describe(join_features).shapeType.lower() == "polygon" else "LENGTH"
        fields = ["FID_{0}".format(os.path.splitext(os.path.basename(target_features))[0]),
                  "FID_{0}".format(os.path.splitext(os.path.basename(join_features))[0]),
                  "SHAPE@{0}".format(geom)]
        overlap_dict = {}
        with arcpy.da.SearchCursor(intersect, fields) as scur:
            for row in scur:
                try:
                    if row[2] > overlap_dict[row[0]][1]:
                        overlap_dict[row[0]] = [row[1], row[2]]
                except:
                    overlap_dict[row[0]] = [row[1], row[2]]

        # Copy the target features and write the largest overlap join feature ID to each record
        # Set up all fields from the target features + ORIG_FID
        fieldmappings = arcpy.FieldMappings()
        fieldmappings.addTable(target_features)
        fieldmap = arcpy.FieldMap()
        fieldmap.addInputField(target_features, arcpy.Describe(target_features).OIDFieldName)
        fld = fieldmap.outputField
        fld.type, fld.name, fld.aliasName = "LONG", "ORIG_FID", "ORIG_FID"
        fieldmap.outputField = fld
        fieldmappings.addFieldMap(fieldmap)
        # Perform the copy
        arcpy.conversion.FeatureClassToFeatureClass(target_features, os.path.dirname(out_fc), os.path.basename(out_fc), "", fieldmappings)
        # Add a new field JOIN_FID to contain the fid of the join feature with the largest overlap
        arcpy.management.AddField(out_fc, "JOIN_FID", "LONG")
        # Calculate the JOIN_FID field
        with arcpy.da.UpdateCursor(out_fc, ["ORIG_FID", "JOIN_FID"]) as ucur:
            for row in ucur:
                try:
                    row[1] = overlap_dict[row[0]][0]
                    ucur.updateRow(row)
                except:
                    if not keep_all:
                        ucur.deleteRow()
        # Join all attributes from the join features to the output
        joinfields = [x.name for x in arcpy.ListFields(join_features) if not x.required]
        arcpy.management.JoinField(out_fc, "JOIN_FID", join_features, arcpy.Describe(join_features).OIDFieldName, joinfields)


# Run the script
if __name__ == '__main__':
    # Get Parameters
    target_features = arcpy.GetParameterAsText(0)
    join_features = arcpy.GetParameterAsText(1)
    out_fc = arcpy.GetParameterAsText(2)
    keep_all = arcpy.GetParameter(3)
    spatial_rel = arcpy.GetParameterAsText(4).lower()

    SpatialJoinLargestOverlap(target_features, join_features, out_fc, keep_all, spatial_rel)
    print "finished"
# End of Spatial Join tool--------------------------------------------------------------------
# Local VARIABLES:
workspace = r"C:\Nick\GCBM\03_Cranbrook\05_working\02_layers\01_external_spatial_data\00_TSA05.gdb"
StudyArea = "'Cranbrook TSA'"
# StudyArea = "'100 Mile House TSA'"
invVintage = 2011
rollback_start = 1990
rolledback_years = invVintage - rollback_start
disturbance_fieldName = "DistYEAR"

disturbances_layer = "in_memory\disturbances_layer"
disturbances_layer2 = "in_memory\disturbances_layer2"
inventory_layer = "in_memory\inventory_layer"
inventory_layer2 = "in_memory\inventory_layer2"
inventory_layer3 = "in_memory\inventory_layer3"
TSABoundary_layer = "in_memory\TSABoundary_layer"

#field names
studyArea_fieldName = "TSA_NUMBER"
invAge_fieldName = "Age2011"
establishmentDate_fieldName = "DE_2011"
inv_dist_dateDiff = "Dist_DE_DIFF"
preDistAge = "preDistAge"
dist_type_field = "DistType"
regen_delay_field = "RegenDelay"
rollback_vintage_field = "Age1990"
new_disturbance_field = "DistYEAR_new"
nullID_field = "TileID"


# Inputs
inventory = r"{}\tsa05".format(workspace)
grid = r"{}\XYgrid_1ha".format(workspace)
gridded_inventory = r"{}\tsa05_inv_gridded".format(workspace)
disturbances = r"{}\MergedDisturbances".format(workspace)
temp_overlay = r"{}\temp_DisturbedInventory".format(workspace)
output = r"{}\DisturbedInventory".format(workspace)
TSABoundary = r"{}\..\01_spatial_reference\TSA_boundaries_2016.shp".format(workspace)

#Where Clauses
StudyArea_whereClause = '{} = {}'.format(arcpy.AddFieldDelimiters(TSABoundary, studyArea_fieldName), StudyArea)
invAge_whereClause = '{} > {}'.format(arcpy.AddFieldDelimiters(inventory, invAge_fieldName), 0)
inv_whereClause = '{} < {}'.format(arcpy.AddFieldDelimiters(inventory, invAge_fieldName), rolledback_years)
dist_whereClause = '{} < {}'.format(arcpy.AddFieldDelimiters(disturbances, disturbance_fieldName), invVintage)
nonConcurrence_whereClause = '{} > {}'.format(arcpy.AddFieldDelimiters(output, nullID_field), 0)
print nonConcurrence_whereClause
print "Making Feature layer..."
arcpy.MakeFeatureLayer_management(inventory, inventory_layer)

#Add all fields needed in this step
print "Adding fields..."
arcpy.AddField_management(inventory_layer, establishmentDate_fieldName, "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(inventory_layer, inv_dist_dateDiff, "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(inventory_layer, preDistAge, "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(inventory_layer, dist_type_field, "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(inventory_layer, regen_delay_field, "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(inventory_layer, rollback_vintage_field, "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(inventory_layer, new_disturbance_field, "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

# PROCESSES
#Select stands where age > zero
print "Filtering stands with age > zero..."
arcpy.Select_analysis(inventory_layer, inventory_layer2, invAge_whereClause)
#Grid intersect
#arcpy.Intersect_analysis([inventory_layer2,grid], gridded_inventory, "ALL", "", "INPUT")
# Join to 1ha cell based on largest area
SpatialJoinLargestOverlap(grid, inventory_layer2, gridded_inventory, False, "largest_overlap")
#Select inventory records that would have an establishment date during the rollback period but are > 0 age
print "Selecting Inventory records..."
arcpy.Select_analysis(gridded_inventory, inventory_layer3, inv_whereClause)

print "Selecting Study area..."
arcpy.Select_analysis(TSABoundary, TSABoundary_layer, StudyArea_whereClause)
print "Clipping merged disturbance to study area..."
#arcpy.Clip_analysis(disturbances, TSABoundary_layer, disturbances_layer)
arcpy.MakeFeatureLayer_management(disturbances, disturbances_layer)

#Select disturbance records that occur before inventory vintage
print "Selecting Disturbance records..."
arcpy.Select_analysis(disturbances_layer, disturbances_layer2, dist_whereClause)

#Intersect layers
print "Intersecting disturbance and Inventory layers..."
arcpy.Union_analysis([inventory_layer3,disturbances_layer2], temp_overlay, "ALL")
#arcpy.Intersect_analysis([inventory_layer3,disturbances_layer2], output, "ALL", "", "INPUT")

print "Removing disturbance polygons where inventory doesnt spatially concur that a disturbance took place..."

arcpy.Select_analysis(temp_overlay, output, nonConcurrence_whereClause)

# cur = arcpy.UpdateCursor(output, nonConcurrence_whereClause)
# for row in cur:
    # if not row.getValue(nullID_field):
        # row.deleteRow(row)

print "Reparing Geometry..."
arcpy.RepairGeometry_management(output, "DELETE_NULL")
print(arcpy.GetMessages())

print "End time: " +(time.strftime('%a %H:%M:%S'))
print "COMPLETE"
'''

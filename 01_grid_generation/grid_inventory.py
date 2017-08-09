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
import os
import inspect
import sys
from dbfread import DBF

class GridInventory(object):
    def __init__(self, inventory, outputDBF, ProgressPrinter):
        self.ProgressPrinter = ProgressPrinter
        self.inventory = inventory
        self.output_dbf_dir = outputDBF

        self.inventory_layer = r"in_memory\inventory_layer"
        self.inventory_layer2 = r"in_memory\inventory_layer2"
        self.grid = "XYgrid"
        self.gridded_inventory = "inventory_gridded"

    def gridInventory(self):
        arcpy.env.workspace = self.inventory.getWorkspace()
        arcpy.env.overwriteOutput = True
        arcpy.Delete_management("in_memory")
        self.invAge_fieldName = self.inventory.getFieldNames()['age']

        tasks = [
            lambda:self.spatialJoin(),
            lambda:self.makeFeatureLayer(),
            lambda:self.selectGreaterThanZeroAgeStands(),
            lambda:self.SpatialJoinLargestOverlap(self.grid, self.inventory_layer2, self.gridded_inventory, False, "largest_overlap"),
            lambda:self.exportGriddedInvDBF()
        ]
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], len(tasks)).start()
        for t in tasks:
            t()
            pp.updateProgressV()
        pp.finish()

    def spatialJoin(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        target_features = arcpy.GetParameterAsText(0)
        join_features = arcpy.GetParameterAsText(1)
        out_fc = arcpy.GetParameterAsText(2)
        keep_all = arcpy.GetParameter(3)
        spatial_rel = arcpy.GetParameterAsText(4).lower()

        self.SpatialJoinLargestOverlap(target_features, join_features, out_fc, keep_all, spatial_rel)
        pp.finish()

    def makeFeatureLayer(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        arcpy.MakeFeatureLayer_management(os.path.join(self.inventory.getWorkspace(), self.inventory.getLayerName()), self.inventory_layer)
        pp.finish()

    def selectGreaterThanZeroAgeStands(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        invAge_whereClause = '{} > {}'.format(arcpy.AddFieldDelimiters(os.path.join(self.inventory.getWorkspace(), self.inventory.getLayerName()), self.invAge_fieldName), 0)
        arcpy.Select_analysis(self.inventory_layer, self.inventory_layer2, invAge_whereClause)
        arcpy.RepairGeometry_management(self.inventory_layer2, "DELETE_NULL")
        pp.finish()

    # Spatial Join tool--------------------------------------------------------------------
    # Main function, all functions run in SpatialJoinOverlapsCrossings
    def SpatialJoinLargestOverlap(self, target_features, join_features, out_fc, keep_all, spatial_rel):
        pp1 = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        if spatial_rel == "largest_overlap":
            # Calculate intersection between Target Feature and Join Features
            intersect = arcpy.analysis.Intersect([target_features, join_features], "intersect", "ONLY_FID", "", "INPUT")
            # Find which Join Feature has the largest overlap with each Target Feature
            # Need to know the Target Features shape type, to know to read the SHAPE_AREA oR SHAPE_LENGTH property
            geom = "AREA" if arcpy.Describe(target_features).shapeType.lower() == "polygon" and arcpy.Describe(join_features).shapeType.lower() == "polygon" else "LENGTH"
            fields = ["FID_{0}".format(os.path.splitext(os.path.basename(target_features))[0]),
                      "FID_{0}".format(os.path.splitext(os.path.basename(join_features))[0]),
                      "SHAPE@{0}".format(geom)]
            overlap_dict = {}
            with arcpy.da.SearchCursor(intersect, fields) as scur:
                pp2 = self.ProgressPrinter.newProcess("search for overlap", 1, 2).start()
                for row in scur:
                    row = (row[0], row[1], round(row[2]*1000000,6))
                    try:
                        if row[2] > overlap_dict[row[0]][1]:
                            overlap_dict[row[0]] = [row[1], row[2]]
                    except:
                        overlap_dict[row[0]] = [row[1], row[2]]
                pp2.finish()
            arcpy.Delete_management("intersect")
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
            arcpy.conversion.FeatureClassToFeatureClass(target_features, self.inventory.getWorkspace(), os.path.basename(out_fc), "", fieldmappings)
            # Add a new field JOIN_FID to contain the fid of the join feature with the largest overlap
            arcpy.management.AddField(out_fc, "JOIN_FID", "LONG")
            # Calculate the JOIN_FID field
            with arcpy.da.UpdateCursor(out_fc, ["ORIG_FID", "JOIN_FID"]) as ucur:
                pp2 = self.ProgressPrinter.newProcess("update rows", 1, 2).start()
                for row in ucur:
                    try:
                        row[1] = overlap_dict[row[0]][0]
                        ucur.updateRow(row)
                    except:
                        if not keep_all:
                            ucur.deleteRow()
                pp2.finish()
            # Join all attributes from the join features to the output
            pp2 = self.ProgressPrinter.newProcess("join fields", 1, 2).start()
            joinfields = [x.name for x in arcpy.ListFields(join_features) if not x.required]
            arcpy.management.JoinField(out_fc, "JOIN_FID", join_features, arcpy.Describe(join_features).OIDFieldName, joinfields)
            pp2.finish()
        pp1.finish()

    def exportGriddedInvDBF(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        arcpy.env.workspace = self.inventory.getWorkspace()
        prev = sys.stdout
        silenced = open('nul', 'w')
        sys.stdout = silenced
        arcpy.TableToDBASE_conversion("inventory_gridded", self.output_dbf_dir)
        pp.finish()
        sys.stdout = prev
        self.inventory.setLayerName("inventory_gridded")
        pp.finish()

    def exportInventory(self, inventory_raster_out, resolution):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        print "\tExporting inventory to raster..."
        arcpy.env.overwriteOutput = True
        classifier_names = self.inventory.getClassifiers()
        fields = {
            "age": self.inventory.getFieldNames()["age"],
            "species": self.inventory.getFieldNames()["species"]
            # "ownership": self.inventory.getFieldNames()["ownership"],
            # "FMLB": self.inventory.getFieldNames()["FMLB"],
            # "THLB": self.inventory.getFieldNames()["THLB"]
        }
        for classifier_name in classifier_names:
            field_name = self.inventory.getClassifierAttr(classifier_name)
            file_path = os.path.join(inventory_raster_out, "{}.tif".format(classifier_name))
            arcpy.FeatureToRaster_conversion("inventory_gridded", field_name, file_path, resolution)
            self.inventory.addRaster(file_path, classifier_name, self.createAttributeTable(
                os.path.join(os.path.dirname(file_path), "{}.tif.vat.dbf".format(classifier_name)), field_name))
            # arcpy.DeleteField_management(file_path, field_name)
        for attr in fields:
            field_name = fields[attr]
            file_path = os.path.join(inventory_raster_out,"{}.tif".format(attr))
            arcpy.FeatureToRaster_conversion("inventory_gridded", field_name, file_path, resolution)
            self.inventory.addRaster(file_path, attr, self.createAttributeTable(
                os.path.join(os.path.dirname(file_path), "{}.tif.vat.dbf".format(attr)), field_name))
            # arcpy.DeleteField_management(file_path, field_name)
        pp.finish()

    def createAttributeTable(self, dbf_path, field_name):
        attr_table = {}
        for row in DBF(dbf_path):
            if len(row)<3:
                return None
            attr_table.update({row.items()[0][1]: [row.items()[-1][1]]})
        return attr_table

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
## Old Script
'''
# Import arcpy module
import arcpy
from arcpy import env
import os
arcpy.env.workspace = r"H:\Nick\GCBM\00_Testing\05_working\02_layers\01_external_spatial_data\00_Workspace.gdb"
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
workspace = r"H:\Nick\GCBM\00_Testing\05_working\02_layers\01_external_spatial_data\00_Workspace.gdb"
StudyArea = "'Cranbrook TSA'"
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
inventory = r"{}\tsaTEST".format(workspace)
grid = r"{}\XYgrid_1ha".format(workspace)
gridded_inventory = r"{}\inventory_gridded".format(workspace)
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

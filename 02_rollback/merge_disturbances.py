# ---------------------------------------------------------------------------
# 01_MergeDisturbances.py
#
#Author: Byron Smiley
#Date: 2016_12_15
#
# Description: Takes all disturbances in two directories (wildfire and harvest) and
# merges the shape files into a single dataset merging the first inputs field values
# over others were overlap exists (this can be edited.)
#
#Processing time: 48 min 22 sec on A105338 (longer)
# ---------------------------------------------------------------------------

# --------------------------------------------------------------------------------------------------------------------------------------------------------------
## New

# Imports
import os
import archook
archook.get_arcpy()
import arcpy
import inspect
import glob
import logging


class MergeDisturbances(object):
    def __init__(self, inventory, disturbances, ProgressPrinter):
        logging.info("Initializing class {}".format(self.__class__.__name__))
        self.ProgressPrinter = ProgressPrinter
        self.inventory = inventory
        self.disturbances = disturbances

        # for disturbance in disturbances if disturbance.standReplacing==1:
        #     self.distWS.append(disturbance)

    def scan_for_layers(self, path, filter):
        return sorted(glob.glob(os.path.join(path, filter)),
                      key=os.path.basename)

    def runMergeDisturbances(self):
        self.workspace = self.inventory.getWorkspace()
        self.grid = r"{}\XYgrid".format(self.workspace)
        self.output = r"{}\MergedDisturbances_polys".format(self.workspace)
        self.gridded_output = r"{}\MergedDisturbances".format(self.workspace)

        tasks = [
            lambda:self.spatialJoin(),
            lambda:self.prepFieldMap(),
            lambda:self.mergeLayers()
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

    def prepFieldMap(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        fm_year = arcpy.FieldMap()
        self.fms = arcpy.FieldMappings()

        self.vTab = arcpy.ValueTable()
        for dist in self.disturbances:
            ws = dist.getWorkspace()
            arcpy.env.workspace = ws
            arcpy.env.overwriteOutput = True
            fcs1 = self.scan_for_layers(ws, dist.getFilter())
            if fcs1:
                # print "Old fire list is: ", fcs1
                for fc in fcs1:
                    # fc = os.path.join(ws, fc)
                    self.fms.addTable(fc)
                    if "NBAC" in fc:
                        fm_year.addInputField(fc, dist.getYearField(), 0, 3)
                    else:
                        fm_year.addInputField(fc, dist.getYearField())
                    self.vTab.addRow(fc)
        # Set the merge rule to find the First value of all fields in the
        # FieldMap object
        fm_year.mergeRule = 'First'

        # Set the output field properties for FieldMap objects
        field_name = fm_year.outputField
        field_name.name = 'DistYEAR'
        field_name.aliasName = 'DistYEAR'
        fm_year.outputField = field_name
        logging.info('Mapping stand-replacing disturbance years to field {}'.format(fm_year.outputField.name))

        # Add the FieldMap objects to the FieldMappings object
        self.fms.addFieldMap(fm_year)
        pp.finish()

    def mergeLayers(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        arcpy.env.workspace = self.workspace
        arcpy.Merge_management(self.vTab, self.output, self.fms)
        self.SpatialJoinLargestOverlap(self.grid, self.output, self.gridded_output, False, "largest_overlap")
        pp.finish()

    # Spatial Join tool--------------------------------------------------------------------
    # Main function, all functions run in SpatialJoinOverlapsCrossings
    def SpatialJoinLargestOverlap(self, target_features, join_features, out_fc, keep_all, spatial_rel):
        pp1 = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 2).start()
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
                pp2 = self.ProgressPrinter.newProcess("search for overlap", 1, 3).start()
                for row in scur:
                    try:
                        if row[2] > overlap_dict[row[0]][1]:
                            overlap_dict[row[0]] = [row[1], row[2]]
                    except:
                        overlap_dict[row[0]] = [row[1], row[2]]
                pp2.finish()

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
                pp2 = self.ProgressPrinter.newProcess("update rows", 1, 3).start()
                for row in ucur:
                    try:
                        row[1] = overlap_dict[row[0]][0]
                        ucur.updateRow(row)
                    except:
                        if not keep_all:
                            ucur.deleteRow()
                pp2.finish()
            # Join all attributes from the join features to the output
            pp2 = self.ProgressPrinter.newProcess("join fields", 1, 3).start()
            joinfields = [x.name for x in arcpy.ListFields(join_features) if not x.required]
            arcpy.management.JoinField(out_fc, "JOIN_FID", join_features, arcpy.Describe(join_features).OIDFieldName, joinfields)
            pp2.finish()
            pp1.finish()


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
## Old Script
'''
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
# VARIABLES:
workspace = r"H:\Nick\GCBM\00_Testing\05_working\02_layers\01_external_spatial_data\00_Workspace.gdb"
# Disturbance Input workspaces
distWS = [r"H:\Nick\GCBM\00_Testing\05_working\02_layers\01_external_spatial_data\03_disturbances\01_historic\02_harvest",  r"H:\Nick\GCBM\00_Testing\05_working\02_layers\01_external_spatial_data\03_disturbances\01_historic\01_fire\shapefiles"]

grid = r"{}\XYgrid_1ha".format(workspace)
output = r"{}\MergedDisturbances_polys".format(workspace)
gridded_output = r"{}\MergedDisturbances".format(workspace)
# PROCESSES
# Create field map
# Create the required FieldMap and FieldMappings objects
print "Prepping Field Map...."
fm_year = arcpy.FieldMap()
fms = arcpy.FieldMappings()

# Get the field names for all original files
NBAC_yr = "EDATE"
NFDB_yr = "YEAR_"
CC_YR = "HARV_YR"

fc_list = []
vTab = arcpy.ValueTable()
for ws in distWS:
    arcpy.env.workspace = ws
    fcs1 = arcpy.ListFeatureClasses("NFDB*", "Polygon")
    print "Old fire list is: "
    print fcs1
    for fc in fcs1:
        if fc!=[]:
            fc = os.path.join(ws, fc)
            fms.addTable(fc)
            fm_year.addInputField(fc, NFDB_yr)
            vTab.addRow(fc)
    fcs2 = arcpy.ListFeatureClasses("NBAC*", "Polygon")
    print "New fire list is: "
    print fcs2
    for fc in fcs2:
        if fc!=[]:
            fc = os.path.join(ws, fc)
            fms.addTable(fc)
            fm_year.addInputField(fc, NBAC_yr, 0,3)
            vTab.addRow(fc)
    harvest = arcpy.ListFeatureClasses("BC_cutblocks90_15*", "Polygon")
    print "Cutblocks list is: "
    print harvest
    for fc in harvest:
        if fc!=[]:
            fc = os.path.join(ws, fc)
            fms.addTable(fc)
            fm_year.addInputField(fc, CC_YR)
            vTab.addRow(fc)

# Set the merge rule to find the First value of all fields in the
# FieldMap object
fm_year.mergeRule = 'First'
print "vTab equals: "
print vTab
# Set the output field properties for FieldMap objects
field_name = fm_year.outputField
field_name.name = 'DistYEAR'
field_name.aliasName = 'DistYEAR'
fm_year.outputField = field_name

# Add the FieldMap objects to the FieldMappings object
fms.addFieldMap(fm_year)
#Merge Layers
print "Merging layers..."
arcpy.env.workspace = workspace
arcpy.Merge_management(vTab, output, fms)
SpatialJoinLargestOverlap(grid, output, gridded_output, False, "largest_overlap")

print "End time: " +(time.strftime('%a %H:%M:%S'))
print "COMPLETE"
'''

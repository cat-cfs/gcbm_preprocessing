'''
Author: Byron Smiley
Date: 2016_12_15

Takes all disturbances in two directories (wildfire and harvest) and
merges the shape files into a single dataset merging the first inputs field values
over others were overlap exists (this can be edited.)
'''
import os
import inspect
import glob
import logging
from preprocess_tools.licensemanager import *

class MergeDisturbances(object):

    def scan_for_layers(self, path, filter):
        return sorted(glob.glob(os.path.join(path, filter)),
                      key=os.path.basename)

    def runMergeDisturbances(self, workspace, disturbances):
        
        grid = r"{}\XYgrid".format(workspace)
        output = r"{}\MergedDisturbances_polys".format(workspace)
        gridded_output = r"{}\MergedDisturbances".format(workspace)

        self.spatialJoin(),
        fms, vtab = self.prepFieldMap(disturbances),
        self.mergeLayers(workspace, fms, vTab, output, grid, gridded_output)

    def spatialJoin(self):
        with arc_license(Products.ARC) as arcpy:
            target_features = arcpy.GetParameterAsText(0)
            join_features = arcpy.GetParameterAsText(1)
            out_fc = arcpy.GetParameterAsText(2)
            keep_all = arcpy.GetParameter(3)
            spatial_rel = arcpy.GetParameterAsText(4).lower()
            self.SpatialJoinLargestOverlap(target_features, join_features, out_fc, keep_all, spatial_rel)

    def prepFieldMap(self, disturbances):
        with arc_license(Products.ARC) as arcpy:
            fm_year = arcpy.FieldMap()
            fms = arcpy.FieldMappings()
            vTab = arcpy.ValueTable()
            
            for dist in disturbances:
                ws = dist["Workspace"]
                arcpy.env.workspace = ws
                arcpy.env.overwriteOutput = True
                fcs1 = self.scan_for_layers(ws, dist["Filter"])
                if fcs1:
                    for fc in fcs1:
                        self.fms.addTable(fc)
                        if "NBAC" in fc:
                            fm_year.addInputField(fc, dist["YearField"], 0, 3)
                        else:
                            fm_year.addInputField(fc, dist["YearField"])
                        vTab.addRow(fc)
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
            fms.addFieldMap(fm_year)
            return fms, vtab

    def mergeLayers(self, workspace, fms, vtab, output_name, grid_name, gridded_output_name):
        with arc_license(Products.ARC) as arcpy:
            arcpy.env.workspace = workspace
            arcpy.Merge_management(vTab, output_name, fms)
            self.SpatialJoinLargestOverlap(grid_name, output_name, gridded_output_name, False, "largest_overlap")

    # Spatial Join tool--------------------------------------------------------------------
    # Main function, all functions run in SpatialJoinOverlapsCrossings
    def SpatialJoinLargestOverlap(self, target_features, join_features, out_fc, keep_all, spatial_rel):
        if spatial_rel != "largest_overlap":
            return

        with arc_license(Products.ARC) as arcpy:
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

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


class MergeDisturbances(object):

    def __init__(self, arcpy, workspace, disturbances):
        self.arcpy = arcpy
        self.workspace = workspace
        self.disturbances = disturbances

    def scan_for_layers(self, path, filter):
        return sorted(glob.glob(os.path.join(path, filter)),
                      key=os.path.basename)

    def runMergeDisturbances(self):
        logging.info("merging disturbances")
        grid = r"{}\XYgrid".format(self.workspace)
        output = r"{}\MergedDisturbances_polys".format(self.workspace)
        gridded_output = r"{}\MergedDisturbances".format(self.workspace)

        #self.spatialJoin()
        fms, vtab = self.prepFieldMap(self.disturbances)
        self.mergeLayers(fms, vtab, output, grid, gridded_output)

    def prepFieldMap(self, disturbances):
        logging.info("preparing field map")

        fm_year = self.arcpy.FieldMap()
        fms = self.arcpy.FieldMappings()
        vTab = self.arcpy.ValueTable()
            
        for dist in disturbances:
            ws = dist["Workspace"]
            self.arcpy.env.workspace = ws
            self.arcpy.env.overwriteOutput = True
            fcs1 = self.scan_for_layers(ws, dist["WorkspaceFilter"])
            if fcs1:
                for fc in fcs1:
                    fms.addTable(fc)
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
        return fms, vTab

    def mergeLayers(self, fms, vtab, output_name, grid_name, gridded_output_name):
        logging.info("merging layers")
        self.arcpy.env.workspace = self.workspace
        self.arcpy.Merge_management(vtab, output_name, fms)
        self.SpatialJoinLargestOverlap(grid_name, output_name, gridded_output_name, False, "largest_overlap")

    # Spatial Join tool--------------------------------------------------------------------
    # Main function, all functions run in SpatialJoinOverlapsCrossings
    def SpatialJoinLargestOverlap(self, target_features, join_features, out_fc, keep_all, spatial_rel):
        if spatial_rel != "largest_overlap":
            return
        logging.info("running spatial join")
        # Calculate intersection between Target Feature and Join Features
        intersect = self.arcpy.analysis.Intersect([target_features, join_features], "in_memory/intersect", "ONLY_FID")
        # Find which Join Feature has the largest overlap with each Target Feature
        # Need to know the Target Features shape type, to know to read the SHAPE_AREA oR SHAPE_LENGTH property
        geom = "AREA" if self.arcpy.Describe(target_features).shapeType.lower() == "polygon" and self.arcpy.Describe(join_features).shapeType.lower() == "polygon" else "LENGTH"
        fields = ["FID_{0}".format(os.path.splitext(os.path.basename(target_features))[0]),
                    "FID_{0}".format(os.path.splitext(os.path.basename(join_features))[0]),
                    "SHAPE@{0}".format(geom)]

        overlap_dict = {}
        logging.info("spatial join: searching for intersections")
        with self.arcpy.da.SearchCursor(intersect, fields) as scur:
            for row in scur:
                try:
                    if row[2] > overlap_dict[row[0]][1]:
                        overlap_dict[row[0]] = [row[1], row[2]]
                except:
                    logging.exception()
                    overlap_dict[row[0]] = [row[1], row[2]]

        # Copy the target features and write the largest overlap join feature ID to each record
        # Set up all fields from the target features + ORIG_FID
        fieldmappings = self.arcpy.FieldMappings()
        fieldmappings.addTable(target_features)
        fieldmap = self.arcpy.FieldMap()
        fieldmap.addInputField(target_features, self.arcpy.Describe(target_features).OIDFieldName)
        fld = fieldmap.outputField
        fld.type, fld.name, fld.aliasName = "LONG", "ORIG_FID", "ORIG_FID"
        fieldmap.outputField = fld
        fieldmappings.addFieldMap(fieldmap)
        # Perform the copy
        self.arcpy.conversion.FeatureClassToFeatureClass(target_features, os.path.dirname(out_fc), os.path.basename(out_fc), "", fieldmappings)
        # Add a new field JOIN_FID to contain the fid of the join feature with the largest overlap
        self.arcpy.management.AddField(out_fc, "JOIN_FID", "LONG")
        # Calculate the JOIN_FID field
        with self.arcpy.da.UpdateCursor(out_fc, ["ORIG_FID", "JOIN_FID"]) as ucur:
            logging.info("spatial join: updating")
            for row in ucur:
                try:
                    row[1] = overlap_dict[row[0]][0]
                    ucur.updateRow(row)
                except:
                    logging.exception()
                    if not keep_all:
                        ucur.deleteRow()

        # Join all attributes from the join features to the output
        joinfields = [x.name for x in self.arcpy.ListFields(join_features) if not x.required]
        self.arcpy.management.JoinField(out_fc, "JOIN_FID", join_features, self.arcpy.Describe(join_features).OIDFieldName, joinfields)

'''
Author: Byron Smiley
Date: 2017_02_28

Description:
  1) Spatially joins the grid with the inventory polygon with the largest area
     within each grid cell

  2) Takes the combined stand-replacing disturbances layer and intersects
     it with the gridded inventory. Output is all polygons in the inventory that would have been
     established during the rollup period intersect with the disturbances that occurred on
     those areas for disturbances that occured between inventory date and rollback start year.
'''
import os
import inspect
import sys
import logging
from dbfread import DBF


class GridInventory(object):
    def __init__(self, arcpy, area_majority_rule=True):

        self.arcpy = arcpy

        self.area_majority_rule = area_majority_rule

        self.inventory_layer = r"in_memory\inventory_layer"
        self.inventory_layer2 = r"in_memory\inventory_layer2"
        self.grid = "XYgrid"
        self.gridded_inventory = "inventory_gridded"

    def gridInventory(self, workspace, workspace_filter, ageFieldName ):
        logging.info("gridding inventory")
        self.arcpy.env.workspace = workspace
        self.arcpy.env.overwriteOutput = True
        self.arcpy.Delete_management("in_memory")

        #self.spatialJoin(workspace)
        self.makeFeatureLayer(
            workspace = workspace,
            workspace_filter = workspace_filter)

        self.selectGreaterThanZeroAgeStands(
            workspace = workspace,
            workspace_filter = workspace_filter,
            ageFieldName=ageFieldName)

        if self.area_majority_rule==True:
            self.SpatialJoinLargestOverlap(
                workspace = workspace,
                target_features = self.grid,
                join_features = self.inventory_layer2,
                out_fc = self.gridded_inventory,
                keep_all = False,
                spatial_rel = "largest_overlap")
        else:
            self.spatialJoinCentroid(
                grid = self.grid,
                inv = self.inventory_layer2,
                out = self.gridded_inventory,
                ageFieldName = ageFieldName)

    def makeFeatureLayer(self, workspace, workspace_filter):
        logging.info("making feature layer")
        self.arcpy.MakeFeatureLayer_management(os.path.join(workspace, workspace_filter), self.inventory_layer)

    def selectGreaterThanZeroAgeStands(self, workspace, workspace_filter, ageFieldName):
        logging.info("selecting >0 stands")
        invAge_whereClause = '{} > {}'.format(self.arcpy.AddFieldDelimiters(os.path.join(workspace, workspace_filter), ageFieldName), 0)
        self.arcpy.Select_analysis(self.inventory_layer, self.inventory_layer2, invAge_whereClause)
        self.arcpy.RepairGeometry_management(self.inventory_layer2, "DELETE_NULL")

    # Spatial Join tool--------------------------------------------------------------------
    # Main function, all functions run in SpatialJoinOverlapsCrossings
    def SpatialJoinLargestOverlap(self, workspace, target_features, join_features, out_fc, keep_all, spatial_rel):
        if spatial_rel != "largest_overlap":
            return
        logging.info("running spatial join (largest overlap method)")

        # Calculate intersection between Target Feature and Join Features
        intersect = self.arcpy.analysis.Intersect([target_features, join_features], "intersect", "ONLY_FID", "", "INPUT")
        # Find which Join Feature has the largest overlap with each Target Feature
        # Need to know the Target Features shape type, to know to read the SHAPE_AREA oR SHAPE_LENGTH property
        geom = "AREA" if self.arcpy.Describe(target_features).shapeType.lower() == "polygon" and \
            self.arcpy.Describe(join_features).shapeType.lower() == "polygon" else "LENGTH"
        fields = ["FID_{0}".format(os.path.splitext(os.path.basename(target_features))[0]),
                    "FID_{0}".format(os.path.splitext(os.path.basename(join_features))[0]),
                    "SHAPE@{0}".format(geom)]
        overlap_dict = {}
        with self.arcpy.da.SearchCursor(intersect, fields) as scur:
            for row in scur:
                row = (row[0], row[1], round(row[2]*1000000,6))
                try:
                    if row[2] > overlap_dict[row[0]][1]:
                        overlap_dict[row[0]] = [row[1], row[2]]
                except:
                    overlap_dict[row[0]] = [row[1], row[2]]

        self.arcpy.Delete_management("intersect")
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
        self.arcpy.conversion.FeatureClassToFeatureClass(target_features, workspace, os.path.basename(out_fc), "", fieldmappings)
        # Add a new field JOIN_FID to contain the fid of the join feature with the largest overlap
        self.arcpy.management.AddField(out_fc, "JOIN_FID", "LONG")
        # Calculate the JOIN_FID field
        with self.arcpy.da.UpdateCursor(out_fc, ["ORIG_FID", "JOIN_FID"]) as ucur:
            for row in ucur:
                try:
                    row[1] = overlap_dict[row[0]][0]
                    ucur.updateRow(row)
                except:
                    if not keep_all:
                        ucur.deleteRow()
        # Join all attributes from the join features to the output

        joinfields = [x.name for x in self.arcpy.ListFields(join_features) if not x.required]
        self.arcpy.management.JoinField(out_fc, "JOIN_FID", join_features, self.arcpy.Describe(join_features).OIDFieldName, joinfields)


    def spatialJoinCentroid(self, grid, inv, out, ageFieldName):
        logging.info("running spatial join (centroid method)")

        if self.arcpy.Exists("inv_gridded_temp"):
            self.arcpy.Delete_management("inv_gridded_temp")
        self.arcpy.SpatialJoin_analysis(grid, inv, "inv_gridded_temp", "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "HAVE_THEIR_CENTER_IN", "", "")
        if self.arcpy.Exists(out):
            self.arcpy.Delete_management(out)
        self.arcpy.Select_analysis("inv_gridded_temp", out, "{} > 0".format(ageFieldName))
        self.arcpy.Delete_management("inv_gridded_temp")
    


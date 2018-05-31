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
from preprocess_tools.licensemanager import *

class GridInventory(object):
    def __init__(self, inventory, outputDBF, ProgressPrinter, area_majority_rule=True):
        logging.info("Initializing class {}".format(self.__class__.__name__))
        self.ProgressPrinter = ProgressPrinter
        self.inventory = inventory
        self.output_dbf_dir = outputDBF
        self.area_majority_rule = area_majority_rule

        self.inventory_layer = r"in_memory\inventory_layer"
        self.inventory_layer2 = r"in_memory\inventory_layer2"
        self.grid = "XYgrid"
        self.gridded_inventory = "inventory_gridded"

    def gridInventory(self):
        with arc_license(Products.ARCINFO) as arcpy:
            arcpy.env.workspace = self.inventory.getWorkspace()
            arcpy.env.overwriteOutput = True
            arcpy.Delete_management("in_memory")
            self.invAge_fieldName = self.inventory.getFieldNames()['age']

        if self.area_majority_rule==True:
            spatial_join = lambda:self.SpatialJoinLargestOverlap(self.grid, self.inventory_layer2, self.gridded_inventory, False, "largest_overlap")
        else:
            spatial_join = lambda:self.spatialJoinCentroid(self.grid, self.inventory_layer2, self.gridded_inventory)

        tasks = [
            lambda:self.spatialJoin(),
            lambda:self.makeFeatureLayer(),
            lambda:self.selectGreaterThanZeroAgeStands(),
            spatial_join
        ]
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], len(tasks)).start()
        for t in tasks:
            t()
            pp.updateProgressV()
        pp.finish()

    def spatialJoin(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        with arc_license(Products.ARCINFO) as arcpy:
            target_features = arcpy.GetParameterAsText(0)
            join_features = arcpy.GetParameterAsText(1)
            out_fc = arcpy.GetParameterAsText(2)
            keep_all = arcpy.GetParameter(3)
            spatial_rel = arcpy.GetParameterAsText(4).lower()
            self.SpatialJoinLargestOverlap(target_features, join_features, out_fc, keep_all, spatial_rel)

        pp.finish()

    def makeFeatureLayer(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        with arc_license(Products.ARCINFO) as arcpy:
            arcpy.MakeFeatureLayer_management(os.path.join(self.inventory.getWorkspace(), self.inventory.getLayerName()), self.inventory_layer)
        pp.finish()

    def selectGreaterThanZeroAgeStands(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        with arc_license(Products.ARCINFO) as arcpy:
            invAge_whereClause = '{} > {}'.format(arcpy.AddFieldDelimiters(os.path.join(self.inventory.getWorkspace(), self.inventory.getLayerName()), self.invAge_fieldName), 0)
            arcpy.Select_analysis(self.inventory_layer, self.inventory_layer2, invAge_whereClause)
            arcpy.RepairGeometry_management(self.inventory_layer2, "DELETE_NULL")
        pp.finish()

    # Spatial Join tool--------------------------------------------------------------------
    # Main function, all functions run in SpatialJoinOverlapsCrossings
    def SpatialJoinLargestOverlap(self, target_features, join_features, out_fc, keep_all, spatial_rel):
        if spatial_rel != "largest_overlap":
            return
            
        pp1 = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        with arc_license(Products.ARCINFO) as arcpy:
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

    def spatialJoinCentroid(self, grid, inv, out):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        with arc_license(Products.ARCINFO) as arcpy:
            if arcpy.Exists("inv_gridded_temp"):
                arcpy.Delete_management("inv_gridded_temp")
            arcpy.SpatialJoin_analysis(grid, inv, "inv_gridded_temp", "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "HAVE_THEIR_CENTER_IN", "", "")
            if arcpy.Exists(out):
                arcpy.Delete_management(out)
            arcpy.Select_analysis("inv_gridded_temp", out, "{} > 0".format(self.inventory.getFieldNames()['age']))
            arcpy.Delete_management("inv_gridded_temp")
        pp.finish()


    def exportGriddedInvDBF(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        self.inventory.setLayerName(self.gridded_inventory)
        with arc_license(Products.ARCINFO) as arcpy:
            arcpy.env.workspace = self.inventory.getWorkspace()
            arcpy.env.overwriteOutput = True

            fms = arcpy.FieldMappings()
            output_fields = ['age','X','Y','THEME1','THEME2','THEME3','THEME4','Shape_Area']
            inv_fields = [field.name for field in arcpy.ListFields(self.gridded_inventory)]
            if "NULL_FIELD" not in inv_fields:
                arcpy.AddField_management(self.gridded_inventory, "NULL_FIELD", "TEXT", "", "", "10", "", "NULLABLE", "NON_REQUIRED", "")

            for i, output_field in enumerate(output_fields):
                fm = arcpy.FieldMap()
                if output_field == 'THEME4':
                    input_field = 'CELL_ID'
                else:
                    try:
                        input_field = self.inventory.getFieldNames()[output_field]
                    except KeyError:
                        if output_field in inv_fields:
                            input_field = output_field
                        else:
                            input_field = None
                if input_field != None:
                    fm.addInputField(self.gridded_inventory, input_field)
                else:
                    fm.addInputField(self.gridded_inventory, "NULL_FIELD")
                logging.info('\t\t{} -> {}'.format(input_field, output_field))

                outf = fm.outputField
                outf.name = output_field
                fm.outputField = outf

                fms.addFieldMap(fm)
            print "Converting table.."
            arcpy.TableToTable_conversion(self.gridded_inventory, self.output_dbf_dir, "inventory.dbf", "", fms)
            arcpy.DeleteField_management(self.gridded_inventory, "NULL_FIELD")

        pp.finish()

    def exportInventory(self, inventory_raster_out, resolution, reportingIndicators):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        print "\tExporting inventory to raster..."
        with arc_license(Products.ARCINFO) as arcpy:
            arcpy.env.overwriteOutput = True
            reporting_indicators = reportingIndicators.getIndicators()
            classifier_names = self.inventory.getClassifiers()
            fields = {
                "age": self.inventory.getFieldNames()["age"],
                "species": self.inventory.getFieldNames()["species"]
            }
            for ri in reporting_indicators:
                if reporting_indicators[ri]==None:
                    fields.update({ri:ri})
            for classifier_name in classifier_names:
                field_name = self.inventory.getClassifierAttr(classifier_name)
                file_path = os.path.join(inventory_raster_out, "{}.tif".format(classifier_name))
                arcpy.FeatureToRaster_conversion(self.gridded_inventory, field_name, file_path, resolution)
                self.inventory.addRaster(file_path, classifier_name, self.createAttributeTable(
                    os.path.join(os.path.dirname(file_path), "{}.tif.vat.dbf".format(classifier_name)), field_name))
            for attr in fields:
                field_name = fields[attr]
                file_path = os.path.join(inventory_raster_out,"{}.tif".format(attr))
                arcpy.FeatureToRaster_conversion(self.gridded_inventory, field_name, file_path, resolution)
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

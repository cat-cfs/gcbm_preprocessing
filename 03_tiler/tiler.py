﻿
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
## New

import glob
import os
import gdal
import time

from mojadata.boundingbox import BoundingBox
from mojadata.tiler2d import Tiler2D
from mojadata.layer.vectorlayer import VectorLayer
from mojadata.layer.rasterlayer import RasterLayer
from mojadata.layer.gcbm.disturbancelayer import DisturbanceLayer
from mojadata.cleanup import cleanup
from mojadata.layer.attribute import Attribute
from mojadata.layer.gcbm.transitionrule import TransitionRule
from mojadata.layer.gcbm.transitionrulemanager import TransitionRuleManager

class Tiler(object):
    def __init__(self, outputDir, spatialBoundaries, inventory, historicDisturbances, rollbackDisturbances,
                    projectedDisturbances, NAmat, reportingIndicators, ProgressPrinter):
        self.ProgressPrinter = ProgressPrinter
        self.output_dir = outputDir
        self.spatial_boundaries = spatialBoundaries
        self.inventory = inventory
        self.historic_disturbances = historicDisturbances
        self.projected_disturbances = projectedDisturbances
        self.NAmat = NAmat
        self.reporting_ind = reportingIndicators
        self.rule_manager = TransitionRuleManager(os.path.abspath("{}\\transition_rules.csv".format(self.output_dir)))

    def runTiler(self, resolution, createReportingLayers):
        pp = self.ProgressPrinter.newProcess("runTiler", 4).start()
        k=0
        pp.updateProgressV(k)
        self.defineBoundingBox(resolution)
        pp.updateProgressV(k)
        layers = []
        if createReportingLayers:
            layers = self.initializeReportingLayers(layers)
        pp.updateProgressV(k)
        self.processHistoricDisturbances(layers)
        pp.updateProgressV(k)
        self.processRollbackDisturbances(layers)
        pp.updateProgressV(k)
        self.processProjectedDisturbances(layers)
        pp.updateProgressV(k)
        tiler.tile(layers)
        self.rule_manager.write_rules()
        pp.updateProgressV(k)
        pp.finish()

    def defineBoundingBox(self, resolution):
        with cleanup():
            self.bbox = BoundingBox(VectorLayer("bbox", self.inventory.getShpFilePath(),
                Attribute(self.inventory.getAgeField()),raw=True), pixel_size=resolution/100000.0)
            self.tiler = Tiler2D(self.bbox, use_bounding_box_resolution=True)

    def processReportingLayers(self, layers):

        layers.append(VectorLayer(self.inventory.getAgeField(), self.inventory.getShpFilePath(),
            Attribute(self.inventory.getAgeField()), raw=True, data_type=gdal.GDT_Int32))

        for classifier in self.inventory.getClassifiers():
            layers.append(VectorLayer(classifier, self.inventory.getShpFilePath(), Attribute(self.inventory.getClassifierAttr(classifier))))

        for reporting_indicator in self.reporting_ind.getReportingIndicators():
            layers.append(VectorLayer(self.reporting_indicator, self.reporting_ind.getShpFilePath(),
                Attribute(self.reporting_ind.getReportingIndAttr(reporting_indicator))))

        layers.append(RasterLayer(self.NAmat.getFilePath(), nodata_value=1.0e38))


    def processHistoricDisturbances(self, layers):
        for dist in self.historic_disturbances.getDisturbances():
            layers.append(DisturbanceLayer(
                self.rule_manager,
                VectorLayer(self.historic_disturbances.getYear(dist), self.historic_disturbances.getShpFilePath(dist), Attribute("Shape_Leng")),
                year=self.historic_disturbances.getYear(dist),
                disturbance_type=self.historic_disturbances.getDistType(dist),
                transition=TransitionRule(
                    regen_delay=0,
                    age_after=0)))

# mpb_shp_severity_to_dist_type_lookup = {
#     "V": "Mountain Pine Beetle – Very Severe Impact",
#     "S": "Mountain Pine Beetle - Severe Impact",
#     "M": "Mountain Pine Beetle - Moderate Impact",
#     "L": "Mountain Pine Beetle - Low Impact",
#     "4": "Mountain Pine Beetle – Very Severe Impact",
#     "3": "Mountain Pine Beetle - Severe Impact",
#     "2": "Mountain Pine Beetle - Moderate Impact",
#     "1": "Mountain Pine Beetle - Low Impact"
# }
#
# print "Processing Historic MPB Disturbances..."
# for file_name in scan_for_layers(r"{}\03_disturbances\01_historic\03_MPB\BCMPB\shapefiles".format(spatial_data), "*.shp"):
#     file_name_no_ext = os.path.basename(os.path.splitext(file_name)[0])
#     year = int(file_name_no_ext[-4:])
#     layers.append(DisturbanceLayer(
#         rule_manager,
#         VectorLayer(file_name_no_ext, file_name, Attribute("Severity", substitutions=mpb_shp_severity_to_dist_type_lookup)),
#         year=year,
#         disturbance_type=Attribute("Severity"),
#         transition=TransitionRule(
#             regen_delay=0,
#             age_after=-1)))


    def processRollbackDisturbances(self, layers):
        rollback_dist_lookup = {
            1: "Wild Fires",
            2: "Clearcut harvesting with salvage"
        }

        rollback_dist_shp = r"C:\Byron\04_100MileHouse\05_working\02_layers\01_external_spatial_data\03_distubances\03_rollbackDisturbances\rollbackDist.shp"
        for year in range(1990, 2015):
            for label, dist_code in (("Wild Fires", 1), ("Clearcut harvesting with salvage", 2)):
                layers.append(DisturbanceLayer(
                    rule_manager,
                    VectorLayer("rollback_{}_{}".format(label, year),
                                rollback_dist_shp,
                                [
                                    Attribute("DistYEAR_n", filter=lambda v, yr=year: v == yr),
                                    Attribute("DistType", filter=lambda v, dt=dist_code: v == dt, substitutions=rollback_dist_lookup),
                                    Attribute("RegenDelay")
                                ]),
                    year=year,
                    disturbance_type=Attribute("DistType"),
                    transition=TransitionRule(
                        regen_delay=Attribute("RegenDelay"),
                        age_after=0)))


    def processProjectedDisturbances(self, layers):
        futureDistTypeLookup = {
            11: "Base CC",
            7: "Wild Fires",
            13: "SlashBurning",
            10: "Partial Cut",
            6: "Base Salvage",
            2: "Wild Fire",
            1: "Clearcut harvesting with salvage"
        }
        future_start_year = 2010

        print "Processing Future Disturbances..."
        for file_name in scan_for_layers(r"{}\03_disturbances\02_future\projDist".format(spatial_data), "*.shp"):
            file_name_no_ext = os.path.basename(os.path.splitext(file_name)[0])
            year = future_start_year + int(file_name_no_ext.split("_")[1])
            layers.append(DisturbanceLayer(
                rule_manager,
                VectorLayer("Proj{}_{}".format("Disturbance", year), file_name, Attribute("dist_type_", substitutions=futureDistTypeLookup)),
                year=year,
                disturbance_type=Attribute("dist_type_"),
                transition=TransitionRule(
                    regen_delay=0,
                    age_after=0)))

    tiler.tile(layers)
    rule_manager.write_rules()

    def scan_for_layers(self, path, filter):
        return sorted(glob.glob(os.path.join(path, filter)),
                      key=os.path.basename)




# --------------------------------------------------------------------------------------------------------------------------------------------------------------
## Old Script


from mojadata.boundingbox import BoundingBox
from mojadata.tiler2d import Tiler2D
from mojadata.layer.vectorlayer import VectorLayer
from mojadata.layer.rasterlayer import RasterLayer
from mojadata.layer.gcbm.disturbancelayer import DisturbanceLayer
from mojadata.cleanup import cleanup
from mojadata.layer.attribute import Attribute
from mojadata.layer.gcbm.transitionrule import TransitionRule
from mojadata.layer.gcbm.transitionrulemanager import TransitionRuleManager

def scan_for_layers(path, filter):
    return sorted(glob.glob(os.path.join(path, filter)),
                  key=os.path.basename)

if __name__ == "__main__":
	print "Start time: " +(time.strftime('%a %H:%M:%S'))
	spatial_data = r"C:\Nick\GCBM\03_Cranbrook\05_working\02_layers\01_external_spatial_data"
	with cleanup():
		pspu_shp = r"{}\01_spatial_reference\PSPUS_2016.shp".format(spatial_data)
        inventory_shp = r"{}\02_inventory\177_inv.shp".format(spatial_data) #make sure this pointed to right place
        bbox = BoundingBox(VectorLayer("bbox", inventory_shp, Attribute("Age2011"),raw=True), pixel_size=0.001)
        tiler = Tiler2D(bbox, use_bounding_box_resolution=True)

        layers = [
            VectorLayer("age2011", inventory_shp, Attribute("Age2011"), raw=True, data_type=gdal.GDT_Int32),
            VectorLayer("species", inventory_shp, Attribute("LeadSpp")),
            VectorLayer("Ownership", inventory_shp, Attribute("Own")),
            VectorLayer("AU", inventory_shp, Attribute("AU")),
            VectorLayer("FMLB", inventory_shp, Attribute("FMLB")),
            VectorLayer("THLB", inventory_shp, Attribute("THLB")),
            VectorLayer("Admin", pspu_shp, Attribute("AdminBou_1")),
            VectorLayer("Eco", pspu_shp, Attribute("EcoBound_1")),
            RasterLayer(r"{}\04_environment\NAmerica_MAT_1971_2000.tif".format(spatial_data), nodata_value=1.0e38)
        ]

        rule_manager = TransitionRuleManager("transition_rules.csv")

        print "Processing Historic Fire Disturbances..."
        for file_name in scan_for_layers(r"{}\03_disturbances\01_historic\01_fire\shapefiles".format(spatial_data), "*.shp"):
           # Assume filenames are like "Wildfire_1990.shp", "Wildfire_NBAC_1991.shp"
           # i.e. the last 4 characters before the extension are the year.
            file_name_no_ext = os.path.basename(os.path.splitext(file_name)[0])
            year = file_name_no_ext[-4:]
            layers.append(DisturbanceLayer(
                rule_manager,
                VectorLayer(file_name_no_ext, file_name, Attribute("Shape_Leng")),
                year=year,
                disturbance_type="Wild Fires",
                transition=TransitionRule(
                    regen_delay=0,
                    age_after=0)))

        print "Processing Historic Harvest Disturbances..."
        cutblock_shp = r"{}\03_disturbances\01_historic\02_harvest\BC_cutblocks90_15.shp".format(spatial_data)
        for year in range(1990, 2015):
            layers.append(DisturbanceLayer(
                rule_manager,
                VectorLayer("harvest_{}".format(year), cutblock_shp, Attribute("HARV_YR", filter=lambda v, yr=year: v == yr)),
                year=year,
                disturbance_type="Clearcut harvesting with salvage",
                transition=TransitionRule(
                    regen_delay=0,
                    age_after=0)))

        mpb_shp_severity_to_dist_type_lookup = {
            "V": "Mountain Pine Beetle – Very Severe Impact",
            "S": "Mountain Pine Beetle - Severe Impact",
            "M": "Mountain Pine Beetle - Moderate Impact",
            "L": "Mountain Pine Beetle - Low Impact",
            "4": "Mountain Pine Beetle – Very Severe Impact",
            "3": "Mountain Pine Beetle - Severe Impact",
            "2": "Mountain Pine Beetle - Moderate Impact",
            "1": "Mountain Pine Beetle - Low Impact"
        }

        print "Processing Historic MPB Disturbances..."
        for file_name in scan_for_layers(r"{}\03_disturbances\01_historic\03_MPB\BCMPB\shapefiles".format(spatial_data), "*.shp"):
            file_name_no_ext = os.path.basename(os.path.splitext(file_name)[0])
            year = int(file_name_no_ext[-4:])
            layers.append(DisturbanceLayer(
                rule_manager,
                VectorLayer(file_name_no_ext, file_name, Attribute("Severity", substitutions=mpb_shp_severity_to_dist_type_lookup)),
                year=year,
                disturbance_type=Attribute("Severity"),
                transition=TransitionRule(
                    regen_delay=0,
                    age_after=-1)))

        futureDistTypeLookup = {
            11: "Base CC",
            7: "Wild Fires",
            13: "SlashBurning",
			10: "Partial Cut",
			6: "Base Salvage",
			2: "Wild Fire",
			1: "Clearcut harvesting with salvage"
        }
        future_start_year = 2010

        print "Processing Future Disturbances..."
        for file_name in scan_for_layers(r"{}\03_disturbances\02_future\projDist".format(spatial_data), "*.shp"):
            file_name_no_ext = os.path.basename(os.path.splitext(file_name)[0])
            year = future_start_year + int(file_name_no_ext.split("_")[1])
            layers.append(DisturbanceLayer(
                rule_manager,
                VectorLayer("Proj{}_{}".format("Disturbance", year), file_name, Attribute("dist_type_", substitutions=futureDistTypeLookup)),
                year=year,
                disturbance_type=Attribute("dist_type_"),
                transition=TransitionRule(
                    regen_delay=0,
                    age_after=0)))

        tiler.tile(layers)
        rule_manager.write_rules()

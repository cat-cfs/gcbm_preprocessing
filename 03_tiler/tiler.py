
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
## New

import glob
import os
import gdal
import time
import inspect
import sys
import logging
import shutil

from projected_disturbances_placeholder import ProjectedDisturbancesPlaceholder
from generate_historic_slashburn import GenerateSlashburn

from mojadata.boundingbox import BoundingBox
from mojadata.tiler2d import Tiler2D
from mojadata.layer.vectorlayer import VectorLayer
from mojadata.layer.rasterlayer import RasterLayer
from mojadata.layer.gcbm.disturbancelayer import DisturbanceLayer
from mojadata.cleanup import cleanup
from mojadata.layer.attribute import Attribute
from mojadata.layer.gcbm.transitionrule import TransitionRule
from mojadata.layer.gcbm.transitionrulemanager import TransitionRuleManager
from preprocess_tools.inputs import TransitionRules

class Tiler(object):
    def __init__(self, spatialBoundaries, inventory, rollbackDisturbances, NAmat, rollback_range,
                                        activity_start_year, historic_range, future_range, resolution, ProgressPrinter):
        logging.info("Initializing class {}".format(self.__class__.__name__))
        self.ProgressPrinter = ProgressPrinter
        self.spatial_boundaries = spatialBoundaries
        self.inventory = inventory
        self.rollback_disturbances = rollbackDisturbances
        self.NAmat = NAmat
        self.rollback_range = rollback_range
        self.activity_start_year = activity_start_year
        self.historic_range = historic_range
        self.future_range = future_range
        self.resolution = resolution
        self.rule_manager = TransitionRuleManager("transition_rules.csv")
        self.layers = []
        self.tiler = None

    def scan_for_layers(self, path, filter):
        return sorted(glob.glob(os.path.join(path, filter)),
                      key=os.path.basename)

    def defineBoundingBox(self, output_dir):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1).start()
        logging.info("Defining bounding box with inventory layer {}".format(os.path.basename(self.inventory.getRasters()[0].getPath())))
        logging.info("Bounding box will be stored in {}".format(os.path.join(output_dir, os.path.basename(self.inventory.getRasters()[0].getPath().split('.')[0]))))
        cwd = os.getcwd()
        os.chdir(output_dir)
        self.bbox = BoundingBox(RasterLayer(self.inventory.getRasters()[0].getPath()), pixel_size=self.resolution)
        self.tiler = Tiler2D(self.bbox, use_bounding_box_resolution=True)
        os.chdir(cwd)
        pp.finish()


    def processGeneralLayers(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3],1).start()
        general_lyrs = []
        for raster in self.inventory.getRasters():
            if raster.getAttrTable() == None:
                self.layers.append(RasterLayer(raster.getPath()))
            else:
                self.layers.append(RasterLayer(raster.getPath(),
                    nodata_value=255,
                    attributes = [raster.getAttr()],
                    attribute_table = raster.getAttrTable()))
            general_lyrs.append(os.path.basename(raster.getPath()).split('.')[0])

        for attr in self.spatial_boundaries.getAttributes():
            attr_field = self.spatial_boundaries.getAttrField(attr)
            self.layers.append(VectorLayer(attr, self.spatial_boundaries.getPathRI(),
                Attribute(attr_field)))
            general_lyrs.append(attr)

        self.layers.append(RasterLayer(self.NAmat.getPath(), nodata_value=1.0e38))
        general_lyrs.append(os.path.basename(self.NAmat.getPath()).split('.')[0])

        pp.finish()

        return general_lyrs


    def processRollbackDisturbances(self):
        rollback_dist_lookup = {
            1: "Wild Fires",
            2: "Clearcut harvesting with salvage",
            13: "SlashBurning"
        }
        rollback_name_lookup = {
            1: "fire",
            2: "harvest",
            13: "slashburn"
        }
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1).start()
        for year in range(self.rollback_range[0], self.rollback_range[1]+1):
            for dist_code in rollback_dist_lookup:
                label = rollback_dist_lookup[dist_code]
                name = rollback_name_lookup[dist_code]
                self.layers.append(DisturbanceLayer(
                    self.rule_manager,
                    VectorLayer("rollback_{}_{}".format(name, year),
                                self.rollback_disturbances.getPath(),
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
        pp.finish()

    # def processHistoricDisturbances(self):
    #     for dist in self.historic_fire.getDisturbances():
    #         self.layers.append(DisturbanceLayer(
    #             self.rule_manager,
    #             VectorLayer(dist.getYear(), dist.getFilePath(), Attribute("Shape_Leng")),
    #             year=dist.getYear(),
    #             disturbance_type=dist.getType(),
    #             transition=TransitionRule(
    #                 regen_delay=0,
    #                 age_after=0)))
    #
    #     for dist in self.historic_harvest.getDisturbances():
    #         self.layers.append(DisturbanceLayer(
    #             self.rule_manager,
    #             VectorLayer(dist.getYear(), dist.getFilePath(), Attribute("Shape_Leng")),
    #             year=dist.getYear(),
    #             disturbance_type=dist.getType(),
    #             transition=TransitionRule(
    #                 regen_delay=0,
    #                 age_after=0)))

    def processHistoricFireDisturbances(self, dist):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1).start()
        for file_name in self.scan_for_layers(dist.getWorkspace(), dist.getFilter()):
            # Assume filenames are like "Wildfire_1990.shp", "Wildfire_NBAC_1991.shp"
            # i.e. the last 4 characters before the extension are the year.
            file_name_no_ext = os.path.basename(os.path.splitext(file_name)[0])
            year = int(file_name_no_ext[-4:])
            if year in range(self.rollback_range[1]+1, self.historic_range[1]+1):
                self.layers.append(DisturbanceLayer(
                    self.rule_manager,
                    VectorLayer("fire_{}".format(year), file_name, Attribute("Shape_Leng")),
                    year=year,
                        disturbance_type="Wild Fires",
                        transition=TransitionRule(
                            regen_delay=0,
                            age_after=0)))
        pp.finish()

    def processHistoricHarvestDisturbances(self, dist, sb_percent):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1).start()
        harvest_shp = self.scan_for_layers(dist.getWorkspace(), dist.getFilter())[0]
        year_range = range(self.rollback_range[1]+1, self.historic_range[1]+1)
        if len(year_range)>0:
            sb = GenerateSlashburn(self.ProgressPrinter)
            sb_shp = sb.generateSlashburn(self.inventory, harvest_shp, "HARV_YR", year_range, sb_percent)

        for year in year_range:
            self.layers.append(DisturbanceLayer(
                self.rule_manager,
                VectorLayer("harvest_{}".format(year), harvest_shp, Attribute("HARV_YR", filter=lambda v, yr=year: v == yr)),
                year=year,
                disturbance_type="Clearcut harvesting with salvage",
                transition=TransitionRule(
                    regen_delay=0,
                    age_after=0)))
            self.layers.append(DisturbanceLayer(
                self.rule_manager,
                # Not sure why v != yr works instead of v == yr ..
                VectorLayer("slashburn_{}".format(year), sb_shp, Attribute("HARV_YR", filter=lambda v, yr=year: v != yr)),
                year=year,
                disturbance_type="SlashBurning",
                transition=TransitionRule(
                    regen_delay=0,
                    age_after=0)))
        pp.finish()

    def processHistoricInsectDisturbances(self, dist):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1).start()
        mpb_shp_severity_to_dist_type_lookup = {
            "V": "Mountain Pine Beetle - Very Severe Impact",
            "S": "Mountain Pine Beetle - Severe Impact",
            "M": "Mountain Pine Beetle - Moderate Impact",
            "L": "Mountain Pine Beetle - Low Impact",
            "4": "Mountain Pine Beetle - Very Severe Impact",
            "3": "Mountain Pine Beetle - Severe Impact",
            "2": "Mountain Pine Beetle - Moderate Impact",
            "1": "Mountain Pine Beetle - Low Impact"
        }

        for file_name in self.scan_for_layers(dist.getWorkspace(), dist.getFilter()):
            file_name_no_ext = os.path.basename(os.path.splitext(file_name)[0])
            year = int(file_name_no_ext[-4:])
            if year in range(self.historic_range[0], self.future_range[1]+1):
                self.layers.append(DisturbanceLayer(
                    self.rule_manager,
                    VectorLayer("insect_{}".format(year), file_name, Attribute("Severity", substitutions=mpb_shp_severity_to_dist_type_lookup)),
                    year=year,
                    disturbance_type=Attribute("Severity"),
                    transition=TransitionRule(
                        regen_delay=0,
                        age_after=-1)))
        pp.finish()

    def processProjectedDisturbances(self, scenario, params):
        if (self.future_range[1]-self.future_range[0])<0:
            return
        pp = self.ProgressPrinter.newProcess("{}_{}".format(inspect.stack()[0][3],scenario), 1).start()
        percent_sb = params[0]
        actv_percent_sb = params[1]
        actv_percent_harv = params[2]
        placeholder = ProjectedDisturbancesPlaceholder(self.inventory, self.rollback_disturbances,
            self.future_range, self.rollback_range, self.activity_start_year, self.ProgressPrinter)
        projectedDisturbances = placeholder.generateProjectedDisturbances(scenario, percent_sb, actv_percent_sb, actv_percent_harv)

        projected_dist_lookup = {
            7: "Wild Fires",
            6: "{} CC".format('Base' if scenario.lower()=='base' else 'CBM_{}'.format(scenario)),
            13: "SlashBurning"
        }
        projected_name_lookup = {
            7: "fire",
            6: "harvest",
            13:"slashburn"
        }
        for year in range(self.historic_range[1]+1, self.future_range[1]+1):
            for dist_code in projected_dist_lookup:
                label = projected_dist_lookup[dist_code]
                name = projected_name_lookup[dist_code]
                self.layers.append(DisturbanceLayer(
                    self.rule_manager,
                    VectorLayer("projected_{}_{}".format(name, year),
                                projectedDisturbances,
                                [
                                    Attribute("DistYEAR_n", filter=lambda v, yr=year: v == yr),
                                    Attribute("DistType", filter=lambda v, dt=dist_code: v == dt, substitutions=projected_dist_lookup),
                                    Attribute("RegenDelay")
                                ]),
                    year=year,
                    disturbance_type=Attribute("DistType"),
                    transition=TransitionRule(
                        regen_delay=Attribute("RegenDelay"),
                        age_after=0)))
        pp.finish()

        # futureDistTypeLookup = dist.getLookupTable()
        # future_start_year = self.future_range[0]
        # for file_name in self.scan_for_layers(dist.getWorkspace(), dist.getFilter()):
        #     file_name_no_ext = os.path.basename(os.path.splitext(file_name)[0])
        #     year = future_start_year + int(file_name_no_ext.split("_")[-1])
        #     if year in range(self.historic_range[1]+1, self.future_range[1]+1):
        #         self.layers.append(DisturbanceLayer(
        #             self.rule_manager,
        #             VectorLayer("Proj{}_{}".format("Disturbance", year), file_name, Attribute("dist_type_", substitutions=futureDistTypeLookup)),
        #             year=year,
        #             disturbance_type=Attribute("dist_type_"),
        #             transition=TransitionRule(
        #                 regen_delay=0,
        #                 age_after=0)))


    def runTiler(self, output_dir, scenario, make_transition_rules):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1).start()
        output_dir_scen = r'{}\SCEN_{}'.format(output_dir, scenario)
        if not os.path.exists(output_dir_scen):
            os.makedirs(output_dir_scen)
        else:
            shutil.rmtree(output_dir_scen)
            os.makedirs(output_dir_scen)
        cwd = os.getcwd()
        os.chdir(output_dir_scen)
        with cleanup():
            logging.info('Tiling layers: {}'.format([l.name for l in self.layers]))
            self.tiler.tile(self.layers)
            self.rule_manager.write_rules()
            transitionRules = None
            if make_transition_rules == True:
                ccol = {}
                for classifier in self.inventory.getClassifiers():
                    ccol.update({classifier:None})
                transitionRules = TransitionRules(path=r"{}\transition_rules.csv".format(output_dir_scen),
                    classifier_cols=ccol, header=True, cols={"NameCol":0, "AgeCol":2, "DelayCol":1})
        os.chdir(cwd)
        self.layers = []
        pp.finish()
        return transitionRules


# --------------------------------------------------------------------------------------------------------------------------------------------------------------
## Old Script

'''
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
'''

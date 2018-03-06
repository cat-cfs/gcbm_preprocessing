import glob
import os
import inspect
import logging
import shutil

from projected_disturbances_placeholder import ProjectedDisturbancesPlaceholder
from generate_historic_slashburn import GenerateSlashburn

from mojadata.boundingbox import BoundingBox
from mojadata.compressingtiler2d import CompressingTiler2D
from mojadata.layer.vectorlayer import VectorLayer
from mojadata.layer.rasterlayer import RasterLayer
from mojadata.layer.gcbm.disturbancelayer import DisturbanceLayer
from mojadata.cleanup import cleanup
from mojadata.layer.attribute import Attribute
from mojadata.layer.filter.valuefilter import ValueFilter
from mojadata.layer.filter.slicevaluefilter import SliceValueFilter
from mojadata.layer.gcbm.transitionrule import TransitionRule
from mojadata.layer.gcbm.transitionrulemanager import SharedTransitionRuleManager
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
        self.mgr = SharedTransitionRuleManager()
        self.mgr.start()
        self.rule_manager = self.mgr.TransitionRuleManager("transition_rules.csv")
        self.layers = []
        self.tiler = None

    def scan_for_layers(self, path, filter):
        return sorted(glob.glob(os.path.join(path, filter)),
                      key=os.path.basename)

    def defineBoundingBox(self, output_dir):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1).start()
        bbox_path = self.inventory.getRasters()[0].getPath()
        logging.info("Defining bounding box with inventory layer {}".format(os.path.basename(bbox_path)))
        logging.info("Bounding box will be stored in {}".format(os.path.join(
            output_dir, os.path.basename(bbox_path.split('.')[0]))))
            
        cwd = os.getcwd()
        os.chdir(output_dir)
        self.bbox = BoundingBox(RasterLayer(bbox_path), pixel_size=self.resolution)
        self.tiler = CompressingTiler2D(self.bbox, use_bounding_box_resolution=True)
        os.chdir(cwd)
        pp.finish()

    def processGeneralLayers(self):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1).start()
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
            self.layers.append(VectorLayer(
                attr,
                self.spatial_boundaries.getPathRI(),
                Attribute(attr_field)))
            
            general_lyrs.append(attr)

        self.layers.append(RasterLayer(self.NAmat.getPath(), nodata_value=1.0e38))
        general_lyrs.append(os.path.basename(self.NAmat.getPath()).split('.')[0])
        pp.finish()

        return general_lyrs

    def processRollbackDisturbances(self, dist_lookup, name_lookup):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1).start()

        for year in range(self.rollback_range[0], self.rollback_range[1] + 1):
            for dist_code in dist_lookup:
                label = dist_lookup[dist_code]
                name = name_lookup[dist_code]
                self.layers.append(DisturbanceLayer(
                    self.rule_manager,
                    VectorLayer("rollback_{}_{}".format(name, year),
                                self.rollback_disturbances.getPath(),
                                [
                                    Attribute("DistYEAR_n", filter=ValueFilter(year)),
                                    Attribute("DistType", filter=ValueFilter(dist_code), substitutions=dist_lookup),
                                    Attribute("RegenDelay")
                                ]),
                    year=year,
                    disturbance_type=Attribute("DistType"),
                    transition=TransitionRule(
                        regen_delay=Attribute("RegenDelay"),
                        age_after=0)))
        pp.finish()

    def processHistoricFireDisturbances(self, dist, dt):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1).start()

        _, rollback_end_year = self.rollback_range
        _, historic_end_year = self.historic_range
        workspace = self.inventory.getWorkspace()
        for year in range(rollback_end_year + 1, historic_end_year + 1):
            self.layers.append(DisturbanceLayer(
                self.rule_manager,
                # The [:4] is specifically to deal with the case of NBAC where the year is followed by the date and time
                VectorLayer("fire_{}".format(year),
                            workspace,
                            Attribute(dist.getYearField(), filter=SliceValueFilter(year, slice_len=4)),
                            layer='MergedDisturbances'),
                year=year,
                disturbance_type=dt,
                transition=TransitionRule(
                    regen_delay=0,
                    age_after=0)))
        pp.finish()

    def processHistoricHarvestDisturbances(self, dist, sb_percent, cc_dt, sb_dt):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1).start()
        harvest_poly_shp = self.scan_for_layers(dist.getWorkspace(), dist.getFilter())[0]
        _, rollback_end_year = self.rollback_range
        _, historic_end_year = self.historic_range
        year_range = range(rollback_end_year + 1, historic_end_year + 1)
        workspace = self.inventory.getWorkspace()
        if year_range:
            sb = GenerateSlashburn(self.ProgressPrinter)
            sb_shp = sb.generateSlashburn(self.inventory, harvest_poly_shp, dist.getYearField(), year_range, sb_percent)

        for year in year_range:
            self.layers.append(DisturbanceLayer(
                self.rule_manager,
                VectorLayer("harvest_{}".format(year),
                            workspace,
                            Attribute(dist.getYearField(), filter=ValueFilter(year, True)),
                            layer='MergedDisturbances'),
                year=year,
                disturbance_type=cc_dt,
                transition=TransitionRule(
                    regen_delay=0,
                    age_after=0)))
                    
            self.layers.append(DisturbanceLayer(
                self.rule_manager,
                VectorLayer("slashburn_{}".format(year),
                            sb_shp,
                            Attribute(dist.getYearField(), filter=ValueFilter(year, True))),
                year=year,
                disturbance_type=sb_dt,
                transition=TransitionRule(
                    regen_delay=0,
                    age_after=0)))
        pp.finish()

    def processHistoricInsectDisturbances(self, dist, attr, dist_type_lookup):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1).start()

        historic_start_year, _ = self.historic_range
        _, future_end_year     = self.future_range
        year_range = range(historic_start_year, future_end_year + 1)
        
        for file_name in self.scan_for_layers(dist.getWorkspace(), dist.getFilter()):
            file_name_no_ext = os.path.basename(os.path.splitext(file_name)[0])
            year = int(file_name_no_ext[-4:])
            if year in year_range:
                self.layers.append(DisturbanceLayer(
                    self.rule_manager,
                    VectorLayer("insect_{}".format(year), file_name, Attribute(attr, substitutions=dist_type_lookup)),
                    year=year,
                    disturbance_type=Attribute(attr),
                    transition=TransitionRule(
                        regen_delay=0,
                        age_after=-1)))
        pp.finish()

    def processGenericHistoricDisturbances(self, dist, dist_type_attr, year_attr, dist_type_lookup):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1).start()

        historic_start_year, _ = self.historic_range
        _, future_end_year     = self.future_range
        year_range = range(historic_start_year, future_end_year + 1)
        
        for file_name in self.scan_for_layers(dist.getWorkspace(), dist.getFilter()):
            for year in year_range:
                self.layers.append(DisturbanceLayer(
                    self.rule_manager,
                    VectorLayer("insect_{}".format(year), file_name, Attribute(dist_type_attr, substitutions=dist_type_lookup)),
                    year=Attribute(year_attr, filter=ValueFilter(year, True)),
                    disturbance_type=Attribute(dist_type_attr)))
        pp.finish()

    def processProjectedDisturbancesRasters(self, scenario, base_raster_dir, scenario_raster_dir, params):

        #not at the top so we dont break existing things for everyone (gdal will be imported)
        from future_raster_processor import FutureRasterProcessor
        from random_raster_subset import RandomRasterSubset
        """
        append existing raster disturbance layers to the tiler instance
        @param scenario str name of the scenario
        @raster_dir directory containing future disturbance rasters 
                    ex "<tsaname>\01a_pretiled_layers\03_disturbances\02_future"
                    specified directory contains scenario names:
                    ex. "<tsaname>\01a_pretiled_layers\03_disturbances\02_future\base"
        """

        pp = self.ProgressPrinter.newProcess("{}_{}".format(inspect.stack()[0][3], scenario), 1).start()
        
        projected_dist_lookup = {
            "fire":  "Wild Fires",
            "harvest":  "{} CC".format("Base" if scenario.lower() == "base" else "CBM_{}".format(scenario)),
            "slashburn": "SlashBurning"
        }
        
        projected_name_lookup = {
            7:  "fire",
            6:  "harvest",
            13: "slashburn"
        }

        percent_sb = params[0]
        actv_percent_sb = params[1]
        actv_percent_harv = params[2]

        f = FutureRasterProcessor(
            r"F:\GCBM\17_BC_ON_1ha\05_working_BC\TSA_2_Boundary\01a_pretiled_layers\03_disturbances\02_future\inputs\base",
            list(range(self.historic_range[1]+1, self.future_range[1]+1)),
            r"F:\GCBM\17_BC_ON_1ha\05_working_BC\TSA_2_Boundary\01a_pretiled_layers\03_disturbances\02_future\outputs\base",
            "fire", "harvest", "slashburn", "projected_fire_{}.tif", "projected_harvest_{}.tif", "projected_slashburn_{}.tif")

        result = []
        result.extend(f.processFire())
        result.extend(f.processHarvest(self.activity_start_year, actv_percent_harv, RandomRasterSubset()))
        result.extend(f.processSlashburn(percent_sb, self.activity_start_year, actv_percent_sb, RandomRasterSubset()))

        for item in result:
            self.layers.append(DisturbanceLayer(
                    self.rule_manager,
                    RasterLayer(item["Path"],
                                attributes="event",
                                attribute_table={1: [1]}),
                    year=item["Year"],
                    disturbance_type=projected_dist_lookup[item["DisturbanceName"]]))


        pp.finish()

    def processProjectedDisturbances(self, scenario, params):
        future_start_year, future_end_year = self.future_range
        if future_start_year > future_end_year:
            return
            
        pp = self.ProgressPrinter.newProcess("{}_{}".format(inspect.stack()[0][3], scenario), 1).start()
        percent_sb = params[0]
        actv_percent_sb = params[1]
        actv_percent_harv = params[2]
        placeholder = ProjectedDisturbancesPlaceholder(self.inventory, self.rollback_disturbances,
            self.future_range, self.rollback_range, self.activity_start_year, self.ProgressPrinter)
        projectedDisturbances = placeholder.generateProjectedDisturbances(scenario, percent_sb, actv_percent_sb, actv_percent_harv)

        projected_dist_lookup = {
            7:  "Wild Fires",
            6:  "{} CC".format("Base" if scenario.lower() == "base" else "CBM_{}".format(scenario)),
            13: "SlashBurning"
        }
        
        projected_name_lookup = {
            7:  "fire",
            6:  "harvest",
            13: "slashburn"
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
                                    Attribute("DistYEAR_n", filter=ValueFilter(year)),
                                    Attribute("DistType", filter=ValueFilter(dist_code), substitutions=projected_dist_lookup),
                                    Attribute("RegenDelay")
                                ]),
                    year=year,
                    disturbance_type=Attribute("DistType"),
                    transition=TransitionRule(
                        regen_delay=Attribute("RegenDelay"),
                        age_after=0)))
        pp.finish()

    def runTiler(self, output_dir, scenario, make_transition_rules):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1).start()

        output_dir_scen = r"{}\SCEN_{}".format(output_dir, scenario)
        if os.path.exists(output_dir_scen):
            shutil.rmtree(output_dir_scen)
        
        logging.info("Tiler output directory: {}".format(output_dir_scen))
        os.makedirs(output_dir_scen)
            
        cwd = os.getcwd()
        os.chdir(output_dir_scen)
        with cleanup():
            logging.info("Tiling layers: {}".format([l.name for l in self.layers]))
            self.tiler.tile(self.layers)
            transitionRules = None
            if make_transition_rules:
                self.rule_manager.write_rules()
                ccol = {}
                for classifier in self.inventory.getClassifiers():
                    ccol.update({classifier: None})
                transitionRules = TransitionRules(path=r"transition_rules.csv".format(output_dir_scen),
                    classifier_cols=ccol, header=True, cols={"NameCol": 0, "AgeCol": 2, "DelayCol": 1})
        
        os.chdir(cwd)
        self.layers = []
        pp.finish()
        
        return transitionRules

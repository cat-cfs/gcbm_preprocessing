from futureprocessing.future_raster_processor import FutureRasterProcessor
from futureprocessing.random_raster_subset import RandomRasterSubset

from gcbm.tilerconfig import TilerConfig
from configuration.futureconfig import FutureConfig
from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig

import sys, shutil
from loghelper import *
import argparse, logging

class Future(object):
    def __init__(self, config, pathRegistry):
        self.config = config
        self.pathRegistry = pathRegistry

    def CreateTilerConfig(self, processedRasterResult, scenario, region_name):

        baseTilerConfigPath = self.pathRegistry.GetPath(
            "HistoricTilerConfigPath",
            region_path=region_name)

        tilerConfig = TilerConfig(baseTilerConfigPath)

        for item in processedRasterResult:
            disturbanceType = item["DisturbanceName"]
            cbm_type = scenario["CBM_Disturbance_Type_Map"][disturbanceType]

            layer = tilerConfig.CreateConfigItem(
                "DisturbanceLayer",
                lyr=tilerConfig.CreateConfigItem(
                    "RasterLayer",
                    path=tilerConfig.CreateRelativePath(
                        baseTilerConfigPath, item["Path"]),
                    attributes="event",
                    attribute_table={1: [1]}),
                year=item["Year"],
                disturbance_type=cbm_type)
            tilerConfig.AppendLayer("future_{}".format(disturbanceType), layer)

        outputTilerConfigPath = os.path.join(
            os.path.dirname(baseTilerConfigPath),
            "{}_tiler_config.yaml".format(scenario["Name"]))
        tilerConfig.save(outputTilerConfigPath)
        return outputTilerConfigPath

    def Process(self, region_name, scenario):

        logging.info("processing future scenario '{0}' for region '{1}'"
                     .format(scenario["Name"],region_name))

        baseRasterDir = self.pathRegistry.GetPath(
            "Future_Dist_Input_Dir", 
            region_path=region_name,
            sha_future_scenario=scenario["SHAScenarioNane"])
        
        future_range = list(range(self.config.GetStartYear(),
                       self.config.GetEndYear()))

        output_dir = self.pathRegistry.GetPath(
               "Future_Dist_Output_Dir",
                region_path=region_name,
                scenario_name=scenario["Name"])

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        f = FutureRasterProcessor(
            base_raster_dir=baseRasterDir,
            years = future_range,
            output_dir = output_dir,
            fire_name = "fire",
            harvest_name = "harvest",
            slashburn_name = "slashburn",
            fire_format = self.config.GetPathFormat("fire"),
            harvest_format = self.config.GetPathFormat("harvest"),
            slashburn_format = self.config.GetPathFormat("slashburn"))

        result = []

        result.extend(f.processFire())

        result.extend(f.processHarvest(
            scenario["Activity_Start_Year"],
            scenario["Harvest_Activity_Percent"],
            RandomRasterSubset()))

        result.extend(f.processSlashburn(
            scenario["Slashburn_Percent"],
            scenario["Activity_Start_Year"],
            scenario["Slashburn_Activity_Percent"],
            RandomRasterSubset()))

        return result

def main():
    create_script_log(sys.argv[0])
    parser = argparse.ArgumentParser(description="future processor sets up "+
                                     "the tiler with the future rasters, "+
                                     " and performs random subsetting for "+
                                     "scenarios")
    parser.add_argument("--pathRegistry", help="path to file registry data")
    parser.add_argument("--futureConfig", help="path to configuration")
    parser.add_argument("--subRegionConfig", help="path to sub region data")
    parser.add_argument("--subRegionNames", help="optional comma delimited "+
                        "string of sub region names (as defined in "+
                        "subRegionConfig) to process, if unspecified all "+
                        "regions will be processed")

    try:
        args = parser.parse_args()

        pathRegistry = PathRegistry(os.path.abspath(args.pathRegistry))
        subRegionConfig = SubRegionConfig(
            os.path.abspath(args.subRegionConfig),
            args.subRegionNames.split(",") if args.subRegionNames else None)
        futureConfig = FutureConfig(os.path.abspath(args.futureConfig))
        future = Future(futureConfig, pathRegistry)

        for region in subRegionConfig.GetRegions():
            for scenario in futureConfig.GetScenarios():
                result = future.Process(
                    region["PathName"],
                    scenario)

                tilerConfig = future.CreateTilerConfig(
                    result,
                    scenario,
                    region["PathName"])




    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all future tasks finished")

if __name__ == "__main__":
    main()


from future.future_raster_processor import FutureRasterProcessor
from future.random_raster_subset import RandomRasterSubset

from configuration.tilerconfig import TilerConfig
from configuration.futureconfig import FutureConfig
from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig

import sys
from loghelper import *
import argparse, logging

class Future(object):
    def __init__(self, config):
        self.config = config

    def Process(self, region_name, scenario):
        baseTilerConfigPath = self.config.GetHistoricTilerConfigPath(
            region_name)
        tilerConfig = TilerConfig(baseTilerConfig)

        logging.info("processing future scenario '{0}' for region '{1}'"
                     .format(scenario_name,region_name))
        f = FutureRasterProcessor(
            self.config.GetBaseRasterDir(region_name),
            list(range(self.config.GetStartYear(),
                       self.config.GetEndYear())),
            self.config.GetRasterOutputDir(region_name),
            "fire", "harvest", "slashburn",
            self.config.GetPathFormat("fire"),
            self.config.GetPathFormat("harvest"),
            self.config.GetPathFormat("slashburn"))

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

        for item in result:
            cbm_type = config.GetCBMDisturbanceType(
                item["DisturbanceName"])

            tilerConfig.CreateConfigItem(
                "DisturbanceLayer",
                lyr=tilerConfig.CreateConfigItem(
                    "RasterLayer",
                    path=tilerConfig.CreateRelativePath(baseTilerConfigPath, item["Path"]),
                    attributes="event",
                    attribute_table={1: [1]}),
                year=item["Year"],
                disturbance_type=cbm_type)

        outputTilerConfigPath = os.path.join(
            os.path.dirname(baseTilerConfigPath),
            "{}_tiler_config.json".format(scenario_name))
        tilerConfig.writeJson(outputTilerConfigPath)

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
        subRegionNames = args.subRegionNames.split(",") \
            if args.subRegionNames else None

        pathRegistry = PathRegistry(args.pathRegistry)
        subRegionConfig = SubRegionConfig(args.subRegionConfig)
        futureConfig = FutureConfig(args.futureConfig, pathRegistry)
        future = Future(futureConfig)

        regionsToProcess = subRegionConfig.GetRegions() if subRegionNames is None \
            else [subRegionConfig.GetRegion(x) for x in subRegionNames]

        for region in regionsToProcess:
            for scenario in self.config.GetScenarios():
                future.Process(region["Name"], scenario)

    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all future tasks finished")

if __name__ == "__main__":
    main()


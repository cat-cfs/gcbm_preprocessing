from future.future_raster_processor import FutureRasterProcessor
from future.random_raster_subset import RandomRasterSubset
from configuration.tilerconfig import TilerConfig

from loghelper import *
import argparse, logging

class Future(object):
    def __init__(self, config):
        self.config = config

    def Process(self, region_name, scenario_name):
        baseTilerConfigPath = self.config.GetHistoricTilerConfigPath(region_name)
        tilerConfig = TilerConfig(baseTilerConfig)

        scenario = self.config.GetScenario(scenario_name)
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
                    attributes="event",
                    attribute_table={1: [1]}),
                year=item["Year"],
                disturbance_type=cbm_type)

        outputTilerConfigPath = os.path.join(
            os.path.dirname(baseTilerConfigPath),
            "{}_tiler_config.json".format(scenario_name))
        tilerConfig.writeJson(outputTilerConfigPath)

def main():

    pass


if __name__ == "__main__":
    main()



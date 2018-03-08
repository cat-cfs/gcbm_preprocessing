from future.future_raster_processor import FutureRasterProcessor
from future.random_raster_subset import RandomRasterSubset

from loghelper import *
import argparse, logging

class Future(object):
    def __init__(self, config):
        self.config = config

    def Process(self, region_name, scenario_name):
        scenario = self.config.GetScenario(scenario_name)
        logging.info("processing future scenario '{0}' for region '{1}'"
                     .format(scenario_name,region_name))
        f = FutureRasterProcessor(
            base_raster_dir,
            list(range(self.config.GetStartYear(),
                       self.config.GetEndYear())),
            scenario_raster_dir,
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
            self.layers.append(DisturbanceLayer(
                    self.rule_manager,
                    RasterLayer(item["Path"],
                                attributes="event",
                                attribute_table={1: [1]}),
                    year=item["Year"],
                    disturbance_type=projected_dist_lookup[item["DisturbanceName"]]))


def main():

    pass


if __name__ == "__main__":
    main()



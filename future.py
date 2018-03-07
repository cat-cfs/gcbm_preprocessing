from future.future_raster_processor import FutureRasterProcessor
from future.random_raster_subset import RandomRasterSubset

from loghelper import *
import argparse

class Future(object):
    def __init__(self):
        pass

    def Process(self, input_dir, output_dir, startYear, endYear):
        f = FutureRasterProcessor(
            base_raster_dir,
            list(range(startYear, endYear)),
            scenario_raster_dir,
            "fire", "harvest", "slashburn",
            "projected_fire_{}.tif",
            "projected_harvest_{}.tif",
            "projected_slashburn_{}.tif")

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


def main():

    pass


if __name__ == "__main__":
    main()



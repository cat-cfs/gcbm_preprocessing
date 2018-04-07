import argparse
import os
import sys
import logging

from loghelper import create_script_log
from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig
from configuration.preprocessorconfig import PreprocessorConfig

from rollback import merge_disturbances
from rollback import update_inventory
from rollback.rollback_tiler_config import RollbackTilerConfig


def main():

    create_script_log(sys.argv[0])
    try:
        parser = argparse.ArgumentParser(description="rollback")
        parser.add_argument("--pathRegistry", help="path to file registry data")
        parser.add_argument(
            "--preprocessorConfig",
            help="path to preprocessor configuration")
        parser.add_argument("--subRegionConfig", help="path to sub region data")
        parser.add_argument(
            "--subRegionNames",
            help=("optional comma delimited string of sub region names (as defined in "
                  "subRegionConfig) to process, if unspecified all regions will be "
                  "processed"))

        args = parser.parse_args()
        subRegionConfig = SubRegionConfig(os.path.abspath(args.subRegionConfig))
        if args.subRegionNames:
            subRegionNames = args.subRegionNames.split(",")
            regions = [subRegionConfig.GetRegion(x) for x in subRegionNames]
        else:
            subRegionNames = None
            regions = subRegionConfig.GetRegions()

        pathRegistry = PathRegistry(os.path.abspath(args.pathRegistry))
        config = PreprocessorConfig(
            os.path.abspath(args.preprocessorConfig), pathRegistry)

        for r in regions:
            region_path = r["PathName"]
            logging.info(region_path)

            disturbances = config.GetRollbackInputLayers(region_path)
            merge_disturbances.merge_disturbances(disturbances)
            merge_disturbances.grid_disturbances(config)
            merge_disturbances.intersect_disturbances_inventory(config)

            update_inventory.rollback_age_disturbed(config)
            update_inventory.rollback_age_non_disturbed(config)
            update_inventory.generate_slashburn(config)

            """tilerPath = self.config.GetRollbackTilerConfigPath(region_path = region_path)
            rollbackDisturbancePath = self.config.GetRollbackDisturbancesOutputDir(region_path)
            tilerConfig = RollbackTilerConfig()
            dist_lookup = self.config.GetRollbackOutputDisturbanceTypes()

            tilerConfig.Generate(outPath=tilerPath,
                inventoryMeta = inventoryMeta,
                resolution = self.config.GetResolution(),
                rollback_disturbances_path=rollbackDisturbancePath,
                rollback_range=[
                    self.config.GetRollbackRange()["StartYear"],
                    self.config.GetRollbackRange()["EndYear"]],
                dist_lookup=dist_lookup)
            """

    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all rollup tasks finished")


if __name__ == "__main__":
    main()

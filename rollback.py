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
from preprocess_tools import postgis_manage

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
        subRegionConfig = SubRegionConfig(os.path.abspath(args.subRegionConfig),
                                           args.subRegionNames.split(","))

        pathRegistry = PathRegistry(os.path.abspath(args.pathRegistry))

        config = PreprocessorConfig(args.preprocessorConfig, pathRegistry)

        for r in subRegionConfig.GetRegions():
            region_path = r["PathName"]
            logging.info(region_path)
            region_postgis_var_path = pathRegistry.GetPath(
                "PostGIS_Region_Connection_Vars",
                region_path=region_path)
            db_url = postgis_manage.get_url(region_postgis_var_path)
            gdal_con = postgis_manage.get_gdal_conn_string(region_postgis_var_path)
            disturbances = config.GetRollbackInputLayers(region_path)
            merge_disturbances.merge_disturbances(db_url, gdal_con, disturbances)
            merge_disturbances.grid_disturbances(db_url, config)
            merge_disturbances.intersect_disturbances_inventory(db_url, config)
            update_inventory.rollback_age_disturbed(db_url, config)
            update_inventory.rollback_age_non_disturbed(db_url, config)
            update_inventory.generate_slashburn(db_url, config)
            update_inventory.export_rollback_disturbances(gdal_con, config, region_path)
            raster_metadata = update_inventory.export_inventory(db_url, gdal_con, config, region_path)


            # run tiler on disturbances
            tiler_path = config.GetRollbackTilerConfigPath(region_path=region_path)
            rollback_disturbances_path = config.GetRollbackDisturbancesOutputDir(
                region_path
            )
            tilerConfig = RollbackTilerConfig()
            dist_lookup = config.GetRollbackOutputDisturbanceTypes()

            tilerConfig.Generate(
                outPath=tiler_path,
                inventoryMeta=raster_metadata,
                resolution=config.GetResolution(),
                rollback_disturbances_path=rollback_disturbances_path,
                rollback_range=[
                    config.GetRollbackRange()["StartYear"],
                    config.GetRollbackRange()["EndYear"]],
                dist_lookup=dist_lookup,
                classifiers = config.GetInventoryClassifiers())


    except Exception:
        logging.exception("error")
        sys.exit(1)

    logging.info("all rollback tasks finished")


if __name__ == "__main__":
    main()

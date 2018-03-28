from configuration.update_gcbm_config import * 

from configuration.pathregistry import PathRegistry
from configuration.futureconfig import FutureConfig
from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig
import os, argparse
from loghelper import *
def main():

    create_script_log(sys.argv[0])
    try:
        parser = argparse.ArgumentParser(description="prepares gcbm configuration files")
        parser.add_argument("--pathRegistry", help="path to file registry data")
        parser.add_argument("--futureConfig", help="path to configuration")
        parser.add_argument("--subRegionConfig", help="path to sub region data")
        parser.add_argument("--subRegionNames", help="optional comma delimited "+
                            "string of sub region names (as defined in "+
                            "subRegionConfig) to process, if unspecified all "+
                            "regions will be processed")
        args = parser.parse_args()

        pathRegistry = PathRegistry(os.path.abspath(args.pathRegistry))
        subRegionConfig = SubRegionConfig(os.path.abspath(args.subRegionConfig))
        futureConfig = FutureConfig(os.path.abspath(args.futureConfig), pathRegistry)

        subRegionNames = args.subRegionNames.split(",") \
            if args.subRegionNames else None
        regionsToProcess = subRegionConfig.GetRegions() if subRegionNames is None \
            else [subRegionConfig.GetRegion(x) for x in subRegionNames]
        for region in regionsToProcess:
            for scenario in futureConfig.GetScenarios():
                tiledLayersDir = pathRegistry.GetPath("TiledLayersDir", 
                                     region_path=region["PathName"],
                                     scenario_name=scenario["Name"])
                study_area = get_study_area(tiledLayersDir)
                update_gcbm_config(args.gcbm_config_template, study_area)
                update_provider_config(args.provider_config_template, study_area, tiledLayersDir)
    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all recliner2GCBM tasks finished")

if __name__ == "__main__":
    main()

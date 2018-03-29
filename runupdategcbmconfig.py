from configuration.update_gcbm_config import * 

from configuration.pathregistry import PathRegistry
from configuration.futureconfig import FutureConfig
from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig
import os, argparse, shutil
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

                gcbm_provider_template = pathRegistry.GetPath("GCBM_config_provider_template")
                gcbm_config_template = pathRegistry.GetPath("GCBM_config_template")
                outputDir = pathRegistry.GetPath("GCBM_Run_Dir",
                                                 region_path=region["PathName"],
                                                 scenario_name=scenario["Name"])
                gcbm_input_db_path= pathRegistry.GetPath("Recliner2GCBMOutpath",
                                                 region_path=region["PathName"],
                                                 scenario_name=scenario["Name"])
                if not os.path.exists(outputDir):
                    os.makedirs(outputDir)

                gcbm_config = os.path.join(outputDir, "GCBM_config.json")
                gcbm_provider = os.path.join(outputDir, "GCBM_config_provider.json")
                shutil.copy(gcbm_config_template, gcbm_config)
                shutil.copy(gcbm_provider_template, gcbm_provider)

                gcbm_output_db_path = pathRegistry.GetPath(
                    "GCBM_OutputDB_Path",
                    region_path=region["PathName"],
                    scenario_name=scenario["Name"])

                gcbm_output_variable_grid_dir = pathRegistry.GetPath(
                    "GCBM_Variable_Grid_Output_Dir",
                    region_path=region["PathName"],
                    scenario_name=scenario["Name"])

                study_area = get_study_area(tiledLayersDir)

                update_gcbm_config(gcbm_config, study_area,
                                   start_year = futureConfig.GetStartYear(),
                                   end_year = futureConfig.GetEndYear(),
                                   output_db_path = gcbm_output_db_path,
                                   variable_grid_output_dir = gcbm_output_variable_grid_dir)

                update_provider_config(gcbm_provider, study_area,
                                       tiledLayersDir, gcbm_input_db_path)

    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all update gcbm config tasks finished")

if __name__ == "__main__":
    main()

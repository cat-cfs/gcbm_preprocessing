from configuration.pathregistry import PathRegistry
from configuration.futureconfig import FutureConfig
from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig
import os, argparse, sys, subprocess
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
        subRegionConfig = SubRegionConfig(
            os.path.abspath(args.subRegionConfig),
            args.subRegionNames.split(",") if args.subRegionNames else None)
        futureConfig = FutureConfig(os.path.abspath(args.futureConfig), pathRegistry)

        for region in subRegionConfig.GetRegions():
            for scenario in futureConfig.GetScenarios():
                logging.info("run gcbm: {0},{1}".format(region["Name"], scenario["Name"]))
                gcbm_config_dir = pathRegistry.GetPath("GCBM_Run_Dir",
                                             region_path=region["PathName"],
                                             scenario_name=scenario["Name"])

                gcbm_config = os.path.join(gcbm_config_dir, "GCBM_config.json")
                gcbm_provider = os.path.join(gcbm_config_dir, "GCBM_config_provider.json")
                gcbm_cli_path = pathRegistry.GetPath("GCBM_EXE")
                
                gcbm_command = [gcbm_cli_path, "--config", gcbm_config, "--config_provider", gcbm_provider]
                logging.info("issuing command: {0}".format(gcbm_command))
                cmnd_output = subprocess.check_output(gcbm_command, 
                                                    stderr=subprocess.STDOUT,
                                                    shell=False, 
                                                    universal_newlines=True);
                logging.info("command executed successfully")

    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all rungcbm tasks finished")

if __name__ == "__main__":
    main()


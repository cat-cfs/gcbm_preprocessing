from configuration.pathregistry import PathRegistry
from configuration.futureconfig import FutureConfig
from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig
import os, argparse, sys, subprocess, shutil, multiprocessing
from loghelper import *

def gcbm_worker(task):
    os.chdir(os.path.dirname(task["gcbm_config"]))
    gcbm_command = [task["gcbm_cli_path"], 
                    "--config", task["gcbm_config"],
                    "--config_provider", task["gcbm_provider"]]


    logging.info("issuing command: {0}".format(gcbm_command))
    with open(os.devnull, 'wb') as devnull:
        cmnd_output = subprocess.check_output(
            gcbm_command, stderr=subprocess.STDOUT)

    logging.info("command executed successfully")

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
        futureConfig = FutureConfig(os.path.abspath(args.futureConfig))

        tasks = []
        for region in subRegionConfig.GetRegions():
            for scenario in futureConfig.GetScenarios():
                logging.info("run gcbm: {0},{1}".format(region["Name"], scenario["Name"]))
                gcbm_config_dir = pathRegistry.GetPath("GCBM_Config_Dir",
                                             region_path=region["PathName"],
                                             scenario_name=scenario["Name"])
                shutil.copy(pathRegistry.GetPath("GCBM_Logging_Conf"), gcbm_config_dir)
                tasks.append({
                    "gcbm_config": os.path.join(gcbm_config_dir, "GCBM_config.json"),
                    "gcbm_provider": os.path.join(gcbm_config_dir, "GCBM_config_provider.json"),
                    "gcbm_cli_path": pathRegistry.GetPath("GCBM_EXE")
                })
        try:
            p = multiprocessing.Pool(min(len(tasks), multiprocessing.cpu_count()))
            p.map(gcbm_worker, tasks)
        finally:
            p.close()
            p.join()


    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all rungcbm tasks finished")

if __name__ == "__main__":
    main()


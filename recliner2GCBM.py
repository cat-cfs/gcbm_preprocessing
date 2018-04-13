from configuration.futureconfig import FutureConfig
from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig
from configuration.recliner2GCBMConfig import Recliner2GCBMConfig
import os, argparse, subprocess, sys
from loghelper import *
class Recliner2GCBM(object):
    def __init__(self, exe_paths, configTemplatePath, outputPath,
                 archiveIndexPath, growthCurvePath, transitionRulesPath):
        self.exe_paths = exe_paths
        
        config = Recliner2GCBMConfig(configTemplatePath)
        config.setOutputPath(outputPath)
        config.setArchiveIndexPath(archiveIndexPath)
        config.setGrowthCurvePath(growthCurvePath)
        config.setTransitionRulesPath(transitionRulesPath)
        outputDir = os.path.dirname(outputPath)
        self.config_path = os.path.join(outputDir, "recliner2GCBMConfig.json")
        if not os.path.exists(outputDir):
            os.makedirs(outputDir)

        config.save(self.config_path)

    def run(self):
        for exe_path in self.exe_paths:
            command = [exe_path, "-c", self.config_path]
            try:
                subprocess.check_call(command)
                logging.info("Found and ran '{}'".format(" ".join(command)))
                break
            except Exception as e:
                logging.error("Failed to run '{}': {}".format(" ".join(command), e))
def main():

    create_script_log(sys.argv[0])
    try:
        parser = argparse.ArgumentParser(description="prepare gcbm input database")
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

        exe_paths = [
            os.path.join(pathRegistry.GetPath("Local_Recliner2GCBM-x64_Dir"),"Recliner2GCBM.exe"),
            os.path.join(pathRegistry.GetPath("Local_Recliner2GCBM-x86_Dir"),"Recliner2GCBM.exe")
        ]

        subRegionNames = args.subRegionNames.split(",") \
            if args.subRegionNames else None
        regionsToProcess = subRegionConfig.GetRegions() if subRegionNames is None \
            else [subRegionConfig.GetRegion(x) for x in subRegionNames]

        for region in regionsToProcess:
            for scenario in futureConfig.GetScenarios():

                outputPath = pathRegistry.GetPath("Recliner2GCBMOutpath",
                                                    region_path=region["PathName"],
                                                    scenario_name=scenario["Name"])
                configTemplatePath = pathRegistry.GetPath("Recliner2GCBMConfigTemplate")
                archiveIndexPath = pathRegistry.GetPath("ArchiveIndex")
                yeildTablePath = pathRegistry.GetPath("YieldTable")
                transitionRulesPath = pathRegistry.GetPath("TransitionRulesPath",
                                                           region_path=region["PathName"],
                                                           scenario_name=scenario["Name"])
                r = Recliner2GCBM(exe_paths, configTemplatePath, outputPath,
                                  archiveIndexPath, yeildTablePath,
                                  transitionRulesPath)
                r.run()

    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all recliner2GCBM tasks finished")

if __name__ == "__main__":
    main()
import os, logging, subprocess
from recliner2GCBMConfig import Recliner2GCBMConfig

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
            subprocess.check_call(command)
            logging.info("Found and ran '{}'".format(" ".join(command)))
            break


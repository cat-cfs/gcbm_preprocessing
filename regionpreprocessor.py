from loghelper import *
from create_grid import Fishnet
from grid_inventory import GridInventory

from merge_disturbances import MergeDisturbances

from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig
from configuration.regionpreprocessorconfig import RegionPreprocessorConfig

import os, sys, argparse

class RegionPreprocessor(object):

    def __init__(self, regionPreprocessorConfig, subRegionConfig):
        self.workspace = workspace
        self.workspace_filter = workspace_filter

    def runFishnet(self):
        fishnet = Fishnet(resolution)
        fishnet.createFishnet(self.workspace, self.workspace_filter)

    def runGridInventory(self):
        grid = GridInventory(area_majority_rule)
        grid.gridInventory(self.workspace, self.workspace_filter, ageFieldName)

    def runMergeDisturbances(self, disturbances):
        m = MergeDisturbances()
        m.runMergeDisturbances(self.workspace, disturbances)


def main():

    start_logging("{0}.log".format(os.path.splitext(sys.argv[0])[0]))
    parser = argparse.ArgumentParser(description="region preprocessor")
    parser.add_argument("--fileRegistryPath", help="path to file registry data")
    parser.add_argument("--regionProcessorPath", help="path to region processor configuration")
    parser.add_argument("--subRegionPath", help="path to sub region data")
    parser.add_argument("--subRegionNames", help="optional comma delimited "+
                        "string of sub region names (as defined in "+
                        "subRegionConfig) to process, if unspecified all "+
                        "regions will be processed")
    args = parser.parse_args()

    pathRegistry = PathRegistry(args.fileRegistryPath)
    regionPreprocessorConfig = RegionPreprocessorConfig(args.regionProcessorPath)
    subRegionConfig = SubRegionConfig(args.subRegionNames)

    p = RegionPreprocessor(regionPreprocessorConfig, subRegionConfig)

    p.runFishnet()
    p.runGridInventory()

if __name__ == "__main__":
    main()

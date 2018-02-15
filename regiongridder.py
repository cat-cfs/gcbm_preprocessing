from loghelper import *
from create_grid import Fishnet
from grid_inventory import GridInventory

from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig
from configuration.regiongridderconfig import RegionGridderConfig

import os, sys, argparse

class RegionGridder(object):

    def __init__(self, config, pathRegistry, fishnet, gridInventory):
        self.config = config
        self.pathRegistry
        self.fishnet = fishnet
        self.gridInventory = gridInventory

    def ProcessSubRegion(self, region_path):
        workspace = self.config.GetInventoryWorkspace(
            self.pathRegistry, region_path)
        workspaceFilter = self.config.GetInventoryFilter()
        ageFieldName = self.config.GetInventoryAgeField()
        self.fishnet.createFishnet(workspace, workspaceFilter)
        self.gridInventory.gridInventory(workspace,
                                        workspace_filter,
                                        ageFieldName)

    def Process(self, subRegionConfig, subRegionNames=None):
        regions = subRegionConfig.GetRegions() if subRegionNames is None \
            else [subRegionConfig.GetRegion(x) for x in subRegionNames]

        for r in regions:
            self.ProcessSubRegion(region_path = r["PathName"])

def main():

    start_logging("{0}.log".format(os.path.splitext(sys.argv[0])[0]))
    parser = argparse.ArgumentParser(description="region preprocessor")
    parser.add_argument("--fileRegistryPath", help="path to file registry data")
    parser.add_argument("--regionGridderConfig", help="path to region gridder configuration")
    parser.add_argument("--subRegionConfig", help="path to sub region data")
    parser.add_argument("--subRegionNames", help="optional comma delimited "+
                        "string of sub region names (as defined in "+
                        "subRegionConfig) to process, if unspecified all "+
                        "regions will be processed")
    args = parser.parse_args()

    regionGridderConfig = RegionGridderConfig(args.regionGridderConfig)
    pathRegistry = PathRegistry(args.fileRegistryPath)
    subRegionConfig = SubRegionConfig(args.subRegionNames)
    fishnet = Fishnet(regionGridderConfig.GetResolution())
    gridInventory = GridInventory(regionGridderConfig.GetAreaMajorityRule())

    p = RegionGridder(
        config = regionGridderConfig,
        pathRegistry = pathRegistry,
        fishnet = fishnet,
        gridInventory = gridInventory)

if __name__ == "__main__":
    main()

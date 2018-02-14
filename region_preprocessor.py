from common import *
from create_grid import Fishnet
from grid_inventory import GridInventory
from pathregistry import PathRegistry
import os, sys, argparse

class RegionPreprocessor(object):

    def __init__(self, workspace, workspace_filter):
        self.workspace = workspace
        self.workspace_filter = workspace_filter

    def runFishnet(self, resolution):
        fishnet = Fishnet(resolution)
        fishnet.createFishnet(self.workspace, self.workspace_filter)

    def runGridInventory(self, ageFieldName, area_majority_rule=True):
        grid = GridInventory(area_majority_rule)
        grid.gridInventory(self.workspace, self.workspace_filter, ageFieldName)

def main():

    start_logging("{0}.log".format(os.path.splitext(sys.argv[0])[0]))
    parser = argparse.ArgumentParser(description="region preprocessor")
    parser.add_argument("--fileRegistryPath", help="path to file registry data")
    parser.add_argument("--resolution", help="tile resolution in degrees")
    args = parser.parse_args()

    pathRegistry = PathRegistry(loadJson(args.fileRegistryPath))
    workspace = pathRegistry.GetPath("Clipped_Inventory_Path", "TSA_2_Boundary")
    workspace_filter = "inventory"
    ageFieldName = "Age2015"
    area_majority_rule = True
    p = RegionPreprocessor(workspace,workspace_filter)

    resolution = float(args.resolution)
    p.runFishnet(resolution)
    p.runGridInventory(ageFieldName, area_majority_rule)

if __name__ == "__main__":
    main()

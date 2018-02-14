from loghelper import *
from gdb_functions import GDBFunctions
from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig
from configuration.regionclipperconfig import RegionClipperConfig
import os, sys, argparse, json

class RegionClipper(object):
    def __init__(self, gdbfunctions, path_registry):
        self.gdbfunc = gdbfunctions
        self.path_registry = path_registry

    def clip(self, workspace, workspace_filter, new_workspace,
             clip_feature, clip_feature_filter):
        self.gdbfunc.clip(workspace=workspace,
                          workspace_filter=workspace_filter,
                          clip_feature=clip_feature,
                          clip_feature_filter=clip_feature_filter,
                          new_workspace=new_workspace)

    def clipCutPolys(self, workspace, workspace_filter, new_workspace,
                     clip_feature, clip_feature_filter):
        self.gdbfunc.clipCutPolys(workspace=workspace,
                          workspace_filter=workspace_filter,
                          clip_feature=clip_feature,
                          clip_feature_filter=clip_feature_filter,
                          new_workspace=new_workspace)

    def copy(self, workspace, workspace_filter, new_workspace):
        self.gdbfunc.copy(workspace=workspace,
                          workspace_filter=workspace_filter,
                          new_workspace=new_workspace)

    def createConfiguration(self, configPath, regionPath):
        return RegionClipperConfig(configPath, self.path_registry, regionPath)

    def ProcessSubRegion(self, clipConfig, clipFeature, clipFeatureFilter):
        '''
        process the tasks specified in tasks for the specified subregion
        @param clipConfig RegionClipperConfig instance
        @param clipFeature path to feature for clipping operations
        @param clipFeatureFilter name of feature in clipFeature
        '''
        for t in clipConfig.GetTasks():
            if t.task == "clipCutPolys":
                self.clipCutPolys(
                    workspace=t.workspace,
                    workspace_filter=t.workspace_filter,
                    new_workspace= t.new_workspace,
                    clip_feature=clipFeature,
                    clip_feature_filter=clipFeatureFilter)
            elif t.task == "clip":
                self.clip(
                    workspace=t.workspace,
                    workspace_filter=t.workspace_filter,
                    new_workspace= t.new_workspace,
                    clip_feature=clipFeature,
                    clip_feature_filter=clipFeatureFilter)
            elif t.task =="copy":
                self.copy(
                    workspace=t.workspace,
                    workspace_filter=t.workspace_filter,
                    new_workspace= t.new_workspace)
            else:
                raise ValueError("specified task not supported '{}'"
                                 .format(t.task))

    def Process(self, regionClipperConfig, subRegionConfig, subRegionNames=None):
        '''
        runs the clip/copy/cut tasks specified in config, 
        optionally for the sub-regions specified
        @param regionClipperConfig path to region clipper configuration
        @param subRegionConfig SubRegionConfig instance
        @param subRegionNames if None all subRegions specified in subRegionConfig are
        processed, otherwise if a list of subregion names are specified that 
        set of subregions are processed
        '''

        regions = subRegionConfig.GetRegions() if subRegionNames is None \
            else [subRegionConfig.GetRegion(x) for x in subRegionNames]

        for r in regions:
            region_path = r["PathName"]
            clipFeature = self.path_registry.GetPath("Clip_Feature", region_path)
            clipFeatureFilter = r["ClipFeatureFilter"]
            clipConfig = self.createConfiguration(regionClipperConfig, region_path)
            self.ProcessSubRegion(clipConfig, clipFeature, clipFeatureFilter)

def main():

    start_logging("{0}.log".format(os.path.splitext(sys.argv[0])[0]))
    parser = argparse.ArgumentParser(description="region clipper. clips, and "+
                                     "copys spatial data: clips the "+ 
                                     "subregions defined in subRegionConfig "+
                                     "with each of the tasks defined in "+
                                     "subRegionNames")
    parser.add_argument("--pathRegistry", help="path to file registry data")
    parser.add_argument("--regionClipperConfig", help="path to clip tasks data")
    parser.add_argument("--subRegionConfig", help="path to sub region data")
    parser.add_argument("--subRegionNames", help="optional comma delimited "+
                        "string of sub region names (as defined in "+
                        "subRegionConfig) to process, if unspecified all "+
                        "regions will be processed")
    args = parser.parse_args()
    subRegionNames = None
    if args.subRegionNames:
        subRegionNames = args.subRegionNames.split(",")

    gdbFunctions = GDBFunctions()
    pathRegistry = PathRegistry(args.pathRegistry)
    subRegionConfig = SubRegionConfig(args.subRegionConfig)

    r = RegionClipper(gdbfunctions = gdbFunctions,
                      path_registry = pathRegistry)

    r.Process(regionClipperConfig = args.regionClipperConfig,
              subRegionConfig = subRegionConfig,
              subRegionNames = subRegionNames)


if __name__ == "__main__":
    main()

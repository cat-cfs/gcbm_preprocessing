from loghelper import *
from preprocess_tools.licensemanager import *

from clip.gdb_functions import GDBFunctions
from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig
from configuration.regionclipperconfig import RegionClipperConfig
import os, sys, argparse, json

class RegionClipper(object):
    def __init__(self, configPath, gdbfunctions, path_registry):
        self.configPath = configPath
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


    def ProcessSubRegion(self, sub_region, clipConfig, clipFeature, clipFeatureFilter):
        '''
        process the tasks specified in tasks for the specified subregion
        @param sub_region the sub region object
        @param clipConfig RegionClipperConfig instance
        @param clipFeature path to feature for clipping operations
        @param clipFeatureFilter name of feature in clipFeature
        '''

        for t in clipConfig.GetTasks(sub_region):
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

    def Process(self, subRegionConfig):
        '''
        runs the clip/copy/cut tasks specified in config, 
        optionally for the sub-regions specified
        @param subRegionConfig SubRegionConfig instance
        '''

        for r in subRegionConfig.GetRegions():
            clipFeature = self.path_registry.GetPath("Clip_Feature")
            clipFeatureFilter = r["ClipFeatureFilter"]
            clipConfig = RegionClipperConfig(
                self.configPath,
                self.path_registry)
            self.ProcessSubRegion(r,
                                 clipConfig, 
                                 clipFeature,
                                 clipFeatureFilter)

def main():

    create_script_log(sys.argv[0])
    try:
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

        with arc_license(Products.ARC) as arcpy:
            gdbFunctions = GDBFunctions(arcpy)
            pathRegistry = PathRegistry(os.path.abspath(args.pathRegistry))
            subRegionConfig = SubRegionConfig(
                os.path.abspath(args.subRegionConfig),
                args.subRegionNames.split(",") if args.subRegionNames else None)

            r = RegionClipper(configPath = args.regionClipperConfig,
                              gdbfunctions = gdbFunctions,
                              path_registry = pathRegistry)

            r.Process(subRegionConfig = subRegionConfig)
    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all clipping tasks finished")

if __name__ == "__main__":
    main()

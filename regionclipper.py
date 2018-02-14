from common import *
from gdb_functions import GDBFunctions
from pathregistry import PathRegistry
import os, sys, argparse

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

    def ProcessSubRegion(self, tasks, subRegionsData):
        '''
        process the tasks specified in tasks for the specified subregion
        @param tasks the dictionary of tasks to run on the subregion
        @param subRegionsData the dictionary of subregion settings
        '''
        getPath = lambda x: self.path_registry.GetPath(x, subRegionsData["PathName"])
        clipFeature = getPath(subRegionsData["ClipFeature"])
        clipFeatureFilter = subRegionsData["ClipFeatureFilter"]
        
        for t in tasks["ClipCutPolysTasks"]:
            self.clipCutPolys(workspace=getPath(t["workspace"]),
                              workspace_filter=t["workspace_filter"],
                              new_workspace= getPath(t["new_workspace"]),
                              clip_feature=clipFeature,
                              clip_feature_filter=clipFeatureFilter)

        for t in tasks["ClipTasks"]:
            self.clip(workspace=getPath(t["workspace"]),
                      workspace_filter=t["workspace_filter"],
                      new_workspace= getPath(t["new_workspace"]),
                      clip_feature=clipFeature,
                      clip_feature_filter=clipFeatureFilter)

        for t in tasks["CopyTasks"]:
            self.copy(workspace=getPath(t["workspace"]),
                      workspace_filter=t["workspace_filter"],
                      new_workspace= getPath(t["new_workspace"]))

    def Process(self, config, subRegionConfig, subRegionNames=None):
        '''
        runs the clip/copy/cut tasks specified in config, 
        optionally for the sub-regions specified
        @param config dictionary of tasks
        @param subRegionNames if None all subRegions specified in config are
        processed, otherwise if a list of subregion names are specified that 
        set of subregions are processed
        '''
        subRegionsByName = {}
        for r in subRegionConfig:
            subRegionName = r["Name"]
            if subRegionName in subRegionsByName:
                raise ValueError("duplicate subregion detected {0}"
                                 .format(subRegionName))
            subRegionsByName[subRegionName] = r
        if subRegionNames == None: #subregion filter unspecified, process all
            for s in subRegionConfig:
                self.ProcessSubRegion(config, s)
        else:
            for sname in subRegionNames:
                if sname in subRegionName:
                    raise ValueError("specified subregion name not found in "+
                                     "subregion data '{}'".format(sname))
                self.ProcessSubRegion(config, subRegionsByName[sname])

def clip(fileRegistryPath, clipTasksPath, subRegionPath, 
         subRegionNames=None):
    gdbFunctions = GDBFunctions()
    pathRegistry = PathRegistry(loadJson(fileRegistryPath))
    clipTasks = loadJson(clipTasksPath)
    subRegionConfig = loadJson(subRegionPath)

    r = RegionClipper(gdbfunctions = gdbFunctions,
                      path_registry = pathRegistry)

    r.Process(config=clipTasks, subRegionConfig=subRegionConfig,
             subRegionNames=subRegionNames)

def main():

    start_logging("{0}.log".format(os.path.splitext(sys.argv[0])[0]))
    parser = argparse.ArgumentParser(description="region clipper. clips, and "+
                                     "copys spatial data: clips the "+ 
                                     "subregions defined in subRegionConfig "+
                                     "with each of the tasks defined in "+
                                     "subRegionNames")
    parser.add_argument("--fileRegistryPath", help="path to file registry data")
    parser.add_argument("--clipTasksPath", help="path to clip tasks data")
    parser.add_argument("--subRegionPath", help="path to sub region data")
    parser.add_argument("--subRegionNames", help="optional comma delimited "+
                        "string of sub region names (as defined in "+
                        "subRegionConfig) to process, if unspecified all "+
                        "regions will be processed")
    args = parser.parse_args()
    subRegions = None
    if args.subRegionNames:
        subRegions = args.subRegionNames.split(",")
    clip(args.fileRegistryPath, args.clipTasksPath,
         args.subRegionPath, subRegions)


if __name__ == "__main__":
    main()

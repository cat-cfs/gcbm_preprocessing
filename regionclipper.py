from gdb_functions import GDBFunctions

class RegionClipper(object):
    def __init__(self, clip_feature, clip_feature_filter):
        self.gdbfunc = GDBFunctions()
        self.clip_feature = clip_feature
        self.clip_feature_filter = clip_feature_filter

    def clip(self, workspace, workspace_filter, new_workspace):
        self.gdbfunc.clip(workspace=workspace,
                          workspace_filter=workspace_filter,
                          clip_feature=self.clip_feature,
                          clip_feature_filter=self.clip_feature_filter,
                          new_workspace=new_workspace)

    def clipCutPolys(self, workspace, workspace_filter, new_workspace):
        self.gdbfunc.clip(workspace=workspace,
                          workspace_filter=workspace_filter,
                          clip_feature=self.clip_feature,
                          clip_feature_filter=self.clip_feature_filter,
                          new_workspace=new_workspace)

    def copy(self, workspace, workspace_filter, new_workspace):
        self.gdbfunc.copy(workspace=workspace,
                          workspace_filter=workspace_filter,
                          new_workspace=new_workspace)

    def Process(self, config):
        pass
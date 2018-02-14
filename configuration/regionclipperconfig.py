import json

class RegionClipperTask(object):
    def __init__(self, task, workspace, workspace_filter, new_workspace):
        self.task = task
        self.workspace = workspace
        self.workspace_filter = workspace_filter
        self.new_workspace = new_workspace

class RegionClipperConfig(object):
    def __init__(self, configPath, pathRegistry, regionPath):
        self.data = self.loadJson(configPath)
        self.pathRegistry = pathRegistry
        self.regionPath= regionPath

    def loadJson(self, path):
        with open(path) as json_data:
            return json.load(json_data)

    def _validate_task(self, task):
        if task not in ["clipCutPolys", "clip", "copy"]:
            raise ValueError("specified task not valid '{}'".format(task))
        return task

    def _unpack_path(self, path):
        if self.pathRegistry.is_dependent_token(path):
            return self.pathRegistry.GetPath(
               self.pathRegistry.strip_dependent_token(path),
               self.regionPath)
        else:
            return path

    def GetTasks(self):
        for t in self.data:
            yield RegionClipperTask(
                task = self._validate_task(t["task"]),
                workspace = self._unpack_path(t["workspace"]),
                workspace_filter = t["workspace_filter"],
                new_workspace = self._unpack_path(t["new_workspace"])
            )

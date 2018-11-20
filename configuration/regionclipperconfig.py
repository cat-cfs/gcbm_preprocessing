import json

class RegionClipperTask(object):
    def __init__(self, task, workspace, workspace_filter, new_workspace):
        self.task = task
        self.workspace = workspace
        self.workspace_filter = workspace_filter
        self.new_workspace = new_workspace

class RegionClipperConfig(object):
    def __init__(self, configPath, pathRegistry):
        self.data = self.loadJson(configPath)
        self.pathRegistry = pathRegistry

    def loadJson(self, path):
        with open(path) as json_data:
            return json.load(json_data)

    def _validate_task(self, task):
        if task not in ["clipCutPolys", "clip", "copy"]:
            raise ValueError("specified task not valid '{}'".format(task))
        return task

    def GetTasks(self, sub_region):
        region_path = sub_region["PathName"]
        for t in self.data:
            has_region_workspace_filter = self.pathRegistry.is_dependent_token(t["workspace_filter"])
            region_workspace_filter = None
            if has_region_workspace_filter:
                key = self.pathRegistry.strip_dependent_token(t["workspace_filter"])
                region_workspace_filter = sub_region[key]
            yield RegionClipperTask(
                task = self._validate_task(t["task"]),
                workspace = self.pathRegistry.UnpackPath(t["workspace"], region_path=region_path),
                workspace_filter = self.pathRegistry.UnpackPath(t["workspace_filter"], workspace_filter=region_workspace_filter),
                new_workspace = self.pathRegistry.UnpackPath(t["new_workspace"], region_path=region_path)
            )

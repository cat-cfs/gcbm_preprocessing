import json

class RegionGridderConfig(object):
    def __init__(self, configPath):
        self.data = self.loadJson(configPath)

    def loadJson(self, path):
        with open(path) as json_data:
            return json.load(json_data)

    def GetResolution(self):
        return self.data["Resolution"]

    def GetAreaMajorityRule(self):
        return self.data["Area_Majority_Rule"]

    def GetInventoryWorkspace(self, pathRegistry, region_path):
        return pathRegistry.UnpackPath(self.data["InventoryWorkspace"], region_path)

    def GetInventoryFilter(self):
        return self.data["InventoryFilter"]

    def GetInventoryAgeField(self):
        return self.data["InventoryAgeField"]


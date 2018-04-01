import json


class SubRegionConfig(object):
    def __init__(self, configPath):
        self.config = self.loadJson(configPath)
        self.subRegionsByName = {}
        self.subRegions = []
        self._initialize()

    def loadJson(self, path):
        with open(path) as json_data:
            return json.load(json_data)

    def _initialize(self):
        for r in self.config:
            self.subRegions.append(r)
            subRegionName = r["Name"]
            if subRegionName in self.subRegionsByName:
                raise ValueError("duplicate subregion detected {0}"
                                 .format(subRegionName))
            self.subRegionsByName[subRegionName] = r

    def GetRegion(self, regionName):
        return self.subRegionsByName[regionName]

    def GetRegions(self):
        return self.subRegions


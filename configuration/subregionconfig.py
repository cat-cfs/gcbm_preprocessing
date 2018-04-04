import json


class SubRegionConfig(object):
    def __init__(self, configPath, subRegionNames=None):
        self.config = self.loadJson(configPath)
        self.subRegionsByName = {}
        self.subRegions = []
        self._initialize(subRegionNames)

    def loadJson(self, path):
        with open(path) as json_data:
            return json.load(json_data)

    def _initialize(self, subRegionNames=None):
        for r in self.config:
            subRegionName = r["Name"]
            if not subRegionNames is None and not subRegionName in subRegionNames:
                continue
            self.subRegions.append(r)
            if subRegionName in self.subRegionsByName:
                raise ValueError("duplicate subregion detected {0}"
                                 .format(subRegionName))
            self.subRegionsByName[subRegionName] = r

    def GetRegion(self, regionName):
        return self.subRegionsByName[regionName]

    def GetRegions(self):
        return self.subRegions


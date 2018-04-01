import json

class FutureConfig(object):
    def __init__(self, configPath, pathRegistry):
        self.config = self.loadJson(configPath)
        self.pathRegistry = pathRegistry
        self.disturbances = {x["Name"]: x for x in
                             self.config["Disturbance_Types"]}
        if len(self.disturbances) != len(self.config["Disturbance_Types"]):
            raise ValueError("duplicate disturbance name detected")

        self.scenarios = {x["Name"]: x for x in 
                          self.config["Scenarios"]}

        if len(self.scenarios) != len(self.config["Scenarios"]):
            raise ValueError("duplicate scenario name detected")

    def loadJson(self, path):
        with open(path) as json_data:
            return json.load(json_data)


    def GetStartYear(self):
        return int(self.config["Start_Year"])

    def GetEndYear(self):
        return int(self.config["End_Year"])

    def GetBaseRasterDir(self, region_name):
        return self.pathRegistry.UnpackPath(
            self.config["Base_Raster_Dir"],
            region_name)

    def GetRasterOutputDir(self, region_name):
        return self.pathRegistry.UnpackPath(
            self.config["Future_Dist_Output_Dir"],
            region_name)

    def GetHistoricTilerConfigPath(self, region_name):
        return self.pathRegistry.UnpackPath(
            self.config["HistoricTilerConfigPath"],
            region_name)

    def GetPathFormat(self, disturbanceName):
        return self.disturbances[disturbanceName]["Path_Format"]

    def GetCBMDisturbanceType(self, disturbanceName):
        return self.disturbances[disturbanceName]["CBM_Name"]

    def GetScenario(self, scenario_name):
        return self.scenarios[scenario_name]

    def GetScenarios(self):
        return self.scenarios
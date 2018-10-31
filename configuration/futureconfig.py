import json

class FutureConfig(object):
    def __init__(self, configPath):
        self.config = self.loadJson(configPath)
        
        self.Historic = {x["Name"]: "Type" in x 
            and x["Type"] == "Historic" 
            for x in self.config["Scenarios"]
            }
            
        self.disturbances = {
            x["Name"]: x for x in
            self.config["Disturbance_Types"]
        }

        if len(self.disturbances) != len(self.config["Disturbance_Types"]):
            raise ValueError("duplicate disturbance name detected")

        self.scenariosbyName = {x["Name"]: x for x in 
                          self.config["Scenarios"]}

        if len(self.scenariosbyName) != len(self.config["Scenarios"]):
            raise ValueError("duplicate scenario name detected")

    def IsHistoric(self, scenarioName):
        return self.Historic[scenarioName]
        
    def loadJson(self, path):
        with open(path) as json_data:
            return json.load(json_data)

    def GetStartYear(self):
        return int(self.config["Start_Year"])

    def GetEndYear(self):
        return int(self.config["End_Year"])

    def GetPathFormat(self, disturbanceName):
        return self.disturbances[disturbanceName]["Path_Format"]

    def GetScenario(self, scenario_name):
        return self.scenariosbyName[scenario_name]

    def GetScenarios(self):
        return self.config["Scenarios"]
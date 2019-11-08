import json
import multiprocessing


class PreprocessorConfig(object):
    def __init__(self, configPath, pathRegistry):
        self.config = self.loadJson(configPath)
        self.pathRegistry = pathRegistry

    def loadJson(self, path):
        with open(path) as json_data:
            return json.load(json_data)

    def GetResolution(self):
        return self.config["Resolution"]

    def GetAreaMajorityRule(self):
        return self.config["Area_Majority_Rule"]

    def GetNProcesses(self):
        if self.config["N_Processes"] == "Auto":
            return multiprocessing.cpu_count() - 1
        else:
            return int(self.config["N_Processes"])

    def GetInventoryWorkspace(self, region_path):
        return self.pathRegistry.UnpackPath(
            self.config["Inventory_Workspace"], region_path=region_path)

    def GetInventoryYear(self):
        return self.config["Inventory_Year"]

    def GetInventoryFilter(self, inventory_workspace_filter):
         return self.pathRegistry.UnpackPath(
            self.config["Inventory_Filter"], inventory_workspace_filter = inventory_workspace_filter)

    def GetInventoryField(self, field):
        return self.config["Inventory_Field_Names"][field]

    def GetInventoryFieldNames(self):
        return self.config["Inventory_Field_Names"]

    def GetInventoryClassifiers(self):
        return self.config["Inventory_Classifiers"]

    def GetReportingClassifiers(self):
        return self.config["Reporting_Classifiers"]

    def GetRollbackRange(self):
        return self.config["Rollback_Range"]

    def GetHistoricRange(self):
        return self.config["Historic_Range"]

    def GetHistoricHarvestYearField(self):
        return self.config["HistoricHarvestYearField"]

    def GetInventoryRasterOutputDir(self, region_path):
        x = self.config["InventoryRasterOutputDir"]
        return self.pathRegistry.UnpackPath(x, region_path=region_path)

    def GetRollbackDisturbancesOutputDir(self, region_path):
        x = self.config["RollbackDisturbancesOutputDir"]
        return self.pathRegistry.UnpackPath(x, region_path=region_path)

    def GetRollbackInputLayers(self, region_path):
        x = self.config["RollbackInputLayers"]
        result = []
        for dist in x:
            result.append({
                "Workspace": self.pathRegistry.UnpackPath(dist["Workspace"], region_path=region_path),
                "WorkspaceFilter": dist["WorkspaceFilter"],
                "YearSQL": dist["YearSQL"],
                "DisturbanceTypeCode": dist["DisturbanceTypeCode"]
            })
        return result

    def GetHistoricMergedDisturbanceLayers(self):
        return self.config["HistoricMergedDisturbanceLayers"]

    def GetRollbackOutputDisturbanceTypes(self):
        return self.config["RollbackOutputDisturbanceTypes"]

    def GetDistAgeProportionFilePath(self):
        return self.pathRegistry.UnpackPath(
            self.config["DistAgeProportionFilePath"])

    def GetRollbackTilerConfigPath(self, region_path):
        return self.pathRegistry.GetPath(
            "RollbackTilerConfigPath", region_path=region_path)

    def GetHistoricTilerConfigPath(self, region_path):
        return self.pathRegistry.GetPath(
            "HistoricTilerConfigPath", region_path=region_path)

    def GetHistoricFireDisturbances(self, region_path):
        item = self.config["HistoricFireDisturbances"]
        return {
            "Name": item["Name"],
            "Workspace": self.pathRegistry.UnpackPath(item["Workspace"], region_path=region_path),
            "WorkspaceFilter": item["WorkspaceFilter"],
            "YearField": item["YearField"],
            "CBM_Disturbance_Type": item["CBM_Disturbance_Type"]
        }

    def GetHistoricHarvestDisturbances(self, region_path):
        item = self.config["HistoricHarvestDisturbances"]
        return {
            "Name": item["Name"],
            "Workspace": self.pathRegistry.UnpackPath(item["Workspace"], region_path=region_path),
            "WorkspaceFilter": item["WorkspaceFilter"],
            "YearField": item["YearField"],
            "CBM_Disturbance_Type": item["CBM_Disturbance_Type"]
        }

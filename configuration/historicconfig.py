import json

class HistoricConfig(object):
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

    def GetInventoryWorkspace(self, region_path):
        return self.pathRegistry.UnpackPath(
            self.config["Inventory_Workspace"], region_path)

    def GetInventoryYear(self):
        return self.config["Inventory_Year"]

    def GetInventoryFilter(self):
        return self.config["Inventory_Filter"]

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
        return self.pathRegistry.UnpackPath(x, region_path)

    def GetRollbackDisturbancesOutput(self, region_path):
        x = self.config["RollBackDisturbancesOutput"]
        return self.pathRegistry.UnpackPath(x, region_path)

    def GetSlashBurnPercent(self):
        x = float(self.config["SlashburnPercent"])
        if x<0 or x >100:
            raise ValueError("configuration slashburn percent out of range." \
                + "expected 0<=x<=100, got: {}".format(x))
        return x

    def GetRollbackDisturbances(self, region_path):
        return self.GetDisturbanceLayers(region_path, self.config["Rollback_Disturbance_Names"])

    def GetDisturbanceLayers(self, region_path, name_filter=None):
        x = self.config["DisturbanceLayers"]
        result = []
        for dist in x:
            if name_filter is not None:
                if dist["Name"] not in name_filter:
                    continue
            result.append({
                "Code": dist["Code"],
                "Name": dist["Name"],
                "Workspace": self.pathRegistry.UnpackPath(dist["Workspace"], region_path),
                "WorkspaceFilter": dist["WorkspaceFilter"],
                "YearField": dist["YearField"],
                "CBM_Disturbance_Type": dist["CBM_Disturbance_Type"]
            })
        return result

    def GetDistAgeProportionFilePath(self):
        return self.pathRegistry.UnpackPath(
            self.config["DistAgeProportionFilePath"])

    def GetHistoricTilerConfigPath(self, region_path):
        return self.pathRegistry.GetPath(
            "HistoricTilerConfigPath", region_path)


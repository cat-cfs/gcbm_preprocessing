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

    def GetSlashBurnInfo(self):
        info = self.config["SlashBurnInfo"]
        x = info["Percent"]
        if x<0 or x >100:
            raise ValueError("configuration slashburn percent out of range." \
                + "expected 0<=x<=100, got: {}".format(x))
        return info

    def GetRollbackInputLayers(self, region_path):
        x = self.config["RollbackInputLayers"]
        result = []
        for dist in x:
            result.append({
                "Code": dist["Code"],
                "Name": dist["Name"],
                "Workspace": self.pathRegistry.UnpackPath(dist["Workspace"], region_path),
                "WorkspaceFilter": dist["WorkspaceFilter"],
                "YearField": dist["YearField"],
                "CBM_Disturbance_Type": dist["CBM_Disturbance_Type"],
            })
        return result

    def GetInsectDisturbances(self, region_path):
        item = self.config["InsectDisturbances"]
        return {
            "Name": item["Name"],
            "Workspace": self.pathRegistry.UnpackPath(item["Workspace"], region_path),
            "WorkspaceFilter": item["WorkspaceFilter"],
            "DisturbanceTypeField": item["DisturbanceTypeField"],
            "CBM_DisturbanceType_Lookup": item["CBM_DisturbanceType_Lookup"]
        }

    def GetDistAgeProportionFilePath(self):
        return self.pathRegistry.UnpackPath(
            self.config["DistAgeProportionFilePath"])

    def GetRollbackTilerConfigPath(self, region_path):
        return self.pathRegistry.GetPath(
            "RollbackTilerConfigPath", region_path)

    def GetHistoricTilerConfigPath(self, region_path):
        return self.pathRegistry.GetPath(
            "HistoricTilerConfigPath", region_path)

    def GetDefaultSpatialBoundaries(self, region_path):

        layer = self.pathRegistry.UnpackPath(
            self.config["SpatialBoundaries"]["Path"])

        return {
            "Path": layer,
            "Attributes": self.config["SpatialBoundaries"]["Attributes"]
        }

    def GetMeanAnnualTemp(self, region_path):
        path = self.pathRegistry.UnpackPath(
            self.config["MeanAnnualTemp"]["Path"])

        return {
            "Path": path,
            "NoData_Value": self.config["MeanAnnualTemp"]["Nodata_Value"]
        }

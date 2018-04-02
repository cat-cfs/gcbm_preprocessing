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

    def GetRollbackDisturbancesOutputDir(self, region_path):
        x = self.config["RollbackDisturbancesOutputDir"]
        return self.pathRegistry.UnpackPath(x, region_path)

    def GetSlashBurnPercent(self):
        x = float(self.config["SlashburnPercent"])
        if x<0 or x >100:
            raise ValueError("configuration slashburn percent out of range." \
                + "expected 0<=x<=100, got: {}".format(x))
        return x

    def GetRollbackInputLayers(self, region_path):
        x = self.config["RollbackInputLayers"]
        result = []
        for dist in x:
            result.append({
                "Workspace": self.pathRegistry.UnpackPath(dist["Workspace"], region_path),
                "WorkspaceFilter": dist["WorkspaceFilter"],
                "YearField": dist["YearField"],
            })
        return result

    def GetHistoricMergedDisturbanceLayers(self):
        return self.config["HistoricMergedDisturbanceLayers"]

    def GetHistoricSlashburnInput(self, region_path):
         x = self.config["HistoricSlashburnInput"]
         harvestLayer = x["HarvestLayer"]
         return {
            "Name": x["Name"],
            "CBM_Disturbance_Type": x["CBM_Disturbance_Type"],
            "HarvestLayer":{
                "Workspace": self.pathRegistry.UnpackPath(harvestLayer["Workspace"], region_path),
                "WorkspaceFilter": harvestLayer["WorkspaceFilter"],
                "YearField": harvestLayer["YearField"],
            }
          }

    def GetRollbackOutputDisturbanceTypes(self):
        return self.config["RollbackOutputDisturbanceTypes"]

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
            self.config["SpatialBoundaries"]["Path"], region_path)

        return {
            "Path": layer,
            "Attributes": self.config["SpatialBoundaries"]["Attributes"]
        }

    def GetMeanAnnualTemp(self, region_path):
        path = self.pathRegistry.UnpackPath(
            self.config["MeanAnnualTemp"]["Path"],
            region_path)

        return {
            "Path": path,
            "Nodata_Value": self.config["MeanAnnualTemp"]["Nodata_Value"]
        }

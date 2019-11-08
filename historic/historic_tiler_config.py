from gcbm.tilerconfig import TilerConfig
import os, logging
class HistoricTilerConfig(object):

    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path
        self.tilerConfig = TilerConfig(input_path)

    def Save(self):
        self.tilerConfig.save(self.output_path)

    def AddSplitDisturbanceLayers(self, layerData, first_year, last_year, classifiers):
        for year in range(first_year, last_year+1):
            filename = layerData["WorkspaceFilter"].replace("*", str(year))
            filepath = os.path.join(layerData["Workspace"], filename)
            if not os.path.exists(filepath):
                logging.warn("path does not exist '{}'".format(filepath))
                continue
            self.AddSplitDistLayer(
                name = "{0}{1}".format(layerData["Name"], year),
                path=filepath,
                year = year,
                yearField = layerData["YearField"],
                cbmDisturbanceTypeName = layerData["CBM_Disturbance_Type"],
                layerMeta="historic_{}".format(layerData["Name"]),
                classifiers=classifiers)

    def AddSplitDistLayer(self, name, path, year, yearField,
                               cbmDisturbanceTypeName,
                               layerMeta, age_after, classifiers):
        valueFilterConfig = self.tilerConfig.CreateConfigItem(
            "ValueFilter",
            target_val = year,
            str_comparison = True)

        attributeConfig = self.tilerConfig.CreateConfigItem(
            "Attribute",
            layer_name = yearField,
            filter = valueFilterConfig)

        vectorLayerConfig = self.tilerConfig.CreateConfigItem(
            "VectorLayer",
            name = name,
            path = self.tilerConfig.CreateRelativePath(self.output_path, path),
            attributes=attributeConfig)

        transitionRuleConfig = self.tilerConfig.CreateConfigItem(
            "TransitionRule",
            regen_delay=0,
            age_after=0,
            classifiers={x : "?" for x in classifiers})

        disturbanceLayerConfig = self.tilerConfig.CreateConfigItem(
            "DisturbanceLayer",
            lyr = vectorLayerConfig,
            year = year,
            disturbance_type= cbmDisturbanceTypeName,
            transition = transitionRuleConfig)

        logging.info("Adding '{}' to the tiler from '{}'".format(name, path))
        self.tilerConfig.AppendLayer(layerMeta, disturbanceLayerConfig)

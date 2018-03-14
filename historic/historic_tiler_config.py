from configuration.tilerconfig import TilerConfig
import os
class HistoricTilerConfig(object):

    def __init__(self, path):
        self.tilerConfig = TilerConfig(path)

    def AddMergedDisturbanceLayers(self, layerData, inventory_workspace, first_year, last_year):

        for item in layerData:
            for year in range(first_year,
                              last_year+1):
                self._AddMergedDisturbanceLayer(
                    name = "{0}_{1}".format(item["Name"], year),
                    year = year,
                    inventory_workspace = inventory_workspace,
                    year_field = item["DisturbanceMapping"]["YearField"],
                    cbmDisturbanceTypeName = item["DisturbanceMapping"]["CBM_Disturbance_Type"],
                    layerMeta = layerData["Metadata"])

    def AddHistoricInsectLayers(self, layerData, first_year, last_year):
        for year in range(first_year, last_year+1):
            filename = layerData["WorkspaceFilter"].replace("*", str(year))
            filepath = os.path.join(layerData["Workspace"], filename)
            self.AddHistoricInsectDisturbance(
                name = "{0}_{1}".format(layerData["Name"], year),
                path=filepath,
                year = year,
                attribute = layerData["DisturbanceMapping"]["DisturbanceTypeField"],
                attribute_lookup = layerData["DisturbanceMapping"]["CBM_DisturbanceType_Lookup"])

    def AddHistoricInsectDisturbance(self, name, path,
                                        year, attribute, attribute_lookup,
                                        layerMeta):
        attributeConfig = self.tilerConfig.CreateConfigItem(
            "Attribute",
            layer_name=attribute,
            substitutions=attribute_lookup)

        vectorlayerConfig = self.tilerConfig.CreateConfigItem(
            "VectorLayer",
            name = name,
            path = path,
            attributes = attributeConfig)

        transitionRuleConfig = self.tilerConfig.CreateConfigItem(
            "TransitionRule",
            regen_delay=0,
            age_after=-1)

        disturbanceLayerConfig = self.tilerConfig.CreateConfigItem(
            "DisturbanceLayer",
            lyr = vectorlayerConfig,
            year = year,
            disturbance_type= self.tilerConfig.CreateConfigItem(
                "Attribute", layer_name=attribute),
            transition = transitionRuleConfig)

        self.tilerConfig.AppendLayer(layerMeta, disturbanceLayerConfig)

    def AddMergedDisturbanceLayer(self, name, year, inventory_workspace, 
                                     year_field, cbmDisturbanceTypeName,
                                     layerMeta):
        """
        append a disturbance layer from the inventory gdb layer "merged disturbances"
        @param name the name of the tiled output layer file
        @param year the year of the disturbance layer 
        @param inventory_workspace the gdb file containing the merged disturbances layer
        @param year_field the name of the field in the merged disturbances layer
        @param cbmDisturbanceTypeName the name of the CBM disturbance type (as defined in the CBM database)
        @param layerMeta the metadata within the tiler config for this layer
        """
        filterConfig = self.tilerConfig.CreateConfigItem(
            "SliceValueFilter",
            target_val=year,
            slice_len=4)

        attributeConfig = self.tilerConfig.CreateConfigItem(
            "Attribute",
            layer_name=year_field,
            filter=filterConfig)

        vectorLayerConfig =  self.tilerConfig.CreateConfigItem(
            "VectorLayer",
            name=name,
            path=inventory_workspace,
            attributes=attributeConfig,
            layer="MergedDisturbances")

        transitionConfig = self.tilerConfig.CreateConfigItem(
            "TransitionRule",
            regen_delay = 0,
            age_after = 0)

        disturbanceLayerConfig = self.tilerConfig.CreateConfigItem(
            "DisturbanceLayer",
            lyr = vectorLayerConfig,
            year = year,
            disturbance_type = cbmDisturbanceTypeName,
            transition = transitionConfig)

        self.tilerConfig.AppendLayer(layerMeta,
                                     disturbanceLayerConfig)

    def AddSlashburn(self, year, path, yearField, name,
                      cbmDisturbanceTypeName, layerMeta):
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
            path = path,
            attributes=attributeConfig)

        transitionConfig = self.tilerConfig.CreateConfigItem(
            regen_delay=0,
            age_after=0)

        disturbanceLayerConfig = self.tilerConfig.CreateConfigItem(
            "DisturbanceLayer",
            lyr = vectorLayerConfig,
            year = year,
            disturbance_type = cbmDisturbanceTypeName,
            transition = transitionConfig)

        self.tilerConfig.AppendLayer(layerMeta,
                                     disturbanceLayerConfig)
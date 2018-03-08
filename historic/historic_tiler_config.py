from configuration.tilerconfig import TilerConfig

class HistoricTilerConfig(object):

    def __init__(self, path):
        self.tilerConfig = TilerConfig(path)

    def AddMergedDisturbanceLayers(self, layerData, inventory_workspace, rollback_end_year, historic_end_year):

        for item in layerData:
            for year in range(rollback_end_year + 1,
                              historic_end_year + 1):
                self._AddMergedDisturbanceLayer(
                    name = "{0}_{1}".format(item["Name"], year),
                    year = year,
                    inventory_workspace = inventory_workspace,
                    year_field = item["YearField"],
                    cbmDisturbanceTypeName = item["CBMDisturbanceTypeName"],
                    layerMeta = layerData["Metadata"])

    def _AddHistoricInsectDisturbance(self, name, filename,
                                        year, attribute, attribute_lookup,
                                        layerMeta):
        attributeConfig = self.tilerConfig.CreateConfigItem(
            "Attribute",
            layer_name=attribute,
            substitutions=attribute_lookup)

        vectorlayerConfig = self.tilerConfig.CreateConfigItem(
            "VectorLayer",
            name = name,
            path = filename,
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

    def _AddMergedDisturbanceLayer(self, name, year, inventory_workspace, 
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

    def _AddSlashburn(self, year, path, yearField, name_filter, name,
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
from gcbm.tilerconfig import TilerConfig
import os, logging
class HistoricTilerConfig(object):

    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path
        self.tilerConfig = TilerConfig(input_path)

    def Save(self):
        self.tilerConfig.save(self.output_path)


    def AddAdminEcoLayers(self, spatial_boundaries_path, attributes):
        for attribute_name, attribute_value in attributes.items():
            attributeConfig = self.tilerConfig.CreateConfigItem(
                "Attribute",
                layer_name=attribute_value)

            vectorLayerConfig = self.tilerConfig.CreateConfigItem(
                "VectorLayer",
                name = attribute_name,
                path = self.tilerConfig.CreateRelativePath(self.output_path, spatial_boundaries_path),
                attributes=attributeConfig)
            self.tilerConfig.AppendLayer("admin_eco", vectorLayerConfig)

    def AddClimateLayer(self, climateLayerPath, nodata_value):
        self.tilerConfig.AppendLayer(
            "climate",
            self.tilerConfig.CreateConfigItem(
                "RasterLayer",
                path=self.tilerConfig.CreateRelativePath(self.output_path, climateLayerPath),
                nodata_value=nodata_value))

    def AddMergedDisturbanceLayers(self, layerData, inventory_workspace,
                                   first_year, last_year, classifiers):

        for item in layerData:
            for year in range(first_year,
                              last_year+1):
                self.AddMergedDisturbanceLayer(
                    name = "{0}_{1}".format(item["Name"], year),
                    year = year,
                    inventory_workspace = inventory_workspace,
                    year_field = item["YearField"],
                    cbmDisturbanceTypeName = item["CBM_Disturbance_Type"],
                    layerMeta = "historic_{}".format(item["Name"]),
                    classifiers = classifiers)

    def AddHistoricInsectLayers(self, layerData, first_year, last_year, classifiers):
        for year in range(first_year, last_year+1):
            filename = layerData["WorkspaceFilter"].replace("*", str(year))
            filepath = os.path.join(layerData["Workspace"], filename)
            if not os.path.exists(filepath):
                logging.warn("insect path does not exist '{}'".format(filepath))
                continue
            self.AddHistoricInsectLayer(
                name = "{0}_{1}".format(layerData["Name"], year),
                path=filepath,
                year = year,
                attribute = layerData["DisturbanceTypeField"],
                attribute_lookup = layerData["CBM_DisturbanceType_Lookup"],
                layerMeta="historic_{}".format(layerData["Name"]),
                classifiers=classifiers)

    def AddHistoricInsectLayer(self, name, path,
                                year, attribute, attribute_lookup,
                                layerMeta,
                                classifiers):
        attributeConfig = self.tilerConfig.CreateConfigItem(
            "Attribute",
            layer_name=attribute,
            substitutions=attribute_lookup)

        vectorlayerConfig = self.tilerConfig.CreateConfigItem(
            "VectorLayer",
            name = name,
            path = self.tilerConfig.CreateRelativePath(self.output_path, path),
            attributes = attributeConfig)

        transitionRuleConfig = self.tilerConfig.CreateConfigItem(
            "TransitionRule",
            regen_delay=0,
            age_after=-1,
            classifiers={x : "?" for x in classifiers})

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
                                     layerMeta, classifiers):
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
            path= self.tilerConfig.CreateRelativePath(self.output_path, inventory_workspace),
            attributes=attributeConfig,
            layer="MergedDisturbances")

        transitionConfig = self.tilerConfig.CreateConfigItem(
            "TransitionRule",
            regen_delay = 0,
            age_after = 0,
            classifiers={x : "?" for x in classifiers})

        disturbanceLayerConfig = self.tilerConfig.CreateConfigItem(
            "DisturbanceLayer",
            lyr = vectorLayerConfig,
            year = year,
            disturbance_type = cbmDisturbanceTypeName,
            transition = transitionConfig)

        self.tilerConfig.AppendLayer(layerMeta,
                                     disturbanceLayerConfig)

    def AddSlashburn(self, year, path, yearField, name,
                      cbmDisturbanceTypeName, layerMeta,
                      classifiers):
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
            name = "{0}_{1}".format(name,year),
            path = self.tilerConfig.CreateRelativePath(self.output_path, path),
            attributes=attributeConfig)

        transitionConfig = self.tilerConfig.CreateConfigItem(
            "TransitionRule",
            regen_delay=0,
            age_after=0,
            classifiers={x : "?" for x in classifiers})

        disturbanceLayerConfig = self.tilerConfig.CreateConfigItem(
            "DisturbanceLayer",
            lyr = vectorLayerConfig,
            year = year,
            disturbance_type = cbmDisturbanceTypeName,
            transition = transitionConfig)

        self.tilerConfig.AppendLayer(layerMeta,
                                     disturbanceLayerConfig)
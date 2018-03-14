from configuration.tilerconfig import TilerConfig

class RollbackTilerConfig(object):
    def __init__(self):
        self.tilerConfig = TilerConfig()

    def Generate(self, outPath, inventoryMeta, resolution,
                 rollback_disturbances_path, rollback_range, dist_lookup):
        self._AddInventory(inventoryMeta, resolution, outPath)
        self._AddRollbackDisturbances(rollback_disturbances_path,
                                      rollback_range, dist_lookup, outPath)
        self._WriteTilerConfig(outPath)

    def _AddInventory(self, inventoryMeta, resolution, config_path):

        t = self.tilerConfig
        inventoryLayers = [
            t.CreateConfigItem(typeName="RasterLayer",
                               path=self.tilerConfig.CreateRelativePath(config_path, x["file_path"]),
                               attributes=[x["attribute"]],
                               attribute_table=x["attribute_table"])
            for x in inventoryMeta]

        boundingbox = t.CreateConfigItem(typeName="BoundingBox",
                                         layer=inventoryLayers[0],
                                         pixel_size=resolution)
        t.Initialize(
            t.CreateConfigItem(typeName="CompressingTiler2D",
                             bounding_box=boundingbox,
                             use_bounding_box_resolution=True))

        for i in inventoryLayers:
            t.AppendLayer("inventory", i)

    def _AddRollbackDisturbances(self, rollback_disturbances_path,
                                rollback_range, dist_lookup, config_path):

        for year in range(rollback_range[0], rollback_range[1] + 1):
            for dist in dist_lookup:
                self._AddRollbackDisturbance(rollback_disturbances_path,
                                       year,
                                       dist["Code"],
                                       dist["Name"],
                                       dist["CBM_Disturbance_Type"],
                                       config_path)

    def _AddRollbackDisturbance(self, rollback_disturbances_path,
                               year, dist_code, name,
                               cbm_disturbance_type_name, config_path):

        t = self.tilerConfig
        
        DistYearAttributeConfig = t.CreateConfigItem(
            "Attribute", 
            layer_name="DistYEAR_n",
            filter=t.CreateConfigItem("ValueFilter",target_val=year))

        DistTypeAttributeConfig = t.CreateConfigItem(
            "Attribute",
            layer_name="DistType",
            filter=t.CreateConfigItem("ValueFilter",target_val=dist_code),
            substitution={dist_code: cbm_disturbance_type_name})
        
        RegenDelayAttributeConfig = t.CreateConfigItem(
            "Attribute", 
            layer_name="RegenDelay")

        attributeList = t.CreateConfigItemList(
            "Attribute",
            [
                DistYearAttributeConfig,
                DistTypeAttributeConfig,
                RegenDelayAttributeConfig
            ]
        )

        vectorLayerConfig =  t.CreateConfigItem(
            "VectorLayer",
            name = "rollback_{}_{}".format(name, year),
            path = self.tilerConfig.CreateRelativePath(config_path,rollback_disturbances_path) ,
            attributes = attributeList)

        transitionConfig = t.CreateConfigItem(
            "TransitionRule",
            regen_delay = RegenDelayAttributeConfig,
            age_after = 0)

        disturbanceLayerConfig = t.CreateConfigItem(
            "DisturbanceLayer",
            lyr = vectorLayerConfig,
            year = year,
            disturbance_type = DistTypeAttributeConfig,
            transition = transitionConfig)
        
        t.AppendLayer("rollback_{}".format(name),
                      disturbanceLayerConfig)

    def _WriteTilerConfig(self, path):
        self.tilerConfig.writeJson(path)
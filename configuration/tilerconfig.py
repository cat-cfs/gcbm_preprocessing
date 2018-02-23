import json
from pydoc import locate

class TilerConfig(object):

    def __init__(self, path=None):
        self.typeRegistry = {
            "BoundingBox": "mojadata.boundingbox",
            "CompressingTiler2D": "mojadata.compressingtiler2d",
            "VectorLayer": "mojadata.layer.vectorlayer",
            "RasterLayer": "mojadata.layer.rasterlayer",
            "DisturbanceLayer": "mojadata.layer.gcbm.disturbancelayer",
            "Attribute": "mojadata.layer.attribute",
            "ValueFilter": "mojadata.layer.filter.valuefilter",
            "SliceValueFilter": "mojadata.layer.filter.slicevaluefilter",
            "TransitionRule": "mojadata.layer.gcbm.transitionrule",
            "SharedTransitionRuleManager": "mojadata.layer.gcbm.transitionrulemanager"
            }
        self.layerMetaIndex = {}
        self.config = {}
        if path is not None:
           config = self.loadJson(path)
           for layer in config["Layers"]:
               self.UpdateMetaIndex(layer["Metadata"],
                                   layer["LayerConfig"])

    def GetFullyQualifiedTypeName(self, typename):
        if not typeName in self.typeRegistry:
            raise ValueError("specified type unknown/unsupported {0}"
                             .format(typeName))
        else:
            return "{0}.{1}".format(self.typeRegistry[typename], typename)

    def AssembleTilerObject(self, config):
        args = {}
        for k,v in config["args"].items():
            if isinstance(v, dict) and "tiler_type" in v:
                args[k] = self.AssembleTilerObject(v)
            else:
                args[k] = v
        type = locate(self.GetFullyQualifiedTypeName(config["tiler_type"]))
        if not type:
            raise ValueError("specified tiler type not found: '{}'."
                             .format(config["tiler_type"]))

        return type(**args)

    def AssembleTiler(self):
        tilerConfig = self.config["TilerConfig"]
        tiler = AssembleTilerObject(tilerConfig)

    def AssembleLayers(self):
        layers = []
        for layerConfig in self.config["Layers"]:
            config = layerConfig["LayerConfig"]
            layer = self.AssembleTilerObject(config)
            layers.append(layer)

    def UpdateMetaIndex(self, layerMeta, layerConfig):
        if layerMeta in self.layerMetaIndex:
            self.layerMetaIndex[layerMeta].append(layerConfig)
        else:
            self.layerMetaIndex[layerMeta] = [layerConfig]

    def Initialize(self, tilerConfig):
        self.config["TilerConfig"] = tilerConfig
        self.config["Layers"] = []

    def AppendLayer(self, layerMeta, layerConfig):
        self.config["Layers"].append({
            "Metadata": layerMeta,
            "LayerConfig": layerConfig
        })
        self.UpdateMetaIndex(layerMeta, layerConfig)

    def GetLayer(self, layerMeta):
        return self.layerMetaIndex[layerMeta]

    def writeJson(self, path, indent=4):
        with open(path, 'w') as outfile:
            json.dump(self.config, outfile, indent=indent)

    def loadJson(self, path):
        with open(path) as json_data:
            return json.load(json_data)

    def CreateConfigItem(self, typeName, **kwargs):
        if not typeName in self.typeRegistry:
            raise ValueError("specified type unknown/unsupported {0}".format(typeName))
        return {
            "tiler_type": typeName,
            "args": kwargs
        }

    def CreateVectorLayerConfig(self, name, path, attributeConfigs, 
                    raw=False, nodata_value=-1,
                    data_type=None, layer=None, date=None):
        return self.CreateConfigItem(
            "VectorLayer",
             name=name,
             path=path,
             attributes=attributeConfigs,
             raw=raw,
             nodata_value=nodata_value,
             data_type=data_type,
             layer=layer,
             date=date)

    def CreateDisturbanceLayerConfig(self, layerConfig, year, disturbance_type, transitionConfig=None):

        return self.CreateConfigItem(
            "DisturbanceLayer", 
            lyr = layerConfig,
            year = year,
            disturbance_type = disturbance_type,
            transition = transitionConfig)

    def CreateTransitionRuleConfig(self, regen_delay=0, age_after=-1, classifiers=None):
        return self.CreateConfigItem(
            "TransitionRule",
            regen_delay=regen_delay,
            age_after=age_after,
            classifiers=classifiers)

    def CreateAttributeConfig(self, layer_name, db_name=None, filterConfig=None, substitutions=None):
        return self.CreateConfigItem(
            "Attribute", 
            layer_name = layer_name,
            db_name = db_name,
            filter = filterConfig,
            substitutions = substitutions)

    def CreateSliceValueFilterConfig(self, target_val, slice_pos=0, slice_len=None):
        return self.CreateConfigItem(
            "SliceValueFilter",
            target_val=target_val,
            slice_pos=slice_pos,
            slice_len=slice_len)
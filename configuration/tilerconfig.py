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
        try:
            inst = type(**args)
            return inst
        except:
            raise RuntimeError("unable to create tiler type '{0}', specified arguments are '{1}'"
                               .format(config["tiler_type"], **args))

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

    def CreateConfigItemList(self, typeName, items=None):
        itemlist = {
            "tiler_type": typeName,
            "argsList": []
        }
        if not items is None:
            itemlist = self.AppendToConfigItemList(itemlist, items)
        return itemlist

    def AppendToConfigItemList(self, itemList, items):
        listType = itemList["tiler_type"]
        for item in items:
            if item["tiler_type"] != listType:
               raise ValueError("mixed types within item list not supported")
            itemList.argsList.append(item["args"])
        return itemList

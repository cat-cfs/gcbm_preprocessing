import json
from pydoc import locate

class TilerConfig(object):

    def __init__(self, path=None):

        self.layerMetaIndex = {}
        self.config = {}
        if path is not None:
           config = self.loadJson(path)
           for layer in config["Layers"]:
               self.UpdateMetaIndex(layer["Metadata"],
                                   layer["LayerConfig"])

    def AssembleTilerObject(self, config):
        args = {}
        for k,v in config["args"].items():
            if isinstance(v, dict) and "tiler_type" in v:
                args[k] = AssembleTilerObject(v)
            else:
                args[k] = v
        type = locate(config["tiler_type"])
        if not type:
            raise ValueError("specified tiler type not found: '{}'." +
                "Make sure to use fully qualified name".format(
                config["tiler_type"]))

        return type(**args)

    def AssembleTiler(self):
        tilerConfig = self.config["TilerConfig"]
        tiler = AssembleTilerObject(tilerConfig)

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
            json.dumps(self.config, indent=indent)

    def loadJson(self, path):
        with open(path) as json_data:
            return json.load(json_data)

    def CreateConfigItem(self, typeName, **kwargs):
        return {
            "tiler_type": typeName,
            "args": kwargs
        }

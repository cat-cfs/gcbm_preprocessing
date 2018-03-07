import json

class FutureConfig(object):
    def __init__(self, configPath, pathRegistry):
        self.config = self.loadJson(configPath)
        self.pathRegistry = pathRegistry

    def loadJson(self, path):
        with open(path) as json_data:
            return json.load(json_data)

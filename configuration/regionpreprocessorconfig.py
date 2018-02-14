import json

class RegionPreprocessorConfig(object):
    def __init__(self, path):
        self.data = self.loadJson(path)

    def loadJson(self, path):
        with open(path) as json_data:
            return json.load(json_data)
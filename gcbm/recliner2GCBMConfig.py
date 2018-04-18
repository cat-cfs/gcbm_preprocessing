import json

class Recliner2GCBMConfig(object):
    def __init__(self, template_path):
        self.config = self.loadJson(template_path)

    def loadJson(self, path):
        with open(path) as json_data:
            return json.load(json_data)

    def writeJson(self, path, indent=4):
        with open(path, 'w') as outfile:
            json.dump(self.config, outfile, indent=indent)

    def setGrowthCurvePath(self, growthcurvepath):
        self.config["GrowthCurves"]["Path"] = growthcurvepath
        for cset in self.config["ClassifierSet"]:
            cset["Path"] = growthcurvepath

    def setOutputPath(self, outputPath):
        self.config["OutputPath"] = outputPath

    def setArchiveIndexPath(self, archiveIndexPath):
        self.config["AIDBPath"] = archiveIndexPath

    def setTransitionRulesPath(self, transitionRulesPath):
        self.config["TransitionRules"]["Path"] = transitionRulesPath

    def save(self, out_path):
        self.writeJson(out_path)



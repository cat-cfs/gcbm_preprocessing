import archook
archook.get_arcpy()
import arcpy

class ClipInput(object):
    def __init__(self, ProgressPrinter):
        self.ProgressPrinter = ProgressPrinter

    def reproject(self, path, output, layer=None):
        pass

    def clip(self, path, output, clip_feature, layer=None):
        if layer:
            Clip_analysis(r'{}\{}'.format(path, layer), clip_feature, output, "")
        else:
            Clip_analysis(path, clip_feature, output, "")
        return output

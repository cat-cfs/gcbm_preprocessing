class ConfigureGCBM(object):
    def __init__(self, output_dir, tiledDisturbances, input_db, classifiers, resolution, exe_path, ProgressPrinter):
        self.ProgressPrinter = ProgressPrinter
        self.output_dir = output_dir
        self.tiled_disturbances = tiledDisturbances
        self.input_db = input_db
        self.classifiers = classifiers
        self.resolution = resolution
        self.exe_path = exe_path

    def configure_config(self):
        pass

    def configure_provider(self):
        pass

import glob

class ConfigureGCBM(object):
    def __init__(self, output_dir, GCBM_scenarios, tiled_dirs, input_db, resolution, rollback_range, future_range, tiles_template_dir, exe_path, ProgressPrinter):
        self.ProgressPrinter = ProgressPrinter
        self.output_dir = output_dir
        self.tiled_disturbances = tiledDisturbances
        self.input_db = input_db
        self.resolution = resolution
        self.exe_path = exe_path

    def getTiles(self):
        pass

    def configureProvider(self):
        for dir in tiled_dirs:
            for moja_dir in glob.glob(r'{}\*\ '.format(dir)):
                tiled_layers.append(moja_dir)
        tiled_layers

    def configureConfig(self):
        pass


'''
Parameters
config:
$start_year
$end_year
$tiles
$disturbances
$disturbance_vars
$output_db
$output_dir

config_provider:
$input_db
resolution
$rollbackHarvest
$historicHarvest
$rollbackFire
$historicFire
$MPB
$projectedDisturbances
$classifiers
$reportingIndicators

'''

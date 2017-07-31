import glob
import inspect

class ConfigureGCBM(object):
    def __init__(self, output_dir, GCBM_scenarios, inventory, reportingIndicators,
                        resolution, rollback_range, future_range, exe_path, ProgressPrinter):
        self.ProgressPrinter = ProgressPrinter
        self.output_dir = output_dir
        self.GCBM_scenarios = GCBM_scenarios
        self.inventory = inventory
        self.reporting_indicators = reportingIndicators
        self.resolution = resolution
        self.start_year = rollback_range[0]
        self.end_year = future_range[1]
        self.exe_path = exe_path

        self.classifiers = []
        self.disturbances = []


    def configureGCBM(self, input_db, general_lyrs, tiler_output_dir):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1).start()
        layer_config_names = self.configureProvider(input_db, general_lyrs, tiler_output_dir)
        self.configureConfig(layer_config_names)
        pp.finish()

    def getTiles(self):
        tiles_text = []
        for file in glob.glob(r'{}\*'.format(tiles_template_dir)):
            if os.path.basename(file).split('.')[-1]=='blk':
                tiles_text.append(os.path.basename(file).split('.')[0].split('_moja_')[-1])
        tiles = []
        for tile_text in tiles_text:
            x, y = tile_text.split('_')
            tiles.append({"x":int(x), "y":int(y)})
        return tiles


    def configureProvider(self, input_db, general_lyrs, tiler_output):
        resolution = self.resolution

        provider_layers = []
        layer_config_names = []
        # harvest layers
        for moja_dir in glob.glob(r'{}\rollback_harvest*\ '.format(tiler_output))+glob.glob(r'{}\harvest*\ '.format(tiler_output)):
            basename = os.path.basename(moja_dir)
            year = basename.split('_moja')[0][-4:]
            name = basename.split('_moja')[0][:-5].split('_')[-1]
            provider_layers.append({
                "name": "{}_{}".format(name, year),
                "layer_path": moja_dir,
                "layer_prefix": basename
            })
        # fire layers
        for moja_dir in glob.glob(r'{}\rollback_fire*\ '.format(tiler_output))+glob.glob(r'{}\fire*\ '.format(tiler_output)):
            basename = os.path.basename(moja_dir)
            year = basename.split('_moja')[0][-4:]
            name = basename.split('_moja')[0][:-5].split('_')[-1]
            provider_layers.append({
                "name": "{}_{}".format(name, year),
                "layer_path": moja_dir,
                "layer_prefix": basename
            })
        # insect layers
        for moja_dir in glob.glob(r'{}\mpb*\ '.format(tiler_output)):
            basename = os.path.basename(moja_dir)
            year = basename.split('_moja')[0][-4:]
            name = basename.split('_moja')[0][:-5].split('_')[-1]
            provider_layers.append({
                "name": "{}_{}".format(name, year),
                "layer_path": moja_dir,
                "layer_prefix": basename
            })
        # projected layers
        pass

        disturbance_names = layer_config_names

        # general layers
        for name in general_lyrs:
            moja_dir = r'{}\{}_moja'.format(tiler_output, name)
            if name == 'age':
                pass
            provider_layers.append({
                "name": name,
                "layer_path": moja_dir,
                "layer_prefix": os.path.basename(moja_dir)
            })
        # reporting indicators
        for ri in reporting_indicators.getIndicators():
            provider_layers.append(ri)

    def configureConfig(self, layer_config_names):
        for name in layer_config_names:
            data_id = layer_config_names[name]
        for classifier in self.inventory.getClassifiers():
            if classifier in layer_config_names:
                classifiers.append(classifier)
            else:
                print "Warning: Classifier '{}' not added to GCBM config".format(classifer)
        disturbances = disturbance_names

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

import os
import glob
import inspect
import json
import sys
import logging

class ConfigureGCBM(object):
    def __init__(self, output_dir, gcbm_configs_dir, GCBM_scenarios, base_scenario, inventory, reportingIndicators,
                        resolution, rollback_range, actv_start_year, future_range, ProgressPrinter):
        logging.info("Initializing class {}".format(self.__class__.__name__))
        self.ProgressPrinter = ProgressPrinter
        self.output_dir = output_dir
        self.gcbm_configs_dir = gcbm_configs_dir
        self.GCBM_scenarios = GCBM_scenarios
        self.base_scenario = base_scenario
        self.inventory = inventory
        self.reporting_indicators = reportingIndicators
        self.tiler_template_dir = None
        self.resolution = resolution
        self.start_year = rollback_range[0]
        self.end_year = future_range[1]
        self.activity_start_year = actv_start_year


    def configureGCBM(self, input_db, general_lyrs, tiler_output_dir):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1).start()
        for scen in self.GCBM_scenarios:
            layer_config_names, disturbance_names = self.configureProvider(input_db, general_lyrs, tiler_output_dir, scen)
            self.configureConfig(layer_config_names, disturbance_names, scen)
        pp.finish()

    def getTiles(self):
        tiles_text = []
        for file in glob.glob(r'{}\*'.format(self.tiler_template_dir)):
            if os.path.basename(file).split('.')[-1]=='blk':
                tiles_text.append(os.path.basename(file).split('.')[0].split('_moja_')[-1])
        tiles = []
        for tile_text in tiles_text:
            x, y = tile_text.split('_')
            tiles.append({"x":int(x), "y":int(y)})
        logging.info('Tiles found: {}'.format(tiles))
        return tiles


    def configureProvider(self, input_db, general_lyrs, tiler_output, scenario):
        resolution = self.resolution

        provider_layers = []
        layer_config_names = {}
        # harvest layers
        for moja_dir in (glob.glob(r'{}\SCEN_{}\rollback_harvest_*_moja'.format(tiler_output, self.base_scenario))
            +glob.glob(r'{}\SCEN_{}\harvest_*_moja'.format(tiler_output, self.base_scenario))
            +glob.glob(r'{}\SCEN_{}\projected_harvest_*_moja'.format(tiler_output, self.base_scenario))):
            if self.tiler_template_dir == None:
                logging.info('Tiler template directory found.')
                self.tiler_template_dir = moja_dir
            basename = os.path.basename(moja_dir)
            year = basename.split('_moja')[0][-4:]
            name = basename.split('_moja')[0][:-5].split('_')[-1]
            name_year = '{}_{}'.format(name,year)
            if int(year) < self.activity_start_year:
                provider_layers.append({
                    "name": name_year,
                    "layer_path": moja_dir,
                    "layer_prefix": basename
                })
                layer_config_names.update({name_year:name_year})
        for moja_dir in glob.glob(r'{}\SCEN_{}\projected_harvest_*_moja'.format(tiler_output, self.GCBM_scenarios[scenario])):
            basename = os.path.basename(moja_dir)
            year = basename.split('_moja')[0][-4:]
            name = basename.split('_moja')[0][:-5].split('_')[-1]
            name_year = '{}_{}'.format(name,year)
            if int(year) >= self.activity_start_year:
                provider_layers.append({
                    "name": name_year,
                    "layer_path": moja_dir,
                    "layer_prefix": basename
                })
                layer_config_names.update({name_year:name_year})

        # fire layers
        for moja_dir in (glob.glob(r'{}\SCEN_{}\rollback_fire_*_moja'.format(tiler_output, self.base_scenario))
            +glob.glob(r'{}\SCEN_{}\fire_*_moja'.format(tiler_output, self.base_scenario))
            +glob.glob(r'{}\SCEN_{}\projected_fire_*_moja'.format(tiler_output, self.base_scenario))):
            basename = os.path.basename(moja_dir)
            year = basename.split('_moja')[0][-4:]
            name = basename.split('_moja')[0][:-5].split('_')[-1]
            name_year = '{}_{}'.format(name,year)
            if int(year) < self.activity_start_year:
                provider_layers.append({
                    "name": name_year,
                    "layer_path": moja_dir,
                    "layer_prefix": basename
                })
                layer_config_names.update({name_year:name_year})
        for moja_dir in glob.glob(r'{}\SCEN_{}\projected_fire_*_moja'.format(tiler_output, self.GCBM_scenarios[scenario])):
            basename = os.path.basename(moja_dir)
            year = basename.split('_moja')[0][-4:]
            name = basename.split('_moja')[0][:-5].split('_')[-1]
            name_year = '{}_{}'.format(name,year)
            if int(year) >= self.activity_start_year:
                provider_layers.append({
                    "name": name_year,
                    "layer_path": moja_dir,
                    "layer_prefix": basename
                })
                layer_config_names.update({name_year:name_year})

        # insect layers
        for moja_dir in glob.glob(r'{}\SCEN_{}\insect_*_moja'.format(tiler_output, self.base_scenario)):
            basename = os.path.basename(moja_dir)
            year = basename.split('_moja')[0][-4:]
            name = basename.split('_moja')[0][:-5].split('_')[-1]
            name_year = '{}_{}'.format(name,year)
            provider_layers.append({
                "name": name_year,
                "layer_path": moja_dir,
                "layer_prefix": basename
            })
            layer_config_names.update({name_year:name_year})

        disturbance_names = [dn for dn in layer_config_names]

        # general layers
        for name in general_lyrs:
            moja_dir = r'{}\SCEN_{}\{}_moja'.format(tiler_output, self.base_scenario, name)
            provider_layers.append({
                "name": name,
                "layer_path": moja_dir,
                "layer_prefix": os.path.basename(moja_dir)
            })
            if name == 'age':
                layer_config_names.update({'initial_age':name})
            elif name == 'NAmerica_MAT_1971_2000':
                layer_config_names.update({'mean_annual_temperature':name})
            elif name == "Eco":
                layer_config_names.update({'eco_boundary':name})
            else:
                layer_config_names.update({name:name})

        # reporting indicators
        reporting_ind = self.reporting_indicators.getIndicators()
        for ri in reporting_ind:
            provider_layers.append({
                "name": ri,
                "layer_path": reporting_ind[ri],
                "layer_prefix": os.path.basename(reporting_ind[ri])
            })
            layer_config_names.update({ri:ri})

        with open(r'{}\05_GCBM_config\GCBM_config_provider.json'.format(sys.path[0]), 'rb') as provider_file:
            config_provider = json.load(provider_file)
        config_provider["Providers"]["SQLite"]["path"] = input_db
        config_provider["Providers"]["RasterTiled"]["cellLatSize"] = self.resolution
        config_provider["Providers"]["RasterTiled"]["cellLonSize"] = self.resolution
        config_provider["Providers"]["RasterTiled"]["layers"] = provider_layers
        output_path = r'{}\SCEN_{}\GCBM_config_provider.json'.format(self.gcbm_configs_dir, scenario)
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
        with open(output_path, 'w') as provider_file:
            json.dump(config_provider, provider_file, sort_keys=True, indent=4)
        logging.info('GCBM config provider generated for scenario {} at {}'.format(scenario, output_path))

        return layer_config_names, disturbance_names

    def configureConfig(self, layer_config_names, disturbance_names, scenario):
        with open(r'{}\05_GCBM_config\GCBM_config.json'.format(sys.path[0]), 'rb') as config_file:
            gcbm_config = json.load(config_file)

        gcbm_config["LocalDomain"]["start_date"] = r'{}/01/01'.format(self.start_year-1)
        gcbm_config["LocalDomain"]["end_date"] = r'{}/01/01'.format(self.end_year+1)

        gcbm_config["LocalDomain"]["landscape"]["tiles"] = self.getTiles()

        for name in layer_config_names:
            data_id = layer_config_names[name]
            gcbm_config["Variables"].update({
                name: {
                    "transform": {
                        "library": "internal.flint",
                        "type": "LocationIdxFromFlintDataTransform",
                        "provider": "RasterTiled",
                        "data_id": data_id
                    }
                }
            })

        classifiers = []
        for classifier in self.inventory.getClassifiers():
            if classifier in [name for name in layer_config_names]:
                classifiers.append(classifier)
            else:
                logging.warning("Classifier '{}' not added to GCBM config".format(classifier))
                print "Warning: Classifier '{}' not added to GCBM config".format(classifier)
        reporting_ind_names = [ri for ri in self.reporting_indicators.getIndicators()]
        gcbm_config["Variables"]["initial_classifier_set"]["transform"]["vars"] = classifiers
        gcbm_config["Variables"]["reporting_classifiers"]["transform"]["vars"] = (
            gcbm_config["Variables"]["reporting_classifiers"]["transform"]["vars"] + reporting_ind_names)
        gcbm_config["Modules"]["CBMDisturbanceEventModule"]["settings"]["vars"] = disturbance_names
        output_directory = self.output_dir
        if not output_directory[0]=='$':
            output_directory = os.path.join(self.output_dir, 'SCEN_{}'.format(scenario))
            if not os.path.exists(output_directory):
                os.makedirs(output_directory)
        gcbm_config["Modules"]["CBMAggregatorSQLiteWriter"]["settings"]["databasename"] = os.path.join(output_directory, 'GCBMoutput.db')
        gcbm_config["Modules"]["WriteVariableGrid"]["settings"]["output_path"] = output_directory
        output_path = r'{}\SCEN_{}\GCBM_config.json'.format(self.gcbm_configs_dir, scenario)
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
        with open(output_path, 'w') as config_file:
            json.dump(gcbm_config, config_file, sort_keys=True, indent=4)
            logging.info('GCBM config generated for scenario {} at {}'.format(scenario, output_path))

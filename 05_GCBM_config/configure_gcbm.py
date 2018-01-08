import os
import glob
import inspect
import json
import sys
import logging
import shutil
import re
from distutils.dir_util import copy_tree
from zipfile import ZipFile

class ConfigureGCBM(object):
    '''
    Configures the GCBM JSONs according to the layers tiled, classifers, reporting indicators,
    start/end years, and activity start year. All moja directories fitting the expected
    naming format within the tiled output layers will be added to the configuration.
    '''
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
        self.tiler_output = tiler_output_dir
        for scen in self.GCBM_scenarios:
            layer_config_names, disturbance_names = self.configureProvider(input_db, general_lyrs, tiler_output_dir, scen)
            self.configureConfig(layer_config_names, disturbance_names, scen)
        pp.finish()

    def replace_params(self, read_file, write_file, replace_d):
        '''
        Copies the file (read_file) to the destination (write_file)
        while replacing occurrences of the input dictionary's (replace_d)
        keys with the corresponding dictionary values.
        This allows for parameterization within the read file.
        Parameter key words can be included in the (text based) read file
        and added to the dictionary 'replace' defined below to be replaced
        by the value upon runtime.
        '''
        with open(read_file, 'r') as read_f:
            with open(write_file, 'w') as write_f:
                for line in read_f:
                    pattern = re.compile("|".join([re.escape(k) for k in replace_d.keys()]))
                    write_f.write(pattern.sub(lambda m: str(replace_d[m.group(0)]), line))

    def replace_params_zip(self, read_file, replace_d):
        '''
        Copies the file (read_file) to the destination (write_file)
        while replacing occurrences of the input dictionary's (replace_d)
        keys with the corresponding dictionary values.
        This allows for parameterization within the read file.
        Parameter key words can be included in the (text based) read file
        and added to the dictionary 'replace' defined below to be replaced
        by the value upon runtime.
        '''
        write_f = []
        for line in read_file.split('\n'):
            pattern = re.compile("|".join([re.escape(k) for k in replace_d.keys()]))
            write_f.append(pattern.sub(lambda m: str(replace_d[m.group(0)]), line))
        return '\n'.join(write_f)

    def copyTilerOutput(self, moja_dir, tiler_scenario, scenario):
        '''
        Copies the tiled layer moja_dir from the tiler scenario to the GCBM scenario
        while replacing any occurences of the tiler scenario clearcut to the GCBM
        scenario clearcut disturbance.
        '''
        tiler_scen_out = os.path.dirname(moja_dir)
        gcbm_scen_moja_dir = os.path.join(os.path.dirname(tiler_scen_out), 'SCEN_{}'.format(scenario), os.path.basename(moja_dir))
        if os.path.exists(gcbm_scen_moja_dir):
            os.remove(gcbm_scen_moja_dir)
        
        if not os.path.exists(os.path.dirname(gcbm_scen_moja_dir)):
            os.makedirs(os.path.dirname(gcbm_scen_moja_dir))
            
        zin = ZipFile(moja_dir, 'r')
        zout = ZipFile(gcbm_scen_moja_dir, 'w')
        replace_d = {'{}{} CC'.format('' if tiler_scenario.lower()=='base' else 'CBM_', tiler_scenario): 'CBM_{} CC'.format(scenario)}
        for item in zin.infolist():
            buffer = zin.read(item.filename)
            if (item.filename.endswith('.json')):
                buffer = self.replace_params_zip(buffer, replace_d)
            zout.writestr(item, buffer)
        zout.close()
        zin.close()

        return gcbm_scen_moja_dir

    def getTiles(self):
        '''
        Explores all directories in the tiler_template_dir and extracts the tile
        x, y from the file name and adds to the list of tiles.
        Assumes a consistent file name format and that the tiler_template_dir
        is not None (at least one tiled disturbance layer was found).
        '''
        tiles_text = []
        z = ZipFile(self.tiler_template_dir)
        dirs = set([os.path.dirname(file) for file in z.namelist()])

        for d in dirs:
            if d != '':
                tiles_text.append(os.path.basename(d).split('_moja_')[-1])
        tiles = []
        for tile_text in tiles_text:
            x, y = tile_text.split('_')
            tiles.append({"x":int(x), "y":int(y)})
        logging.info('Tiles found: {}'.format(tiles))
        return tiles

    def addLayerConfigNamesPreActivity(self, dirs, name):
        '''
        For each directory in dirs (List), adds the disturbance to the provider layers
        for insertion to the config provider JSON and adds the name to the layer
        config names for insertion to the config JSON.
        Only selects disturbances that occur before the activity start year.
        '''
        logging.info('Adding tiled layers for {}'.format(name))
        for moja_dir in dirs:
            if self.tiler_template_dir == None:
                logging.info('Tiler template directory found.')
                self.tiler_template_dir = moja_dir
            basename = os.path.basename(moja_dir).split('.')[0]
            year = basename.split('_moja')[0][-4:]
            name = basename.split('_moja')[0][:-5].split('_')[-1]
            name_year = '{}_{}'.format(name,year)
            if int(year) < self.activity_start_year:
                self.provider_layers.append({
                    "name": name_year,
                    "layer_path": os.path.join('$dir',os.path.relpath(moja_dir.split('.')[0],self.tiler_output)),
                    "layer_prefix": basename
                })
                self.layer_config_names.append([name_year,name_year])

    def addLayerConfigNamesPostActivity(self, dirs, name, tiler_scenario, scenario):
        '''
        For each directory in dirs (List), adds the disturbance to the provider layers
        for insertion to the config provider JSON and adds the name to the layer
        config names for insertion to the config JSON.
        Only selects disturbances that occur at or after the activity start year.
        If the scenario is different from the tiler scenario, the moja_dir will
        be copied and the CC disturbances replaced with the correct scenario.
        '''
        logging.info('Adding tiled layers for {}'.format(name))
        for moja_dir in dirs:
            if self.tiler_template_dir == None:
                logging.info('Tiler template directory found.')
                self.tiler_template_dir = moja_dir
            basename = os.path.basename(moja_dir).split('.')[0]
            year = basename.split('_moja')[0][-4:]
            name = basename.split('_moja')[0][:-5].split('_')[-1]
            name_year = '{}_{}'.format(name,year)
            if int(year) >= self.activity_start_year:
                if scenario != tiler_scenario:
                    moja_dir = self.copyTilerOutput(moja_dir, tiler_scenario, scenario)
                self.provider_layers.append({
                    "name": name_year,
                    "layer_path": os.path.join('$dir',os.path.relpath(moja_dir.split('.')[0],self.tiler_output)),
                    "layer_prefix": basename
                })
                self.layer_config_names.append([name_year,name_year])

    def configureProvider(self, input_db, general_lyrs, tiler_output, scenario):
        '''
        Configures the config provider JSON according to the layers tiled in the
        tiler. Adds all existing layers matching the expected disturbance names
        in the tiler output directory. Writes to the config provider JSON (which
        is stored in the gcbm_configs_dir) each of the provider layers and passes
        the names off for the configureConfig.
        '''
        resolution = self.resolution

        self.provider_layers = []
        self.layer_config_names = []

        # Order: Fire, Insect, Harvest, Slashburn

        # fire layers
        self.addLayerConfigNamesPreActivity((glob.glob(r'{}\SCEN_{}\rollback_fire_*_moja.zip'.format(tiler_output, self.base_scenario))
            +glob.glob(r'{}\SCEN_{}\fire_*_moja.zip'.format(tiler_output, self.base_scenario))
            +glob.glob(r'{}\SCEN_{}\projected_fire_*_moja.zip'.format(tiler_output, self.base_scenario))),
            'fire')
        self.addLayerConfigNamesPostActivity(
            glob.glob(r'{}\SCEN_{}\projected_fire_*_moja.zip'.format(tiler_output, self.GCBM_scenarios[scenario])),
            'proj_fire', self.GCBM_scenarios[scenario], scenario)

        # insect layers
        self.addLayerConfigNamesPreActivity(
            glob.glob(r'{}\SCEN_{}\insect_*_moja.zip'.format(tiler_output, self.base_scenario)),
            'insect')

        # prescribed burn layers for parks
        self.addLayerConfigNamesPreActivity(
            glob.glob(r'{}\SCEN_{}\prescribed_burn_*_moja.zip'.format(tiler_output, self.base_scenario)),
            'prescribed_burn')
            
        # harvest layers
        self.addLayerConfigNamesPreActivity((glob.glob(r'{}\SCEN_{}\rollback_harvest_*_moja.zip'.format(tiler_output, self.base_scenario))
            +glob.glob(r'{}\SCEN_{}\harvest_*_moja.zip'.format(tiler_output, self.base_scenario))
            +glob.glob(r'{}\SCEN_{}\projected_harvest_*_moja.zip'.format(tiler_output, self.base_scenario))),
            'harvest')
        self.addLayerConfigNamesPostActivity(
            glob.glob(r'{}\SCEN_{}\projected_harvest_*_moja.zip'.format(tiler_output, self.GCBM_scenarios[scenario])),
            'proj_harvest', self.GCBM_scenarios[scenario], scenario)

        # slashburn layers
        self.addLayerConfigNamesPreActivity((glob.glob(r'{}\SCEN_{}\rollback_slashburn_*_moja.zip'.format(tiler_output, self.base_scenario))
            +glob.glob(r'{}\SCEN_{}\slashburn_*_moja.zip'.format(tiler_output, self.base_scenario))
            +glob.glob(r'{}\SCEN_{}\projected_slashburn_*_moja.zip'.format(tiler_output, self.base_scenario))),
            'slashburn')
        self.addLayerConfigNamesPostActivity(
            glob.glob(r'{}\SCEN_{}\projected_slashburn_*_moja.zip'.format(tiler_output, self.GCBM_scenarios[scenario])),
            'proj_slashburn', self.GCBM_scenarios[scenario], scenario)

        disturbance_names = [dn[0] for dn in self.layer_config_names]

        # reporting indicators
        reporting_ind = self.reporting_indicators.getIndicators()
        for ri in reporting_ind:
            if reporting_ind[ri]!=None:
                self.provider_layers.append({
                    "name": ri,
                    "layer_path": os.path.join('$dir',os.path.relpath(reporting_ind[ri],self.tiler_output)),
                    "layer_prefix": os.path.basename(reporting_ind[ri])
                })
                self.layer_config_names.append([ri,ri])

        # general layers
        for name in general_lyrs:
            moja_dir = r'{}\SCEN_{}\{}_moja'.format(tiler_output, self.base_scenario, name)
            self.provider_layers.append({
                "name": name,
                "layer_path": os.path.join('$dir',os.path.relpath(moja_dir,self.tiler_output)),
                "layer_prefix": os.path.basename(moja_dir)
            })
            if name == 'age':
                self.layer_config_names.append(['initial_age',name])
            elif name == 'NAmerica_MAT_1971_2000':
                self.layer_config_names.append(['mean_annual_temperature',name])
            elif name == "Eco":
                self.layer_config_names.append(['eco_boundary',name])
            else:
                self.layer_config_names.append([name,name])

        with open(r'{}\05_GCBM_config\GCBM_config_provider.json'.format(sys.path[0]), 'rb') as provider_file:
            config_provider = json.load(provider_file)
        config_provider["Providers"]["SQLite"]["path"] = '$input_db'
        config_provider["Providers"]["RasterTiled"]["cellLatSize"] = self.resolution
        config_provider["Providers"]["RasterTiled"]["cellLonSize"] = self.resolution
        config_provider["Providers"]["RasterTiled"]["layers"] = self.provider_layers
        output_path = r'{}\SCEN_{}\GCBM_config_provider.json'.format(self.gcbm_configs_dir, scenario)
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
        with open(output_path, 'w') as provider_file:
            json.dump(config_provider, provider_file, sort_keys=True, indent=4)
        logging.info('GCBM config provider generated for scenario {} at {}'.format(scenario, output_path))

        return self.layer_config_names, disturbance_names

    def configureConfig(self, layer_config_names, disturbance_names, scenario):
        '''
        Configures the config JSON according to the layers configured in the
        config provider. Sets other variables such as the start year, end year,
        output paths, and reporting indicators. Writes to the config JSON which
        is stored in the gcbm_configs_dir.
        '''
        with open(r'{}\05_GCBM_config\GCBM_config.json'.format(sys.path[0]), 'rb') as config_file:
            gcbm_config = json.load(config_file)

        # parameterize for master batch
        gcbm_config["LocalDomain"]["start_date"] = r'{}/01/01'.format('$start_year') # self.start_year-1)
        gcbm_config["LocalDomain"]["end_date"] = r'{}/01/01'.format('$end_year') # self.end_year+1)

        gcbm_config["LocalDomain"]["landscape"]["tiles"] = self.getTiles()

        for name, data_id in layer_config_names:
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

        inventory_classifiers = set(self.inventory.getClassifiers())
        layer_classifiers = {name for name, _ in layer_config_names}
        missing_classifiers = inventory_classifiers - layer_classifiers
        classifiers = list(inventory_classifiers - missing_classifiers)
        for classifier in list(missing_classifiers):
            logging.warning("Classifier '{}' not added to GCBM config".format(classifier))
            print "Warning: Classifier '{}' not added to GCBM config".format(classifier)
                
        reporting_ind_names = [ri for ri in self.reporting_indicators.getIndicators()]
        gcbm_config["Variables"]["initial_classifier_set"]["transform"]["vars"] = classifiers
        gcbm_config["Variables"]["reporting_classifiers"]["transform"]["vars"] = (
            gcbm_config["Variables"]["reporting_classifiers"]["transform"]["vars"] + reporting_ind_names)
        gcbm_config["Variables"]["admin_boundary"] = self.inventory.getProvince()
        gcbm_config["Modules"]["CBMDisturbanceEventModule"]["settings"]["vars"] = disturbance_names

        output_directory = self.output_dir
        if not output_directory.startswith('$'):
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

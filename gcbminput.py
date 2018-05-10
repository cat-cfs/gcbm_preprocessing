from gcbm.update_gcbm_config import *
from gcbm.recliner2GCBM import Recliner2GCBM
from gcbm.runtiler import RunTiler

from configuration.pathregistry import PathRegistry
from configuration.futureconfig import FutureConfig
from configuration.preprocessorconfig import PreprocessorConfig
from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig
import os, argparse, shutil
from loghelper import *

def runtiler(futureConfig, pathRegistry, subRegionConfig):
    for region in subRegionConfig.GetRegions():
        for scenario in futureConfig.GetScenarios():
            logging.info("tiling {0},{1}".format(region["Name"], scenario["Name"]))
            t = RunTiler()
            outpath = pathRegistry.GetPath(
                "TiledLayersDir", 
                region_path=region["PathName"],
                scenario_name=scenario["Name"])
            transitionRulesOutPath = pathRegistry.GetPath(
                "TransitionRulesPath", 
                region_path=region["PathName"],
                scenario_name=scenario["Name"])
            t.launch(
                config_path = os.path.join(
                    pathRegistry.GetPath(
                        "Pretiled_Layers", 
                        region_path=region["PathName"]),
                        "{}_tiler_config.yaml".format(scenario["Name"])),
                tiler_output_path = outpath,
                transitionRulesPath = transitionRulesOutPath)

def recliner2gcbm(futureConfig, pathRegistry, subRegionConfig):

    exe_paths = [
        os.path.join(pathRegistry.GetPath("Local_Recliner2GCBM-x64_Dir"),"Recliner2GCBM.exe"),
        os.path.join(pathRegistry.GetPath("Local_Recliner2GCBM-x86_Dir"),"Recliner2GCBM.exe")
    ]
    
    for region in subRegionConfig.GetRegions():
        for scenario in futureConfig.GetScenarios():
            logging.info("recliner2gcbm: {0},{1}".format(region["Name"], scenario["Name"]))
            outputPath = pathRegistry.GetPath("Recliner2GCBMOutpath",
                                              region_path=region["PathName"],
                                              scenario_name=scenario["Name"])
            configTemplatePath = pathRegistry.GetPath("Recliner2GCBMConfigTemplate")
            archiveIndexPath = pathRegistry.GetPath("ArchiveIndex")
            yeildTablePath = pathRegistry.GetPath("YieldTable")
            transitionRulesPath = pathRegistry.GetPath("TransitionRulesPath",
                                                       region_path=region["PathName"],
                                                       scenario_name=scenario["Name"])
            r = Recliner2GCBM(exe_paths, configTemplatePath, outputPath,
                              archiveIndexPath, yeildTablePath,
                              transitionRulesPath)
            r.run()

def gcbmconfig(preprocessorConfig, futureConfig, pathRegistry, subRegionConfig, use_relpaths):
    for region in subRegionConfig.GetRegions():
        for scenario in futureConfig.GetScenarios():
            logging.info("gcbm config: {0},{1}".format(region["Name"], scenario["Name"]))
            tiledLayersDir = pathRegistry.GetPath("TiledLayersDir", 
                                 region_path=region["PathName"],
                                 scenario_name=scenario["Name"])
    
            gcbm_provider_template = pathRegistry.GetPath("GCBM_config_provider_template")
            gcbm_config_template = pathRegistry.GetPath("GCBM_config_template")
            configDir = pathRegistry.GetPath("GCBM_Config_Dir",
                                             region_path=region["PathName"],
                                             scenario_name=scenario["Name"])
            gcbm_input_db_path= pathRegistry.GetPath("GCBMInputDBPath",
                                             region_path=region["PathName"],
                                             scenario_name=scenario["Name"])
            if not os.path.exists(configDir):
                os.makedirs(configDir)
    
            gcbm_config = os.path.join(configDir, "GCBM_config.json")
            gcbm_provider = os.path.join(configDir, "GCBM_config_provider.json")
            shutil.copy(gcbm_config_template, gcbm_config)
            shutil.copy(gcbm_provider_template, gcbm_provider)
    
            gcbm_output_db_path = pathRegistry.GetPath(
                "GCBM_OutputDB_Path",
                region_path=region["PathName"],
                scenario_name=scenario["Name"])
    
            gcbm_output_variable_grid_dir = pathRegistry.GetPath(
                "GCBM_Variable_Grid_Output_Dir",
                region_path=region["PathName"],
                scenario_name=scenario["Name"])
    
            study_area = get_study_area(tiledLayersDir)

            reporting_classifiers = preprocessorConfig.GetReportingClassifiers().keys()
            reporting_classifiers.extend(
                preprocessorConfig.GetDefaultSpatialBoundaries(
                    region_path=region["PathName"])["Attributes"].keys())
            update_gcbm_config(gcbm_config, study_area,
                               start_year = preprocessorConfig.GetHistoricRange()["StartYear"],
                               end_year = futureConfig.GetEndYear(),
                               classifiers = preprocessorConfig.GetInventoryClassifiers().keys(),
                               reporting_classifiers = reporting_classifiers,
                               output_db_path = gcbm_output_db_path,
                               variable_grid_output_dir = gcbm_output_variable_grid_dir,
                               output_relpaths = use_relpaths)
    
            update_provider_config(gcbm_provider, study_area,
                                   tiledLayersDir, gcbm_input_db_path,
                                   use_relpaths)

def main():

    create_script_log(sys.argv[0])
    try:
        parser = argparse.ArgumentParser(description="prepares gcbm configuration files")
        parser.add_argument("--pathRegistry", help="path to file registry data")
        parser.add_argument("--preprocessorConfig", help="path to preprocessor configuration")
        parser.add_argument("--futureConfig", help="path to configuration")
        parser.add_argument("--subRegionConfig", help="path to sub region data")
        parser.add_argument("--subRegionNames", help="optional comma delimited "+
                            "string of sub region names (as defined in "+
                            "subRegionConfig) to process, if unspecified all "+
                            "regions will be processed")
        parser.add_argument("--tiler", action="store_true", dest="tiler", help="if specified, run the tiler")
        parser.add_argument("--recliner2gcbm", action="store_true", dest="recliner2gcbm", help="if specified, run recliner2gcbm")
        parser.add_argument("--gcbmconfig", action="store_true", dest="gcbmconfig", help="if specified, run gcbmconfig")
        parser.add_argument("--gcbmconfig_abspaths", action="store_true", dest="gcbmconfig_abspaths", help=
                            "if specified all gcbm related paths are interpreted and stored as absolute paths "
                            "in gcbm configurations, otherwise if unspecified, all paths are assumed to be "
                            "relative to gcbm configuration directory")
        parser.set_defaults(tiler=False, recliner2gcbm=False, gcbmconfig=False, gcbmconfig_abspaths=False)
        args = parser.parse_args()

        pathRegistry = PathRegistry(os.path.abspath(args.pathRegistry))
        subRegionConfig = SubRegionConfig(
            os.path.abspath(args.subRegionConfig),
            args.subRegionNames.split(",") if args.subRegionNames else None)
        futureConfig = FutureConfig(os.path.abspath(args.futureConfig))
        preprocessorConfig = PreprocessorConfig(args.preprocessorConfig, pathRegistry)

        if not args.tiler \
           and not args.recliner2gcbm \
           and not args.gcbmconfig:
            logging.error("nothing to do")

        if args.tiler:
            runtiler(futureConfig, pathRegistry, subRegionConfig)
        if args.recliner2gcbm:
            recliner2gcbm(futureConfig, pathRegistry, subRegionConfig)
        if args.gcbmconfig:
            gcbmconfig(preprocessorConfig, futureConfig, pathRegistry, subRegionConfig, not(args.gcbmconfig_abspaths))

    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all gcbminput tasks finished")

if __name__ == "__main__":
    main()

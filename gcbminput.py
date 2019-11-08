from gcbm.runtiler import RunTiler

from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig
import os, argparse, shutil, sys
from loghelper import *

def runtiler(pathRegistry, subRegionConfig, tiler_config_type):
    for region in subRegionConfig.GetRegions():
        logging.info("tiling {0},{1}".format(region["Name"]))
        t = RunTiler()
        outpath = pathRegistry.GetPath(
            "TiledLayersDir", 
            region_path=region["PathName"])
        transitionRulesOutPath = pathRegistry.GetPath(
            "TransitionRulesPath", 
            region_path=region["PathName"])
        t.launch(
            config_path = os.path.join(
                pathRegistry.GetPath(
                    "Pretiled_Layers", 
                    region_path=region["PathName"]),
                    "{}_tiler_config.yaml".format(tiler_config_type)),
            tiler_output_path = outpath,
            transitionRulesPath = transitionRulesOutPath)

def main():

    create_script_log(sys.argv[0])
    try:
        parser = argparse.ArgumentParser(description="prepares gcbm configuration files")
        parser.add_argument("--pathRegistry", help="path to file registry data")
        parser.add_argument("--subRegionConfig", help="path to sub region data")
        parser.add_argument("--subRegionNames", help="optional comma delimited "+
                            "string of sub region names (as defined in "+
                            "subRegionConfig) to process, if unspecified all "+
                            "regions will be processed")
        parser.add_argument("--tiler_config_type", help="pass the name/type of the tiler config to use, in place of scenario")
        parser.add_argument("--tiler", action="store_true", dest="tiler", help="if specified, run the tiler")
        parser.set_defaults(tiler=False)
        args = parser.parse_args()

        pathRegistry = PathRegistry(os.path.abspath(args.pathRegistry))
        subRegionConfig = SubRegionConfig(
            os.path.abspath(args.subRegionConfig),
            args.subRegionNames.split(",") if args.subRegionNames else None)

        tiler_config_type = args.tiler_config_type

        if not args.tiler:
            logging.error("nothing to do")

        if args.tiler:
            runtiler(pathRegistry, subRegionConfig, tiler_config_type)

    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all gcbminput tasks finished")

if __name__ == "__main__":
    main()

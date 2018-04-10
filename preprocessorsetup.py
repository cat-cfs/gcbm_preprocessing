from loghelper import *
import os, sys, argparse, shutil, zipfile

from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig
def main():

    create_script_log(sys.argv[0])
    try:
        parser = argparse.ArgumentParser(description="sets up external data in working directory for subsequent processes")
        parser.add_argument("--pathRegistry", help="path to file registry data")
        parser.add_argument("--subRegionConfig", help="path to sub region data")
        parser.add_argument("--subRegionNames", help="optional comma delimited "+
                            "string of sub region names (as defined in "+
                            "subRegionConfig) to process, if unspecified all "+
                            "regions will be processed")
        parser.add_argument("--spatial", action="store_true", dest="spatial", help="copy spatial files to the working dir")
        parser.add_argument("--future", action="store_true", dest="future", help="copys future projection files to the working dir")
        parser.add_argument("--aspatial", action="store_true", dest="aspatial", help="copy aspatial files to the working dir")
        parser.add_argument("--tools", action="store_true", dest="tools", help="copy tools to the working dir")
        parser.set_defaults(spatial=False)
        parser.set_defaults(aspatial=False)
        parser.set_defaults(tools=False)
        args = parser.parse_args()

        pathRegistry = PathRegistry(os.path.abspath( args.pathRegistry))
        subRegionConfig = SubRegionConfig(
            os.path.abspath(args.subRegionConfig),
            args.subRegionNames.split(',') if args.subRegionNames else None)

        if not args.spatial \
           and not args.aspatial \
           and not args.tools \
           and not args.future:
            logging.error("nothing to do")

        if args.aspatial:
            src = pathRegistry.GetPath("Source_External_Aspatial_Dir")
            dst = pathRegistry.GetPath("External_Aspatial_Dir")
            logging.info("copying external aspatial data to local working directory")
            logging.info("source: {}".format(src))
            logging.info("destination: {}".format(dst))
            shutil.copytree(src=src, dst=dst)

        if args.tools:
            toolPathPairs = [("Source_GCBM_Dir", "Local_GCBM_Dir"),
                             ("Source_Recliner2GCBM-x64_Dir", "Local_Recliner2GCBM-x64_Dir"),
                             ("Source_Recliner2GCBM-x86_Dir", "Local_Recliner2GCBM-x86_Dir")]
            for pair in toolPathPairs:
                src = pathRegistry.GetPath(pair[0])
                dst = pathRegistry.GetPath(pair[1])
                logging.info("copying external tool from {} to {}".format(pair[0],pair[1]))
                logging.info("source: {}".format(src))
                logging.info("destination: {}".format(dst))
                shutil.copytree(src=src,dst=dst)

        if args.future:
            for region in subRegionConfig.GetRegions():
                src = pathRegistry.GetPath("Source_External_Future_Dir",
                                           future_scenario_zip=region["FutureScenarioZip"])
                dest = pathRegistry.GetPath("Future_Dist_Input_Dir",
                                            region_path=region["PathName"])

                with zipfile.ZipFile(src, 'r') as z:
                    if not os.path.exists(dest):
                        os.makedirs(dest)
                    logging.info("unzipping future project files to local working directory")
                    logging.info("source: {} ".format(src))
                    logging.info("destination dir: {}".format(dest))
                    # see: https://stackoverflow.com/questions/4917284/extract-files-from-zip-without-keeping-the-structure-using-python-zipfile
                    for f in z.namelist():
                        filename = os.path.basename(f)
                        if not filename:
                            continue
                        srcFile = z.open(f)
                        destFile = file(os.path.join(dest, filename), 'wb')
                        with srcFile, destFile:
                            shutil.copyfileobj(srcFile, destFile)

        if args.spatial:
            src = pathRegistry.GetPath("Source_External_Spatial_Dir")
            dst = pathRegistry.GetPath("External_Spatial_Dir")
            logging.info("copying external spatial data to local working directory")
            logging.info("source: {}".format(src))
            logging.info("destination: {}".format(dst))
            shutil.copytree(src=src, dst=dst)



    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all setup tasks finished")

if __name__ == "__main__":
    main()

from loghelper import *
import os, argparse, shutil

from configuration.pathregistry import PathRegistry
def main():

    create_script_log(sys.argv[0])
    try:
        parser = argparse.ArgumentParser(description="sets up external data in working directory for subsequent processes")
        parser.add_argument("--pathRegistry", help="path to file registry data")
        parser.add_argument("--spatial", dest="spatial", help="copy spatial files to the working dir")
        parser.add_argument("--aspatial", dest="aspatial", help="copy aspatial files to the working dir")
        parser.add_argument("--tools", dest="tools", help="copy tools to the working dir")
        parser.set_defaults(spatial=False)
        parser.set_defaults(aspatial=False)
        parser.set_defaults(tools=False)
        args = parser.parse_args()

        pathRegistry = PathRegistry(os.path.abspath( args.pathRegistry))
        
        if not args.spatial and not args.aspatial and not args.tools:
            logging.error("nothing to do")

        if args.spatial:
            src = pathRegistry.GetPath("Source_External_Spatial_Dir")
            dst = pathRegistry.GetPath("External_Spatial_Dir")
            logging.info("copying external spatial data to local working directory")
            shutil.copytree(src=src, dst=dst)

        if args.aspatial:
            src = pathRegistry.GetPath("Source_External_Aspatial_Dir")
            dst = pathRegistry.GetPath("External_Aspatial_Dir")
            logging.info("copying external aspatial data to local working directory")
            shutil.copytree(src=src, dst=dst)

        if args.tools:
            pass

    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all setup tasks finished")

if __name__ == "__main__":
    main()

from loghelper import *
import os, argparse, shutil

from configuration.pathregistry import PathRegistry
def main():

    create_script_log(sys.argv[0])
    try:
        parser = argparse.ArgumentParser(description="sets up external data in working directory for subsequent processes")
        parser.add_argument("--pathRegistry", help="path to file registry data")

        args = parser.parse_args()

        pathRegistry = PathRegistry(os.path.abspath( args.pathRegistry))
        src = pathRegistry.GetPath("Source_External_Spatial_Dir")
        dst = pathRegistry.GetPath("External_Data_Dir")
        logging.info("copying external data to local working directory")
        shutil.copytree(src=src, dst=dst)


    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all setup tasks finished")

if __name__ == "__main__":
    main()

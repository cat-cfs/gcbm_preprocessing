from configuration.pathregistry import PathRegistry

class Recliner2GCBM(object):
    def __init__(self, config_dir, output_path, exe_path=None):
        logging.info("Initializing class {}".format(self.__class__.__name__))
        self.ProgressPrinter = ProgressPrinter
        self.exe_paths = [exe_path] or [
            os.path.join("M:", "Spatially_explicit", "03_Tools", "Recliner2GCBM-{}".format(platform), "Recliner2GCBM.exe")
            for platform in ("x64", "x86")]
            
        self.config_dir = config_dir
        self.output_path = output_path
        self.transition_rules = transitionRules
        self.yield_table = yieldTable
        self.aidb = aidb

    def run(self):
        for exe_path in self.exe_paths:
            command = [exe_path, "-c", config_path]
            try:
                subprocess.check_call(command)
                logging.info("Found and ran '{}'".format(" ".join(command)))
                break
            except Exception as e:
                logging.error("Failed to run '{}': {}".format(" ".join(command), e))
def main():

    create_script_log(sys.argv[0])
    try:
        parser = argparse.ArgumentParser(description="sets up external data in working directory for subsequent processes")
        parser.add_argument("--pathRegistry", help="path to file registry data")

        args = parser.parse_args()

        pathRegistry = PathRegistry(os.path.abspath(args.pathRegistry))
        
        if not args.spatial and not args.aspatial:
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

    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all setup tasks finished")

if __name__ == "__main__":
    main()
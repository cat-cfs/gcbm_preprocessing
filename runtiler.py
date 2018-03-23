import os, argparse
from loghelper import *
from mojadata.layer.gcbm.transitionrulemanager import SharedTransitionRuleManager
from mojadata.cleanup import cleanup
from configuration.tilerconfig import TilerConfig

class RunTiler(object):
    
    def launch(self, config_path, tiler_output_path, transitionRulesPath=None):
        if not os.path.exists(tiler_output_path):
            os.makedirs(tiler_output_path)
        mgr = SharedTransitionRuleManager()
        mgr.start()

        transitionRulesPath = transitionRulesPath if transitionRulesPath else \
            os.path.join(tiler_output_path, "transition_rules.csv")

        rule_manager = mgr.TransitionRuleManager(transitionRulesPath)

        absPathInjection = lambda relpath : os.path.abspath(
            os.path.join(os.path.dirname(config_path), relpath))

        objectArgInjections = {
            "DisturbanceLayer": {
                "transition_rule_manager": lambda : rule_manager
            },
            "VectorLayer": {
                "path": absPathInjection
            },
            "RasterLayer": {
                "path": absPathInjection
            },
            "Attribute": { # unicode not supported for attribute names
                "layer_name": lambda name : name.encode("ascii","ignore")
            }
        }
        cwd = os.getcwd()
        os.chdir(tiler_output_path)
        config = TilerConfig(config_path)

        tiler = config.AssembleTiler(objectArgInjections)
        layers = config.AssembleLayers(objectArgInjections)
        with cleanup():
            tiler.tile(layers)
            rule_manager.write_rules()
        os.chdir(cwd)

def main():

    create_script_log(sys.argv[0])
    try:
        parser = argparse.ArgumentParser(description="rollback")
        parser.add_argument("--tilerConfig", help="path to a tiler config json file")
        parser.add_argument("--outputPath", help="path to preprocessor configuration")
        parser.add_argument("--transitionRulesOutPath", help="path to sub region data (optional, if unspecified a default value is used)")

        args = parser.parse_args()
        config_path = os.path.abspath(args.tilerConfig)
        tiler_output_path = os.path.abspath(args.outputPath)
        transitionRulesPath = os.path.abspath(args.transitionRulesOutPath) \
           if args.transitionRulesOutPath else None

        r = RunTiler()

        r.launch(
            config_path = config_path,
            tiler_output_path = tiler_output_path,
            transitionRulesPath = transitionRulesPath)

    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all tiler tasks finished")


if __name__ == "__main__":
    main()
import os, argparse
from loghelper import *
from mojadata.layer.gcbm.transitionrulemanager import SharedTransitionRuleManager
from configuration.tilerconfig import TilerConfig

class RunTiler(object):
    def launch(self, config_path, tiler_output_path, transitionRulesPath):
        mgr = SharedTransitionRuleManager()
        mgr.start()
        rule_manager = mgr.TransitionRuleManager(transitionRulesPath) #"transition_rules.csv")

        absPathInjection = lambda relpath : os.path.abspath(os.path.join(os.path.dirname(config_path), relpath))

        objectArgInjections = {
            "DisturbanceLayer": {
                "transition_rule_manager": lambda : rule_manager
            },
            "VectorLayer": {
                "path": absPathInjection
            },
            "RasterLayer": {
                "path": absPathInjection
            }
        }
        if not os.path.exists(tiler_output_path):
            os.makedirs(tiler_output_path)
        os.chdir(tiler_output_path)
        config = TilerConfig(config_path)
        tiler = config.AssembleTiler(objectArgInjections)
        layers = config.AssembleLayers(objectArgInjections)
        tiler.tile(layers)

def main():

    create_script_log(sys.argv[0])
    try:
        parser = argparse.ArgumentParser(description="rollback")
        parser.add_argument("--tilerConfig", help="path to file registry data")
        parser.add_argument("--outputPath", help="path to preprocessor configuration")
        parser.add_argument("--transitionRulesOutPath", help="path to sub region data")

        r = RunTiler()
        r.launch(
            config_path = r"C:\Dev\Scott\gcbm_test_dir\05_working_BC\TSA_2_Boundary\01a_pretiled_layers\historic_tiler_config.json",
            tiler_output_path = r"C:\Dev\Scott\gcbm_test_dir\05_working_BC\TSA_2_Boundary\tiled_layers\test_output",
            transitionRulesPath = "transitionRules.csv")
    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all tiler tasks finished")


if __name__ == "__main__":
    main()
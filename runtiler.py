import os
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
    r = RunTiler()
    r.launch(config_path = r"F:\GCBM\17_BC_ON_1ha\05_working_BC\TSA_2_Boundary\01a_pretiled_layers\historic_tiler_config.json",
             tiler_output_path = r"F:\GCBM\17_BC_ON_1ha\05_working_BC\TSA_2_Boundary\01b_tiled_layers\test_output",
             transitionRulesPath = "transitionRules.csv")


if __name__ == "__main__":
    main()
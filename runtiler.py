import os
from mojadata.layer.gcbm.transitionrulemanager import SharedTransitionRuleManager
from configuration.tilerconfig import TilerConfig

class RunTiler(object):
    def launch(self, config_path, transitionRulesPath):
        mgr = SharedTransitionRuleManager()
        mgr.start()
        rule_manager = mgr.TransitionRuleManager(transitionRulesPath) #"transition_rules.csv")
        objectArgInjections = {
            "DisturbanceLayer": {
                "transition_rule_manager": rule_manager
                }
            }
        os.chdir(r"F:\GCBM\17_BC_ON_1ha\05_working_BC\TSA_2_Boundary\01a_pretiled_layers")
        config = TilerConfig(config_path)
        tiler = config.AssembleTiler(objectArgInjections)
        layers = config.AssembleLayers(objectArgInjections)

def main():
    r = RunTiler()
    r.launch(r"F:\GCBM\17_BC_ON_1ha\05_working_BC\TSA_2_Boundary\01a_pretiled_layers\historic_tiler_config.json",
             "transitionRules.csv")


if __name__ == "__main__":
    main()
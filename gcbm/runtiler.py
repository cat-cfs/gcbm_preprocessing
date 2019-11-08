import os, argparse
from loghelper import *
from mojadata.layer.gcbm.transitionrulemanager import SharedTransitionRuleManager
from mojadata.cleanup import cleanup
from tilerconfig import TilerConfig

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

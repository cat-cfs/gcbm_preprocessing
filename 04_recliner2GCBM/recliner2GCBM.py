import csv
import json
import os
import subprocess
import inspect
import logging

class Recliner2GCBM(object):
    def __init__(self, config_dir, output_path, transitionRules, yieldTable, aidb, ProgressPrinter, exe_path=None):
        logging.info("Initializing class {}".format(self.__class__.__name__))
        self.ProgressPrinter = ProgressPrinter
        if exe_path==None:
            self.exe_path = r"M:\Spatially_explicit\03_Tools\Recliner2GCBM-x64\Recliner2GCBM.exe"
            self.exe_path_32 = r'M:\Spatially_explicit\03_Tools\Recliner2GCBM-x86\Recliner2GCBM.exe'
        else:
            self.exe_path = exe_path
        self.config_dir = config_dir
        self.output_path = output_path
        self.transition_rules = transitionRules
        self.yield_table = yieldTable
        self.aidb = aidb

    def runRecliner2GCBM(self, custom_settings=None):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1).start()
        default_config = {
            "Project":{
                "Mode":0,
                "Configuration":0
            },
            "OutputPath":self.output_path,
            "AIDBPath":self.aidb.getPath(),
            "ClassifierSet":[
                # {
                #     "Name":"AU",
                #     "Path":"H:\\Nick\\GCBM\\00_Testing\\05_working\\01_configs\\Recliner2GCBM\\yield.csv",
                #     "Page":0,
                #     "Column":0,
                #     "Header":true
                # },
                # {
                #     "Name":"LDSPP",
                #     "Path":"H:\\Nick\\GCBM\\00_Testing\\05_working\\01_configs\\Recliner2GCBM\\yield.csv",
                #     "Page":0,
                #     "Column":0,
                #     "Header":true
                # }
            ],
            "GrowthCurves":{
                "Path":self.yield_table.getPath(),
                "Page":0,
                "Header":self.yield_table.isHeader(),
                "SpeciesCol":self.yield_table.getSpeciesCol(),
                "IncrementStartCol":self.yield_table.getIncrementRange()[0],
                "IncrementEndCol":self.yield_table.getIncrementRange()[1],
                "Interval":self.yield_table.getInterval(),
                "Classifiers":[
                    # {
                    #     "Name":"AU",
                    #     "Column":0
                    # },
                    # {
                    #     "Name":"LDSPP",
                    #     "Column":1
                    # }
                ]
            },
            "TransitionRules":{
                "Path":self.transition_rules.getPath(),
                "Page":0,
                "Header":self.transition_rules.isHeader(),
                "NameCol":self.transition_rules.getNameCol(),
                "AgeCol":self.transition_rules.getAgeCol(),
                "DelayCol":self.transition_rules.getDelayCol(),
                "Classifiers":[
                    # {
                    #     "Name":"AU",
                    #     "Column":3
                    # },
                    # {
                    #     "Name":"LDSPP",
                    #     "Column":4
                    # }
                ]
            }
        }

        for classifier in self.yield_table.getClassifiers():
            default_config["ClassifierSet"].append(
                {
                    "Name": classifier,
                    "Path": self.yield_table.getPath(),
                    "Page": 0,
                    "Column": self.yield_table.getClassifierCol(classifier),
                    "Header": self.yield_table.isHeader()
                }
            )
            default_config["GrowthCurves"]["Classifiers"].append(
                {
                    "Name": classifier,
                    "Column": self.yield_table.getClassifierCol(classifier)
                }
            )
            default_config["TransitionRules"]["Classifiers"].append(
                {
                    "Name": classifier,
                    "Column": self.transition_rules.getClassifierCol(classifier)
                }
            )
        if custom_settings!=None:
            default_config = default_config.update(custom_settings)
        config_path = os.path.join(self.config_dir, "recliner2GCBM_config.json")
        with open(config_path, "w") as config:
            json.dump(default_config, config)
            logging.info('Recliner2GCBM config json created at {}'.format(config_path))
        try:
            run = subprocess.Popen([self.exe_path, "-c", config_path])
            run.communicate()
        except:
            try:
                run = subprocess.Popen([self.exe_path_32, "-c", config_path])
                run.communicate()
            except:
                print "Recliner2GCBM Failed"
                raise

        pp.finish()

    def prepTransitionRules(self, transitionRules):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1).start()
        out = os.path.join(self.config_dir, os.path.basename(transitionRules.getPath()))
        with open(transitionRules.getPath(), "r") as transitionRules_in, open(out, "w") as transitionRules_out:
            reader = csv.reader(transitionRules_in)
            writer = csv.writer(transitionRules_out, lineterminator="\n")
            all_rows = []
            if transitionRules.isHeader():
                try:
                    header = reader.next()
                except StopIteration as e:
                    header = ["id", "regen_delay", "age_after"]
                for classifier in [c for c in transitionRules.getClassifiers() if transitionRules.getClassifierCol(c)==None]:
                    transitionRules.setClassifierCol({classifier: len(header)})
                    header.append(classifier)
                all_rows.append(header)
            for row in reader:
                for _ in transitionRules.getClassifiers():
                    row.append("?")
                all_rows.append(row)
            writer.writerows(all_rows)
        transitionRules.setPath(out)
        self.transition_rules = transitionRules
        logging.info('Transition rules prepped and saved to {}'.format(out))
        pp.finish()
        return transitionRules

    def prepYieldTable(self, yieldTable):
        return yieldTable

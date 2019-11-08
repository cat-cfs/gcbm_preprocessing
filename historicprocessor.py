from loghelper import *

import argparse, sys
from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig
from configuration.preprocessorconfig import PreprocessorConfig
from historic.historic_tiler_config import HistoricTilerConfig
from preprocess_tools import postgis_manage

class Historic(object):
    """
    computes historic slashburn as a proportion of the historical harvest
    appends to tiler configuration with the historical layers
    """
    def __init__(self, preprocessorConfig):
        self.preprocessorConfig = preprocessorConfig

    def Process(self, region_path, db_url, gdal_con):
        #load the rollback tiler config path. We will append to a copy of this.
        input_path = self.preprocessorConfig.GetRollbackTilerConfigPath(region_path)
        output_path = self.preprocessorConfig.GetHistoricTilerConfigPath(region_path)
        tilerConfig = HistoricTilerConfig(
            input_path=input_path,
            output_path=output_path)

        classifiers = list(self.preprocessorConfig.GetInventoryClassifiers().keys())

        tilerConfig.AddSplitDisturbanceLayers(
           layerData = self.preprocessorConfig.GetHistoricFireDisturbances(region_path),
           first_year = self.preprocessorConfig.GetHistoricRange()["StartYear"],
           last_year = self.preprocessorConfig.GetHistoricRange()["EndYear"],
           classifiers=classifiers)

        tilerConfig.AddSplitDisturbanceLayers(
           layerData = self.preprocessorConfig.GetHistoricHarvestDisturbances(region_path),
           first_year = self.preprocessorConfig.GetHistoricRange()["StartYear"],
           last_year = self.preprocessorConfig.GetHistoricRange()["EndYear"],
           classifiers=classifiers)

        tilerConfig.Save()
        return output_path

def main(): 

    create_script_log(sys.argv[0])
    try:
        parser = argparse.ArgumentParser(description="historic processor: processes inputs for the tiler for the historic portion of simulations")
        parser.add_argument("--pathRegistry", help="path to file registry data")
        parser.add_argument("--preprocessorConfig", help="path to preprocessor config")
        parser.add_argument("--subRegionConfig", help="path to sub region data")
        parser.add_argument("--subRegionNames", help="optional comma delimited "+
                            "string of sub region names (as defined in "+
                            "subRegionConfig) to process, if unspecified all "+
                            "regions will be processed")
        parser.set_defaults(runtiler=False)

        args = parser.parse_args()

        pathRegistry = PathRegistry(os.path.abspath(args.pathRegistry))
        preprocessorConfig = PreprocessorConfig(os.path.abspath(args.preprocessorConfig),
                                        pathRegistry)


        subRegionConfig = SubRegionConfig(
            os.path.abspath(args.subRegionConfig),
            args.subRegionNames.split(",") if args.subRegionNames else None)

        historic = Historic(preprocessorConfig)
        for r in subRegionConfig.GetRegions():
            logging.info(r["Name"])
            region_path = r["PathName"]
            region_postgis_var_path = pathRegistry.GetPath(
                "PostGIS_Region_Connection_Vars",
                region_path=region_path)

            db_url = postgis_manage.get_url(region_postgis_var_path)
            gdal_con = postgis_manage.get_gdal_conn_string(region_postgis_var_path)
            tilerConfigPath = historic.Process(region_path, db_url, gdal_con)

            #postgis_manage.drop_working_db(
            #        pathRegistry.GetPath("PostGIS_Connection_Vars"),
            #        region_postgis_var_path)

    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all historic tasks finished")

if __name__ == "__main__":
    main()

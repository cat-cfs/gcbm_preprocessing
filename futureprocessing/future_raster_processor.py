import os, shutil, logging
from random_raster_subset import RandomRasterSubset

class FutureRasterProcessor(object):
    def __init__(self, base_raster_dir, years, output_dir,
                 fire_name, harvest_name, slashburn_name,
                 fire_format, harvest_format, slashburn_format):
        self.years = years
        self.base_raster_dir = base_raster_dir
        self.output_dir = output_dir

        self.fire_format = fire_format
        self.harvest_format = harvest_format
        self.slashburn_format = slashburn_format

        self.fire_name = fire_name
        self.harvest_name = harvest_name
        self.slashburn_name = slashburn_name

        self.base_paths = {
            fire_name: {},
            harvest_name: {},
        }
        for year in years:
            self.base_paths[fire_name][year] = self._getValidPath(self.fire_format, year)
            self.base_paths[harvest_name][year] = self._getValidPath(self.harvest_format, year)

    def createProcessedRasterResult(self, year, path, disturbance_name):
        return {
            "Year": year,
            "Path": path,
            "DisturbanceName": disturbance_name
            }

    def _getValidPath(self, format, year):
        path = os.path.join(
            self.base_raster_dir,
            format.format(year))
        if not os.path.exists(path):
            raise ValueError("path does not exist {}"
                                .format(path))
        return path


    def processSlashburn(self, percent, activityStartYear, activityPercent, random_subset):
        """
        param percent the percentage of harvest for slashburn prior to the activity start year
        param activityStartYear the year at which activity_percent is used to override percent
        param activityPercent the percentage of harvest for slashburn starting in the activityStartYear
        param random_subset instance of RandomRasterSubset to process rasters
        """

        logging.info("processing future slashburn")
        result = []
        for year in self.years:
            harvest_raster_scenario_path = os.path.join(self.output_dir, 
                                                        self.harvest_format.format(year))
            if not os.path.exists(harvest_raster_scenario_path):
                raise ValueError("harvest scenarios must be processed before slashburn")
            slashburn_path = os.path.join(self.output_dir, self.slashburn_format.format(year))
            if year >= activityStartYear:
                percent = activityPercent

            random_subset.RandomSubset(input = harvest_raster_scenario_path,
                                       output = slashburn_path,
                                       percent = percent)
            result.append(
                self.createProcessedRasterResult(
                    year = year,
                    path = slashburn_path,
                    disturbance_name = self.slashburn_name))
        return result

    def processHarvest(self, activityStartYear, activityPercent, random_subset):
        """
        param activityStartYear the year at which activity_percent is used on
              base harvest.  For years less than activityStartYear the base raster is copied.
        param activityPercent the percent of base for the activity
        param random_subset instance of RandomRasterSubset to process rasters
        """
        logging.info("processing future harvest")
        result = []
        for year in self.years:
            harvest_raster_base_path = self.base_paths["harvest"][year]
            harvest_raster_scenario_path = os.path.join(self.output_dir, 
                                                        self.harvest_format.format(year))
            if year >= activityStartYear:
                random_subset.RandomSubset(
                    input = harvest_raster_base_path,
                    output = harvest_raster_scenario_path,
                    percent = activityPercent)
            else:
                shutil.copy(harvest_raster_base_path,
                            harvest_raster_scenario_path)
            result.append(
                self.createProcessedRasterResult(
                    year = year,
                    path = harvest_raster_scenario_path,
                    disturbance_name = self.harvest_name))
        return result

    def processFire(self):
        """copies fire rasters to the scenario dir"""

        logging.info("copying base fire rasters to scenario dir")
        result = []
        for year in self.years:
            fire_raster_base_path = self.base_paths["fire"][year]
            fire_raster_scenario_path = os.path.join(self.output_dir, 
                                                     self.fire_format.format(year))
            shutil.copy(fire_raster_base_path,
                        fire_raster_scenario_path)
            result.append(
                self.createProcessedRasterResult(
                    year = year,
                    path = fire_raster_scenario_path,
                    disturbance_name = self.fire_name))
        return result

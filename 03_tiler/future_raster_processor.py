import os, shutil, logging
from randomrastersubset import RandomRasterSubset

class FutureRasterProcessor(object):
    def __init__(self, base_raster_dir, years, output_dir):
        self.years = years
        self.base_raster_dir = base_raster_dir
        self.output_dir = output_dir
        self.fire_format = "projected_fire_{year}.tif"
        self.harvest_format = "projected_harvest_{year}.tif"
        self.slashburn_format = "projected_slashburn_{year}.tif"

        self.base_paths = {
            "fire": {},
            "harvest": {},
        }
        for year in years:
            self.base_paths["fire"][year] = self._getValidPath(self.fire_format, year)
            self.base_paths["harvest"][year] = self._getValidPath(self.harvest_format, year)

    def _getValidPath(self, format, year):
        path = os.path.join(
            self.base_raster_dir,
            format.format(year=year))
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
        for year in self.years:
            harvest_raster_scenario_path = os.path.join(self.output_dir, 
                                                        self.harvest_format.format(year=year))
            if not os.path.exists(harvest_raster_scenario_path):
                raise ValueError("harvest scenarios must be processed before slashburn")
            slashburn_path = os.path.join(self.output_dir, self.slashburn_format.format(year=year))
            if year >= activityStartYear:
                percent = activityPercent

            random_subset.RandomSubset(input = harvest_raster_scenario_path,
                                       output = slashburn_path,
                                       percent = percent)

    def processHarvest(self, activityStartYear, activityPercent, random_subset):
        """
        param activityStartYear the year at which activity_percent is used on
              base harvest.  For years less than activityStartYear the base raster is copied.
        param activityPercent the percent of base for the activity
        param random_subset instance of RandomRasterSubset to process rasters
        """
        logging.info("processing future harvest")
        for year in self.years:
            harvest_raster_base_path = self.base_paths["harvest"][year]
            harvest_raster_scenario_path = os.path.join(self.output_dir, 
                                                        self.harvest_format.format(year=year))
            if year >= activityStartYear:
                random_subset.RandomSubset(
                    input = harvest_raster_base_path,
                    output = harvest_raster_scenario_path,
                    percent = activityPercent)
            else:
                shutil.copy(harvest_raster_base_path,
                            harvest_raster_scenario_path)

    def processFire(self):
        """copies fire rasters to the scenario dir"""

        logging.info("copying base fire rasters to scenario dir")
        for year in self.years:
            fire_raster_base_path = self.base_paths["fire"][year]
            fire_raster_scenario_path = os.path.join(self.output_dir, 
                                                     self.fire_format.format(year=year))
            shutil.copy(fire_raster_base_path,
                        fire_raster_scenario_path)

f = FutureRasterProcessor(
    r"F:\GCBM\17_BC_ON_1ha\05_working_BC\TSA_2_Boundary\01a_pretiled_layers\03_disturbances\02_future\inputs\base",
    list(range(2015, 2075)),
    r"F:\GCBM\17_BC_ON_1ha\05_working_BC\TSA_2_Boundary\01a_pretiled_layers\03_disturbances\02_future\outputs\base")


import time
t0 = time.time()
f.processFire()
f.processHarvest(2040, 50, RandomRasterSubset())
f.processSlashburn(50, 2040, 100, RandomRasterSubset()) 
t1 = time.time()
print(t1-t0)
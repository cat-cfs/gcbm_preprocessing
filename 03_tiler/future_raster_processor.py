import os
from randomrastersubset import RandomRasterSubset

class FutureRasterProcessor(object):
    def __init__(self, base_raster_dir, years):
        self.years = years
        self.base_raster_dir = base_raster_dir
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

    def processSlashburn(self, year_percents, out_dir, random_subset):
        """
        param year_percents list of number pairs (year, percents)
        param out_dir the directory to which the raster files are written
        """
        for yp in year_percents:
            year = yp[0]
            percent = yp[1]





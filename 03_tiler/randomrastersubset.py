from osgeo import gdal
import numpy as np
import shutil

#used this as a reference
#https://geohackweek.github.io/raster/04-workingwithrasters/

class RandomRasterSubset(object):
    def __init__(self):
        pass

    def readInput(self, input, band=1):
        """
        reads the input raster and returns it as a numpy array
        """
        try:
            ds = gdal.Open(input)
            return np.array(ds.GetRasterBand(band)
                            .ReadAsArray())
        finally:
            del ds

    def writeOutput(self, output, values, band=1):
        try:
            ds = gdal.Open(output, gdal.GA_Update)
            band = ds.GetRasterBand(band)
            band.WriteArray(values)
        finally:
            del ds

    def RandomSubset(self, input, output, percent, default = 0, filter = [1], band=1):
        """
        takes a random subset of the filtered values of the input
        raster and writes the subset to the raster file specified by output
        """
        if percent < 0 or percent > 100:
           raise ValueError("specified percent out of bounds")
        p = percent / 100.0

        # copy the original to a new file
        shutil.copy(input, output)
        if p == 1: return

        # read the input as an array
        raster1 = self.readInput(input)

        #it is faster to generate random numbers for every position
        #(filtered or not) than to attempt to generate for only the filtered
        #subset with a non numpy native method
        rnd = np.random.rand(raster1.shape[0], raster1.shape[1])

        #filter the input raster values based on the specified filter
        filtered = np.isin(raster1, filter)

        #filter the subset based on passing both the filter and 
        #having p >= the random value for the index
        subset = np.where((filtered) & (rnd < p), raster1, default) 

        self.writeOutput(output, subset)

r = RandomRasterSubset()
r.RandomSubset(r"F:\GCBM\17_BC_ON_1ha\05_working_BC\TSA_2_Boundary\01a_pretiled_layers\03_disturbances\02_future\inputs\base\projected_fire_2015.tif",
              "out.tif", 10, 0, filter=[1])


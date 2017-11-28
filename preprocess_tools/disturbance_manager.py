import os
import logging
import re
from preprocess_tools.licensemanager import *

class DisturbanceParser(object):
    def __init__(self, path, multiple, type, year_disp, dist_type, name, year_range, filter_attribute=None, filter_code=None, year_attribute=None, extract_yr_re=None, standReplacing=True):
        '''
        Parameters
        path: {String} The path to the disturbances. Either directory/workspace if multiple or
              file path if single.
        multiple: {Boolean} True if there are multiple layers/shape files to consider
        type: {String} The type of file to read the disturbance as. Either 'gdb' or 'shp'
        year_disp: {int} If the year is in timestep form, this will be the year when timestep=0, else 0
        year_attribute: {String} Optional. If the year is contained in the layer/shape file this will
                        denote the name of the attribute column to get the year from.
        extract_yr_re: {String} A regular expression to get the year or timestep as a regular expression group
                        match object either in the file name or in the year attribute column. Can be excluded if
                        the year or timestep appears as is in the year attribute column.
        filter_attribute: {String} The column or field name in the layer/shape file to filter by
        filter_code: {String} The value to filter by in the filter_attribute column
        dist_type: {String} The AIDB disturbance type
        name: {String} The name for the new normalized layers
        standReplacing: {Boolean} Whether the disturbance is considered stand replacing or not
        '''
        self.path = path
        self.multiple = multiple
        self.type = type
        self.year_disp = year_disp
        self.year_attribute = year_attribute
        self.year_range = year_range
        self.extract_yr_re = extract_yr_re
        self.filter_attribute = filter_attribute
        self.filter_code = filter_code
        self.dist_type = dist_type
        self.name = name
        self.standReplacing = standReplacing

    def multiple(self):
        pass

    def listAll(self):
        if self.type=="gdb":
            with arc_license(Products.ARC) as arcpy:
                return arcpy.ListFeatureClasses()
        elif self.type=="shp":
            return os.listdir(self.path)

    def createDisturbanceCollection(self, gdb_path, lookup_attr=None, lookup=None):
        print "Creating disturbance collection"
        distColl = DisturbanceCollection(gdb_path, [], self.dist_type, self.standReplacing, lookup_attr, lookup)
        selectLayer = SelectLayer(self.path, gdb_path, self.filter_attribute, self.filter_code)
        with arc_license(Products.ARC) as arcpy:
            arcpy.env.overwriteOutput = True

            if self.type=="gdb":
                if self.multiple==True:
                    arcpy.env.workspace = self.path
                    for layer in listAll():
                        m = re.search(self.extract_yr_re, layer)
                        if m!=None:
                            try:
                                year = int(m.group(1)) + self.year_disp
                                if year in range(self.year_range[0], self.year_range[1]+1):
                                    name_yr = "_".join([self.name, str(year)])
                                    selectLayer.multipleGdb(name_yr, layer)
                                    distColl.add(DisturbanceLayer(year=year, aidb_dist=self.dist_type, name=name_yr, coll=distColl))
                            except ValueError:
                                logging.warning("Year/Timestep value not found in layer: {}".format(layer))

                elif self.multiple==False:
                    workspace, layer = os.path.split(self.path)
                    arcpy.env.workspace = workspace
                    for unique_year in set(row[0] for row in arcpy.da.SearchCursor(self.path, self.year_attribute)):
                        if self.extract_yr_re!=None:
                            m = re.search(self.extract_yr_re, unique_year)
                            try:
                                year = int(m.group(1)) + self.year_disp
                            except ValueError:
                                logging.warning("Year/Timestep value not found in attribute: {}".format(row.getValue(self.year_attribute)))
                        else:
                            year = int(unique_year) + self.year_disp
                        if year in range(self.year_range[0], self.year_range[1]+1):
                            name_yr = "_".join([self.name, str(year)])
                            selectLayer.singleGdb(name_yr, self.year_attribute, unique_year)
                            distColl.add(DisturbanceLayer(year=year, aidb_dist=self.dist_type, name=name_yr, coll=distColl))


            elif self.type=="shp":
                if self.multiple==True:
                    for layer in self.listAll():
                        m = re.search(self.extract_yr_re, layer)
                        if m!=None:
                            try:
                                year = int(m.group(1)) + self.year_disp
                                if year in range(self.year_range[0], self.year_range[1]+1):
                                    name_yr = "_".join([self.name, str(year)])
                                    selectLayer.multipleShp(name_yr, layer)
                                    distColl.add(DisturbanceLayer(year=year, aidb_dist=self.dist_type, name=name_yr, coll=distColl))
                            except ValueError:
                                logging.warning("Year/Timestep value not found in layer: {}".format(layer))

                elif self.multiple==False:
                    unique_years = {row[0] for row in arcpy.da.SearchCursor(self.path, self.year_attribute)}
                    for unique_year in [r for r in unique_years if r in range(self.year_range[0], self.year_range[1]+1)]:
                        if self.extract_yr_re!=None:
                            m = re.search(self.extract_yr_re, unique_year)
                            try:
                                year = int(m.group(1)) + self.year_disp
                            except ValueError:
                                logging.warning("Year/Timestep value not found in attribute: {}".format(row.getValue(self.year_attribute)))
                        else:
                            year = int(unique_year) + self.year_disp
                        name_yr = "_".join([self.name, str(year)])
                        selectLayer.singleShp(name_yr, self.year_attribute, unique_year)
                        distColl.add(DisturbanceLayer(year=year, aidb_dist=self.dist_type, name=name_yr, coll=distColl))

        print "Finished Creating disturbance collection"
        return distColl

class SelectLayer(object):
    def __init__(self, path, gdb_path, filter_attr, filter_code):
        self.path = path
        self.gdb_path = gdb_path
        if filter_attr!=None and filter_code!=None:
            self.filter_string = '"{0}" = {2}{1}{2}'.format(
                filter_attr, filter_code, "\'" if isinstance(filter_code, basestring) else "")
        else:
            self.filter_string = "1=1"

    def multipleShp(self, name, layer):
        with arc_license(Products.ARC) as arcpy:
            arcpy.env.workspace = os.path.dirname(self.path)
            arcpy.env.overwriteOutput = True
            arcpy.MakeFeatureLayer_management(os.path.join(self.path, layer), name)
            arcpy.SelectLayerByAttribute_management(name, "NEW_Selection",self.filter_string)
            if arcpy.Exists(os.path.join(self.gdb_path, name)):
                arcpy.Delete_management(os.path.join(self.gdb_path, name))
            arcpy.FeatureClassToGeodatabase_conversion(name, self.gdb_path)

    def singleShp(self, name, year_attr, year_code):
        with arc_license(Products.ARC) as arcpy:
            arcpy.env.workspace = os.path.dirname(self.path)
            arcpy.env.overwriteOutput = True
            filter_year = '"{0}" = {2}{1}{2}'.format(year_attr, year_code,
                "\'" if isinstance(year_code, basestring) else "")
            filter_string_yr = " AND ".join([self.filter_string,filter_year])
            arcpy.MakeFeatureLayer_management(self.path, name)
            arcpy.SelectLayerByAttribute_management(name, "NEW_Selection", filter_string_yr)
            if arcpy.Exists(os.path.join(self.gdb_path, name)):
                arcpy.Delete_management(os.path.join(self.gdb_path, name))
            arcpy.FeatureClassToGeodatabase_conversion(name, self.gdb_path)

    def multipleGdb(self, name):
        with arc_license(Products.ARC) as arcpy:
            arcpy.env.workspace = self.path
            arcpy.env.overwriteOutput = True
            arcpy.MakeFeatureLayer_management(os.path.join(self.path, layer), name)
            arcpy.SelectLayerByAttribute_management(name, "NEW_Selection",self.filter_string)
            if arcpy.Exists(os.path.join(self.gdb_path, name)):
                arcpy.Delete_management(os.path.join(self.gdb_path, name))
            arcpy.FeatureClassToGeodatabase_conversion(name, self.gdb_path)

    def singleGdb(self, name, year_attr, year_code):
        with arc_license(Products.ARC) as arcpy:
            arcpy.env.workspace = os.path.dirname(self.path)
            arcpy.env.overwriteOutput = True
            filter_year = '"{0}" = {2}{1}{2}'.format(year_attr, year_code,
                "\'" if isinstance(year_code, basestring) else "")
            filter_string_yr = " AND ".join([self.filter_string,filter_year])
            arcpy.MakeFeatureLayer_management(self.path, name)
            arcpy.SelectLayerByAttribute_management(name, "NEW_Selection",filter_string_yr)
            if arcpy.Exists(os.path.join(self.gdb_path, name)):
                arcpy.Delete_management(os.path.join(self.gdb_path, name))
            arcpy.FeatureClassToGeodatabase_conversion(name, self.gdb_path)


class DisturbanceCollection(object):
    def __init__(self, path, disturbances, type, standReplacing, lookup_attr=None, lookup=None):
        self.path = path
        self.disturbances = disturbances
        self.type = type
        self.standReplacing = standReplacing
        self.lookup_attr = lookup_attr
        self.lookup = lookup
        dir, name = os.path.split(path)
        if os.path.exists(dir):
            if not os.path.exists(path):
                with arc_license(Products.ARC) as arcpy:
                    arcpy.CreateFileGDB_management(dir, name)
        else:
            logging.error("Directory {} not found".format(dir))

    def add(self, disturbance):
        self.disturbances.append(disturbance)

    def remove(self, disturbance):
        if disturbance in self.disturbances:
            self.disturbances.remove(disturbance)
        else:
            print "Disturbance Not Found"

    def getDisturbances(self):
        return self.disturbances

    def getLookupAttr(self):
        return self.lookup_attr

    def getLookup(self):
        return self.lookup


class DisturbanceLayer(object):
    def __init__(self, year, aidb_dist, name, coll):
        self.year = year
        self.type = type
        self.path = os.path.join(coll.path, name)
        self.collection = coll
        self.name = name

    def __str__(self):
        print self.name

    def getYear(self):
        return self.year

    def getType(self):
        return self.aidb_dist

    def getPath(self):
        return self.path

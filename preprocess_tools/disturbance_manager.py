import archook
archook.get_arcpy()
import arcpy
import os
import logging

class YearParser(object):
    def __init__(self, re, in_file_name):
        self.re = re


class DisturbanceParser(object):
    def __init__(self, path, multiple, type, year_disp, year_attribute=None, layer_re, dist_attribute, dist_code, dist_type, name, standReplacing=True):
        '''
        Parameters
        path: {String} The path to the disturbances. Either directory/workspace if multiple or
              file path if single.
        multiple: {Boolean} True if there are multiple layers/shape files to consider
        type: {String} The type of file to read the disturbance as. Either 'gdb' or 'shp'
        year_disp: {int} If the year is in timestep form, this will be the year when timestep=0, else 0
        year_attribute: {String} Optional. If the year is contained in the layer/shape file this will
                        denote the name of the attribute column to get the year from.
        layer_re: {String} A regular expression to get the year or timestep as a regular expression group
                 match either in the file name or in the year attribute column.
        dist_attribute: {String} The column name in the layer/shape file for the disturbance type
        dist_code: {String} The value to filter by in the dist_attribute column
        dist_type: {String} The AIDB disturbance type
        name: {String} The name for the new normalized layers
        standReplacing: {Boolean} Whether the disturbance is considered stand replacing or not
        '''
        self.multiple = multiple
        self.type = type
        self.year_disp = year_disp
        self.year_attribute = year_attribute
        self.layer_re = layer_re
        self.dist_attribute = dist_attribute
        self.dist_code = dist_code
        self.dist_type = dist_type
        self.name = name
        self.standReplacing = standReplacing

    def multiple(self):
        pass

    def listAll(self):
        if self.type=="gdb":
            return arcpy.ListFeatureClasses()
        elif self.type=="shp":
            return os.listdir(self.path)

    def createDisturbanceCollection(self, gdb_path):
        distColl = DisturbanceCollection(gdb_path, [], self.dist_type, self.standReplacing)
        selectLayer = SelectLayer(self.path, gdb_path)

        if self.type=="gdb":
            if self.multiple==True:
                arcpy.env.workspace = self.path
                for layer in listAll():
                    m = re.search(layer_re, layer)
                    if m!=None:
                        try:
                            year = int(m.group(1)) + year_disp
                            npath = self.new_path if self.new_path else self.path
                            selectLayer.multipleGdb(self.name, layer, self.dist_attribute, self.dist_code)
                            distColl.add(DisturbanceLayer(year=year, type=self.dist_type, path=self.path, new_path=npath, name=self.name))
                        except ValueError:
                            logging.warning("Year/Timestep value not found in layer: {}".format(layer))
            elif self.multiple==False:
                workspace, layer = os.path.split(self.path)
                arcpy.env.workspace = workspace


        elif self.type=="shp":
            if self.multiple==True:
                for layer in listAll():
                    m = re.search(layer_re, layer)
                    if m!=None:
                        try:
                            year = int(m.group(1)) + year_disp
                            npath = self.new_path if self.new_path else self.path
                            selectLayer.multipleShp(self.name, layer, self.dist_attribute, self.dist_code)
                            distColl.add(DisturbanceLayer(self, year=year, new_path=npath))
                        except ValueError:
                            logging.warning("Year/Timestep value not found in layer: {}".format(layer))


class SelectLayer(object):
    def __init__(self, path, gdb_path):
        self.path = path
        self.gdb_path = gdb_path

    def multipleShp(self, name, layer, dist_attr, dist_code):
        arcpy.MakeFeatureLayer_management(os.path.join(self.path, layer), name)
        arcpy.SelectLayerByAttribute_management(name, "NEW_Selection", "{0} = {1}".format(dist_attr, dist_code))
        arcpy.FeatureClassToGeodatabase_conversion(name, gdb_path)

    def singleShp(self, name, dist_attr, dist_code, year_attr, year_code):
        arcpy.MakeFeatureLayer_management(self.path, name)
        arcpy.SelectLayerByAttribute_management(name, "NEW_Selection",
            "{0} = {1} AND {2} = {3}".format(dist_attr, dist_code, year_attr, year_code))
        arcpy.FeatureClassToGeodatabase_conversion(name, gdb_path)

    def multipleGdb(self, name, dist_attr, dist_code):
        arcpy.MakeFeatureLayer_management(os.path.join(self.path, layer), name)
        arcpy.SelectLayerByAttribute_management(name, "NEW_Selection", "{0} = {1}".format(dist_attr, dist_code))
        arcpy.FeatureClassToGeodatabase_conversion(name, gdb_path)

    def singleGdb(self, name, dist_attr, dist_code, year_attr, year_code):
        arcpy.MakeFeatureLayer_management(self.path, name)
        arcpy.SelectLayerByAttribute_management(name, "NEW_Selection",
            "{0} = {1} AND {2} = {3}".format(dist_attr, dist_code, year_attr, year_code))
        arcpy.FeatureClassToGeodatabase_conversion(name, gdb_path)


class DisturbanceCollection(object):
    def __init__(self, path, disturbances, type, standReplacing):
        self.path = path
        self.disturbances = disturbances
        self.type = type
        self.standReplacing = standReplacing

    def add(self, disturbance):
        self.disturbances.append(disturbance)

    def remove(self, disturbance):
        if disturbance in self.disturbances:
            self.disturbances.remove(disturbance)
        else:
            print "Disturbance Not Found"


class DisturbanceLayer(object):
    def __init__(self, year, type, path, new_path, name):

class DisturbanceShp(object):
    def __init__(self, year, type, path, new_path, name):

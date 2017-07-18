import arcpy
import gcbm_aws
import os

class Inventory(object):
	def __init__(self, path, layer, age_field, year, classifiers_attr, field_names=None):
		if path.split('.')[-1] == "gdb":
			self.workspace = path
			arcpy.env.workspace = self.workspace
		else:
			workspace = None
		self._path = path
		self._layer_name = layer
		self._age_field = age_field
		self._year = year
		self._bounding_box = self.getBoundingBox()
		self._field_names = field_names
		self._classifiers_attr = classifiers_attr
		self._rasters = []

	def getPath(self):
		return self._path

	def setPath(self, path):
		self._path = path

	def getLayerName(self):
		return self._layer_name

	def setLayerName(self, layer):
		self._layer_name = layer

	def getAgeField(self):
		return self._age_field

	def getYear(self):
		return self._year

	def reproject(self, new_name):
		print "Reprojecting Inventory... ",
		arcpy.env.overwriteOutput = True
		#PROJECTIONS
		#method
		transform_method = "WGS_1984_(ITRF00)_To_NAD_1983"
		#input
		input_proj = "PROJCS['PCS_Albers',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Albers'],PARAMETER['False_Easting',1000000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-126.0],PARAMETER['Standard_Parallel_1',50.0],PARAMETER['Standard_Parallel_2',58.5],PARAMETER['Latitude_Of_Origin',45.0],UNIT['Meter',1.0]]"
		#output
		output_proj = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]"
		# Process: Project
		new_path = os.path.join(self._path, new_name)
		arcpy.Project_management(os.path.join(self._path, self._layer_name), new_path, output_proj,
			transform_method, input_proj, "NO_PRESERVE_SHAPE", "","NO_VERTICAL")
		self._layer_name = new_name
		self._bounding_box = self.getBoundingBox()
		print "Done"

	def getBoundingBox(self):
		desc = arcpy.Describe(self._layer_name)
		e = desc.extent
		return [e.XMin, e.YMin, e.XMax, e.YMax]

	def getBoundingBoxD(self):
		extent = list(gcbm_aws.util.get_bbox(self._path, self._layer_name))
		return extent

	def getBottomLeftCorner(self):
		return self._bounding_box[0], self._bounding_box[1]

	def getTopRightCorner(self):
		return self._bounding_box[2], self._bounding_box[3]

	def getClassifiers(self):
		return [c for c in self._classifiers_attr]

	def getClassifierAttr(self, classifier):
		try:
			return self._classifiers_attr[classifier]
		except:
			return None

	def getRasters(self):
		return self._rasters

	def addRaster(self, path, attr, attr_table):
		self._rasters.append(Raster(path, attr, attr_table))

	def getFieldNames(self):
		field_names = {
			"disturbed_inventory": "DisturbedInventory",
			"disturbed_inventory_layer": "disturbedInventory_layer",
			"age": "Age2011",
			"establishment_date": "DE_2011",
			"disturbance_yr": "DistYEAR",
			"new_disturbance_yr": "DistYEAR_new",
			"inv_dist_date_diff": "Dist_DE_DIFF",
			"dist_type": "DistType",
			"harv_yr": "HARV_YR",
			"regen_delay": "RegenDelay",
			"pre_dist_age": "preDistAge",
			"rollback_vintage": "Age1990",
			"species": "LeadSpp"
		}
		if self._field_names != None:
			field_names.update(self._field_names)
		return field_names

class Raster(object):
	def __init__(self, path, attr, attr_table):
		self._path = path
		self._attr = attr
		self._attr_table = attr_table

	def getAttr(self):
		return self._attr

	def getAttrTable(self):
		return self._attr_table

	def getPath(self):
		return self._path

class TransitionRules(object):
	def __init__(self, path, classifier_cols, header, cols):
		self._classifiers = classifier_cols
		self._path = path
		self._header = bool(header in ["1", True])
		self._name_col = cols["NameCol"]
		self._age_col = cols["AgeCol"]
		self._delay_col = cols["DelayCol"]

	def getClassifiers(self):
		return [c for c in self._classifiers]

	def getClassifierCol(self, classifier):
		return self._classifiers[classifier]

	def setClassifierCol(self, classifier_col):
		self._classifiers.update(classifier_col)

	def isHeader(self):
		return self._header

	def getFilePath(self):
		return self._path

	def setFilePath(self, path):
		self._path = path

	def getNameCol(self):
		return self._name_col

	def getAgeCol(self):
		return self._age_col

	def getDelayCol(self):
		return self._delay_col


class YieldTable(object):
	def __init__(self, path, classifier_cols, header, interval, cols):
		self._classifiers = classifier_cols
		self._path = path
		self._header = bool(header in ["1", True])
		self._species_col = cols["SpeciesCol"]
		self._increment_col_range = cols["IncrementRange"]
		self._interval = interval

	def getClassifiers(self):
		return [c for c in self._classifiers]

	def getClassifierCol(self, classifier):
		return self._classifiers[classifier]

	def setClassifierCol(self, classifier_col):
		self._classifiers.update(classifier_col)

	def isHeader(self):
		return self._header

	def getFilePath(self):
		return self._path

	def setFilePath(self, path):
		self._path = path

	def getSpeciesCol(self):
		return self._species_col

	def getIncrementRange(self):
		return self._increment_col_range

	def getInterval(self):
		return self._interval


# class Classifier(object):
#     def __init__(self, name):
#         self._name = name
#
#     def getName(self):
#         return self._name

class HistoricDisturbances(object):
    def __init__(self):
        pass

class ProjectedDisturbances(object):
    def __init__(self):
        pass

class NAmericaMAT(object):
    def __init__(self, path):
        self._path = path

    def getPath(self):
    	return self._path

    def setPath(self, path):
    	self._path = path

class AIDB(object):
	def __init__(self, path):
		self._path = path

	def getPath(self):
		return self._path

	def setPath(self):
		self._path = path

class SpatialBoundaries(object):
	def __init__(self, path_tsa, path_pspu, type, filter, attributes):
		self._path_tsa = path_tsa
		self._path_pspu = path_pspu
		self._type = type
		self._attributes = attributes
		if "field" and "code" in filter:
			self._filter = filter
			if "operator" not in filter:
				self._filter.update({"operator": "="})

	def getPathTSA(self):
		return self._path_tsa

	def getPathPSPU(self):
		return self._path_pspu

	def setPathTSA(self, path):
		self._path_tsa = path

	def setPathPSPU(self, path):
		self._path_pspu = path

	def getType(self):
		return self._type

	def getFilter(self):
		return self._filter

	def getAttributes(self):
		return [a for a in self._attributes]

	def getAttrField(self, attr):
		return self._attributes[attr]


class ReportingIndicators(object):
	def __init__(self, indicators):
		self._indicators = indicators

	def getReportingIndicators(self):
		pass

	def addReportingIndicator(self, name, path, attribute):
		pass

class RollbackDisturbances(object):
	def __init__(self, path):
		self._path = path

	def getPath(self):
		return self._path

class HistoricDisturbance(object):
	def __init__(self, workspace, filter, year_field):
		self._workspace = workspace
		self._filter = filter
		self._year_field = year_field

	def getWorkspace(self):
		return self._workspace

	def getFilter(self):
		return self._filter

	def getYearField(self):
		return self._year_field

class ProjectedDisturbance(object):
	def __init__(self, workspace, filter, scenario, lookup_table):
		self._workspace = workspace
		self._filter = filter
		self._scenario = scenario
		self._lookup_table = lookup_table

	def getWorkspace(self):
		return self._workspace

	def getFilter(self):
		return self._filter

	def getScenario(self):
		return self._scenario

	def getLookupTable(self):
		return self._lookup_table

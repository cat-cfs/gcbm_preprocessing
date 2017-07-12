import arcpy
import gcbm_aws

class Inventory(object):
	def __init__(self, path, layer, age_field, year, classifiers_attr, field_names=None):
		if inventory_path.split('.')[-1] == "gdb":
			self.workspace = inventory_path
			arcpy.env.workspace = self.workspace
		else:
			workspace = None
		self._inventory_path = path
		self._layer_name = layer
		self._age_field = age_field
		self._year = year
		self._desc = arcpy.Describe(layer)
		self._bounding_box = self.getBoundingBoxM()
		self._field_names = field_names
		self._classifiers_attr = classifiers_attr

	def getPath(self):
		return self._inventory_path

	def setPath(self, path):
		self._inventory_path = path

	def getLayerName(self):
		return self._layer_name

	def setLayerName(self, layer):
		self._layer_name = layer

	def getAgeField(self):
		return self._age_field

	def getYear(self):
		return self._year

	def getBoundingBoxM(self):
		e = self._desc.extent
		return [e.XMin, e.YMin, e.XMax, e.YMax]

	def getBoundingBoxD(self):
		extent = list(gcbm_aws.util.get_bbox(self._inventory_path, self._layer_name))

	def getBottomLeftCorner(self):
		return self._bounding_box[0], self._bounding_box[1]

	def getTopRightCorner(self):
		return self._bounding_box[2], self._bounding_box[3]

	def getClassifiers(self):
		return [c for c in self._classifiers_attr]

	def getClassifierAttr(self, classifier):
		return self._classifers_attr[classifier]

	def getFieldNames(self):
		field_names = {
			"disturbed_inventory": "DisturbedInventory",
			"disturbed_inventory_layer": "disturbedInventory_layer",
			"inv_age": "Age2011",
			"establishment_date": "DE_2011",
			"disturbance_yr": "DistYEAR",
			"new_disturbance_yr": "DistYEAR_new",
			"inv_dist_date_diff": "Dist_DE_DIFF",
			"dist_type": "DistType",
			"harv_yr": "HARV_YR",
			"regen_delay": "RegenDelay",
			"pre_dist_age": "preDistAge",
			"rollback_vintage": "Age1990"
		}
		if self._field_names != None:
			field_names.update(self._field_names)
		return field_names

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
    def __init__(self):
        pass

class AIDB(object):
	def __init__(self, path):
		self._path = path

	def getPath(self):
		return self._path

class SpatialBoundaries(object):
	def __init__(self, path, type, attribute, name):
		self._path = path
		self._type = type
		self._attribute = attribute
		self._name = name

	def getFilePath(self):
		return self._path

	def getType(self):
		return self._type

	def getAttributeCol(self):
		return self._attribute

	def getName(self):
		return self._name

class ReportingIndicators(object):
	def __init__(self, indicators):
		self._indicators = indicators

	def getReportingIndicators(self):
		pass

	def addReportingIndicator(self, name, path, attribute):
		pass

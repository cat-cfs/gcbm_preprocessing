import arcpy
import os
import glob
import shutil

class SpatialInputs(object):
	def __init__(self, workspace, filter):
		self._workspace = workspace
		self._filter = filter

	def getWorkspace(self):
		return self._workspace

	def getFilter(self):
		return self._filter

	def reproject(self, new_workspace, name=None):
		# Project the layer from NAD 1983 to WGS 1984
		if not os.path.exists(new_workspace):
			self.createWorkspace(new_workspace)
		if new_workspace==self.getWorkspace() and name==None:
			raise Exception('Error: Cannot overwrite. Specify a new workspace or a new layer name.')
		arcpy.env.overwriteOutput = True
		transform_method = "WGS_1984_(ITRF00)_To_NAD_1983"
		output_proj = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]"
		print "Reprojecting {}...".format(self.getFilter()),
		for layer in self.scan_for_layers():
			if name==None:
				if '.tif' in os.path.basename(layer):
					arcpy.ProjectRaster_management(layer, os.path.join(new_workspace, os.path.basename(layer)), output_proj, "", "", transform_method, "", "")
				else:
					arcpy.Project_management(layer, os.path.join(new_workspace, os.path.basename(layer)), output_proj, transform_method, "", "NO_PRESERVE_SHAPE", "","NO_VERTICAL")
			else:
				if '.tif' in os.path.basename(layer):
					arcpy.ProjectRaster_management(layer, os.path.join(new_workspace, os.path.basename(layer)), output_proj, "", "", transform_method, "", "")
				else:
					arcpy.Project_management(layer, os.path.join(new_workspace, name), output_proj, transform_method, "", "NO_PRESERVE_SHAPE", "","NO_VERTICAL")
				self._filter = name
				break
		self._workspace = new_workspace
		print "Done"

	def clip(self, workspace, clip_feature, clip_feature_filter, new_workspace, name=None):
		if not os.path.exists(new_workspace):
			self.createWorkspace(new_workspace)
		if new_workspace==self.getWorkspace() and name==None:
			raise Exception('Error: Cannot overwrite. Specify a new workspace or a new layer name.')
		print "Clipping {}...".format(self.getFilter()),
		arcpy.env.workspace = workspace
		arcpy.env.overwriteOutput = True
		arcpy.MakeFeatureLayer_management(clip_feature, 'clip_to', clip_feature_filter)
		for layer in self.scan_for_layers():
			arcpy.MakeFeatureLayer_management(layer, 'clip')
			arcpy.SelectLayerByLocation_management('clip', "INTERSECT", 'clip_to', "", "NEW_SELECTION", "NOT_INVERT")
			if name==None:
				arcpy.FeatureClassToFeatureClass_conversion('clip', new_workspace, os.path.basename(layer))
			else:
				arcpy.FeatureClassToFeatureClass_conversion('clip', new_workspace, name)
				self._filter = name
				break
		arcpy.Delete_management('clip_to')
		self._workspace = new_workspace
		print "Done"

	def clipCutPolys(self, workspace, clip_feature, clip_feature_filter, new_workspace, name=None):
		if not os.path.exists(new_workspace):
			self.createWorkspace(new_workspace)
		if new_workspace==self.getWorkspace() and name==None:
			raise Exception('Error: Cannot overwrite. Specify a new workspace or a new layer name.')
		print "Clipping {}{}...".format(self.getFilter(), ' to {}'.format(name) if name else ''),
		arcpy.env.workspace = workspace
		arcpy.env.overwriteOutput = True
		arcpy.MakeFeatureLayer_management(clip_feature, 'clip_to', clip_feature_filter)
		for layer in self.scan_for_layers():
			arcpy.MakeFeatureLayer_management(layer, 'clip')
			if name==None:
				arcpy.Clip_analysis('clip', 'clip_to', os.path.join(new_workspace, os.path.basename(layer)))
			else:
				arcpy.Clip_analysis('clip', 'clip_to', os.path.join(new_workspace, name))
				self._filter = name
				break
		arcpy.Delete_management('clip_to')
		self._workspace = new_workspace
		print "Done"

	def copy(self, new_workspace):
		if not os.path.exists(new_workspace):
			self.createWorkspace(new_workspace)
		if new_workspace==self.getWorkspace():
			raise Exception('Error: Cannot overwrite. Specify a new workspace or a new layer name.')
		print "Copying {}...".format(self.getFilter()),
		for layer in self.scan_for_layers():
			if '.gdb' in self.getWorkspace():
				arcpy.env.workspace = self.getWorkspace()
				arcpy.FeatureClassToFeatureClass_conversion(os.path.basename(layer), new_workspace, os.path.basename(layer))
			else:
				for file in self.scan_for_files(os.path.basename(layer).split('.')[0]):
					shutil.copyfile(file, os.path.join(new_workspace, os.path.basename(file)))
		self._workspace = new_workspace
		print 'Done'

	def createWorkspace(self, new_workspace):
		if '.gdb' in os.path.basename(new_workspace):
			if os.path.exists(os.path.dirname(new_workspace)):
				arcpy.CreateFileGDB_management(os.path.dirname(new_workspace), os.path.basename(new_workspace).split('.')[0])
			else:
				os.makedirs(os.path.dirname(new_workspace))
				arcpy.CreateFileGDB_management(os.path.dirname(new_workspace), os.path.basename(new_workspace).split('.')[0])
		else:
			os.makedirs(new_workspace)

	def scan_for_layers(self):
		if '.gdb' in self.getWorkspace():
			arcpy.env.workspace = self.getWorkspace()
			all = arcpy.ListFeatureClasses()
			return [os.path.join(self.getWorkspace(), layer) for layer in all if layer==self.getFilter()]
		return sorted(glob.glob(os.path.join(self.getWorkspace(), self.getFilter())), key=os.path.basename)

	def scan_for_files(self, name):
		return sorted(glob.glob(os.path.join(self.getWorkspace(), '{}*'.format(name))), key=os.path.basename)

class Inventory(SpatialInputs):
	def __init__(self, workspace, filter, year, classifiers_attr, field_names=None):
		arcpy.env.workspace = workspace
		self._workspace = workspace
		self._filter = filter
		self._year = year
		self._bounding_box = self.getBoundingBox()
		self._field_names = field_names
		self._classifiers_attr = classifiers_attr
		self._rasters = []

	def getWorkspace(self):
		return self._workspace

	def setWorkspace(self, path):
		self._workspace = path

	def getLayerName(self):
		return self._filter

	def setLayerName(self, layer):
		self._filter = layer

	def getFilter(self):
		return self._filter

	def getYear(self):
		return self._year

	def reproject(self, new_workspace, name=None):
		super(Inventory, self).reproject(new_workspace, name=name)
		self._bounding_box = self.getBoundingBox()

	def getBoundingBox(self):
		arcpy.env.workspace = self._workspace
		desc = arcpy.Describe(self._filter)
		e = desc.extent
		return [e.XMin, e.YMin, e.XMax, e.YMax]

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
			"age": "Age2011",
			"species": "LeadSpp",
			"ownership": "Own",
			"FMLB": "FMLB",
			"THLB": "THLB",
			"establishment_date": "DE",
			"dist_date_diff": "Dist_DE_DIFF",
			"pre_dist_age": "preDistAge",
			"dist_type": "DistType",
			"regen_delay": "RegenDelay",
			"rollback_age": "Age1990",
			"disturbance_yr": "DistYEAR",
			"new_disturbance_yr": "DistYEAR_new"
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

	def getPath(self):
		return self._path

	def setPath(self, path):
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

	def getPath(self):
		return self._path

	def setPath(self, path):
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


class NAmericaMAT(SpatialInputs):
	def __init__(self, workspace, filter):
		self._workspace = workspace
		self._filter = filter

	def getPath(self):
		return os.path.join(self._workspace, self._filter)


class AIDB(object):
	def __init__(self, path):
		self._path = path

	def getPath(self):
		return self._path

	def setPath(self):
		self._path = path

class SpatialBoundaries(SpatialInputs):
	def __init__(self, workspace, filter_tsa, filter_pspu, type, area_filter, attributes):
		self._workspace = workspace
		self._path_tsa = os.path.join(workspace, filter_tsa)
		self._path_pspu = os.path.join(workspace, filter_pspu)
		self._type = type
		self._attributes = attributes
		if "field" and "code" in area_filter:
			self._area_filter = area_filter
			if "operator" not in area_filter:
				self._area_filter.update({"operator": "="})
		else:
			print "Warning: invalid area filter object"

	def getWorkspace(self):
		return self._workspace

	def getFilter(self):
		return "*.shp"

	def getPathTSA(self):
		return self._path_tsa

	def getPathPSPU(self):
		return self._path_pspu

	def setPathTSA(self, path):
		self._workspace = os.path.dirname(path)
		self._path_tsa = path

	def setPathPSPU(self, path):
		self._workspace = os.path.dirname(path)
		self._path_pspu = path

	def getType(self):
		return self._type

	def getAreaFilter(self):
		return self._area_filter

	def getAttributes(self):
		return [a for a in self._attributes]

	def getAttrField(self, attr):
		return self._attributes[attr]


class ReportingIndicators(object):
	def __init__(self, indicators):
		self._reporting_indicators = indicators

	def getIndicators(self):
		return self._reporting_indicators

	def addReportingIndicator(self, indicator):
		self._reporting_indicators.update(indicator)

class RollbackDisturbances(object):
	def __init__(self, path):
		self._path = path

	def getPath(self):
		return self._path

class HistoricDisturbance(SpatialInputs):
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

class ProjectedDisturbance(SpatialInputs):
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

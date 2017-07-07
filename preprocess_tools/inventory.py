import arcpy
import gcbm_aws

class Inventory(object):
	def __init__(self, inventory_path, layer, age_field, year, fieldNames=None):
		if inventory_path.split('.')[-1] == "gdb":
			self.workspace = inventory_path
			arcpy.env.workspace = self.workspace
		else:
			workspace = None
		self._inventory_path = inventory_path
		self._layer_name = layer
		self._age_field = age_field
		self._year = year
		self._desc = arcpy.Describe(layer)
		self._bounding_box = self.getBoundingBoxM()
		self.fieldNames = fieldNames

	def getPath(self):
		return self._inventory_path

	def getLayerName(self):
		return self._layer_name

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

	def getFieldNames(self):
		fieldNames = {
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
		if self.fieldNames != None:
			fieldNames.update(self.fieldNames)

		return fieldNames

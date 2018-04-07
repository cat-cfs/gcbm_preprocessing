import csv
import random
import os
import logging
import inspect

import pgdata


class RollbackDistributor(object):
    def __init__(self, **age_proportions):
        self._rand = random.Random()
        self._ages = []
        for age, proportion in age_proportions.iteritems():
            self._ages.extend([age] * int(100.00 * proportion))

        self._rand.shuffle(self._ages)
        self._choices = {age: 0 for age in age_proportions.keys()}

    def __str__(self):
        return str(self._choices)

    def next(self):
        age = self._rand.choice(self._ages)
        self._choices[age] += 1
        return int(age)


def rollback_age_disturbed(config):
    """ Calculate pre-disturbance age and rollback inventory age
    """
    dist_age_prop_path = config.GetDistAgeProportionFilePath()
    logging.info("Calculating pre disturbance age using '{}' to select age"
                 .format(dist_age_prop_path))
    # Calculating pre-disturbance age is one execution per grid cell record
    # It should be possible to apply the update to all cells at once...
    # Maybe using this approach?
    # https://dba.stackexchange.com/questions/55363/set-random-value-from-set/55364#55364
    dist_age_props = {}
    with open(dist_age_prop_path, "r") as age_prop_file:
        reader = csv.reader(age_prop_file)
        reader.next()  # skip header
        for dist_type, age, prop in reader:
            dist_type = int(dist_type)
            dist_ages = dist_age_props.get(dist_type)
            if not dist_ages:
                dist_age_props[dist_type] = {}
                dist_ages = dist_age_props[dist_type]
            dist_ages[age] = float(prop)
    age_distributors = {}
    for dist_type, age_props in dist_age_props.iteritems():
        age_distributors[dist_type] = RollbackDistributor(**age_props)
    db = pgdata.connect()
    for row in db['preprocessing.inventory_disturbed']:
        age_distributor = age_distributors.get(dist_type)
        # logging.info("Age picks for disturbance type {}:{}".format(
        # dist_type, str(age_distributor)))
        sql = """
            UPDATE preprocessing.inventory_disturbed
            SET pre_dist_age = %s
            WHERE grid_id = %s
        """
        db.execute(sql, (age_distributor.next(), row['grid_id']))

    logging.info("Calculating rollback inventory age")
    sql = """
        UPDATE preprocessing.inventory_disturbed
        SET rollback_age = pre_dist_age + (%s - new_disturbance_yr)
    """
    db = pgdata.connect()
    db.execute(sql, (config.GetRollbackRange()["StartYear"]))


def rollback_age_non_disturbed(config):
    """ Roll back age for undisturbed stands
    """
    logging.info('Rolling back ages for age {}'.format(
        config.GetRollbackRange()["StartYear"]))
    sql_path = os.path.join(os.path.dirname(inspect.stack()[0][1]), 'sql')
    db = pgdata.connect(sql_path=sql_path)
    db['preprocessing.inventory_rollback'].drop()
    db.execute(
        db.queries['inventory_rollback'],
        (config.GetInventoryYear(), config.GetRollbackRange()["StartYear"]))


def generate_slashburn(config):
    """
    Generate annual slashburn disturbances for the rollback period.

    Note:
    slashburn disturbances are written as grid cells to preprocessing.temp_slashburn
    (this lets us use the same query to generate slashburn for rollback and historic)
    """
    rollback_start = config.GetRollbackRange()["StartYear"]
    rollback_end = config.GetRollbackRange()["EndYear"]
    slashburn_percent = config.GetSlashBurnPercent()
    logging.info('Generating slashburn for {}-{} as {} of annual harvest area'.format(
        rollback_start,
        rollback_end,
        slashburn_percent))
    sql_path = os.path.join(os.path.dirname(inspect.stack()[0][1]), 'sql')
    db = pgdata.connect(sql_path=sql_path)
    db['preprocessing.temp_slashburn'].drop()
    db.execute("""
        CREATE TABLE preprocessing.temp_slashburn
        (slashburn_id serial primary key,
         grid_id integer,
         dist_type integer,
         year integer)
    """)
    for year in range(rollback_start, rollback_end + 1):
        db.execute(db.queries['create_slashburn'], (year, slashburn_percent))


class ExportRollback(object):
    def __init__(self, inventory_workspace, inventory_year, inventory_field_names,
                 inventory_classifiers, rollbackInvOut, rollbackDisturbancesOutput, rollback_range,
                 resolution, sb_percent, reporting_classifiers):

        self.inventory_workspace = inventory_workspace
        self.inventory_year = inventory_year
        self.inventory_field_names = inventory_field_names
        self.inventory_classifiers = inventory_classifiers

        self.rollbackDisturbanceOutput = rollbackDisturbancesOutput
        self.rasterOutput = rollbackInvOut
        self.resolution = resolution
        self.slashburn_percent = sb_percent
        self.reporting_classifiers = reporting_classifiers

        #data
        self.gridded_inventory = "inventory_gridded"
        self.disturbedInventory = "DisturbedInventory"
        self.RolledBackInventory = "inventory_gridded_1990"
        self.rollback_range = rollback_range
        self.inv_vintage = inventory_year
        self.rollback_start = rollback_range[0]

        #layers
        self.RolledBackInventory_layer = "RolledBackInventory_layer"
        self.gridded_inventory_layer = "gridded_inventory_layer"
        self.disturbedInventory_layer = "disturbedInventory_layer"


    def exportRollbackDisturbances(self):

        #Export rollback disturbances

        logging.info('Exporting rollback disturbances to {}'.format(self.rollbackDisturbanceOutput))
        dirname =  os.path.dirname(self.rollbackDisturbanceOutput)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        dissolveFields = [self.dist_type_field, self.new_disturbance_field,self.regen_delay_field, self.CELL_ID]
        selectClause =  "{} IS NOT NULL".format(self.new_disturbance_field)

        self.arcpy.SelectLayerByAttribute_management(self.RolledBackInventory_layer, "NEW_SELECTION", selectClause)
        self.arcpy.Dissolve_management(self.RolledBackInventory_layer, self.rollbackDisturbanceOutput, dissolveFields,
            "","SINGLE_PART","DISSOLVE_LINES")

    def exportRollbackInventory(self):

        logging.info('Exporting rolled back inventory rasters to {}'.format(self.rasterOutput))
        rasterMeta = []
        self.arcpy.env.overwriteOutput = True

        fields = {
            "age": self.inventory_field_names["rollback_age"],
            "species": self.inventory_field_names["species"]
        }

        for classifierName, fieldName in self.reporting_classifiers.items():
            if not classifierName in fields:
                fields.update({classifierName:fieldName})
            else:
                raise KeyError("duplicated reporting classifier: '{}'".format(classifierName))

        if not os.path.exists(self.rasterOutput):
            os.makedirs(self.rasterOutput)
        for classifier_name, classifier_attribute in self.inventory_classifiers.items():
            logging.info('Exporting classifer {} from {}'.format(classifier_name, os.path.join(self.inventory_workspace,self.RolledBackInventory)))
            field_name = classifier_attribute
            file_path = os.path.join(self.rasterOutput, "{}.tif".format(classifier_name))
            attribute_table_path = os.path.join(self.rasterOutput, "{}.tif.vat.dbf".format(classifier_name))
            self.arcpy.FeatureToRaster_conversion(self.RolledBackInventory, field_name, file_path, self.resolution)
            rasterMeta.append(
                {
                    "file_path": file_path,
                    "attribute": classifier_name,
                    "attribute_table": self.createAttributeTable(attribute_table_path, field_name)
                }
            )
        for attr in fields:
            logging.info('Exporting field {} from {}'.format(attr, os.path.join(self.inventory_workspace,self.RolledBackInventory)))
            field_name = fields[attr]
            file_path = os.path.join(self.rasterOutput,"{}.tif".format(attr))
            attribute_table_path = os.path.join(self.rasterOutput, "{}.tif.vat.dbf".format(attr))
            self.arcpy.FeatureToRaster_conversion(self.RolledBackInventory, field_name, file_path, self.resolution)
            rasterMeta.append(
                {
                    "file_path": file_path,
                    "attribute": attr,
                    "attribute_table": self.createAttributeTable(attribute_table_path, field_name)
                })

        return rasterMeta

    def createAttributeTable(self, dbf_path, field_name):
        # Creates an attribute table with the field name given
        # to be used in the tiler along with the tif. This is
        # necessary for fields that are not integers.
        attr_table = {}
        for row in DBF(dbf_path):
            if len(row)<3:
                return None
            attr_table.update({row.items()[0][1]: [row.items()[-1][1]]})
        return attr_table


def load_dist_age_prop(self, dist_age_prop_path):
    """
    Load disturbance age csv data to postgres
    Currently not used but could be useful to speed up calculatePreDistAge
    """
    db = pgdata.connect()
    db['preprocessing.dist_age_prop'].drop()
    db.execute("""CREATE TABLE preprocessing.dist_age_prop
                  (dist_type_id integer, age integer, proportion numeric)""")
    with open(dist_age_prop_path, "r") as age_prop_file:
        reader = csv.reader(age_prop_file)
        reader.next()  # skip header
        for dist_type, age, prop in reader:
            db.execute("""
                INSERT INTO preprocessing.dist_age_prop
                (dist_type_id, age, proportion)
                VALUES (%s, %s, %s)
            """, (dist_type, age, prop))

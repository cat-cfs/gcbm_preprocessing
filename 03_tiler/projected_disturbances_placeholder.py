import archook
archook.get_arcpy()
import arcpy
import shutil
import inspect
import os
import glob
import logging

class ProjectedDisturbancesPlaceholder(object):
    def __init__(self, inventory, rollbackDisturbances, ProgressPrinter, output_dir=None):
        self.ProgressPrinter = ProgressPrinter
        self.inventory = inventory
        self.rollbackDisturbances = rollbackDisturbances
        if output_dir==None:
            self.output_dir = os.path.abspath(r'{}\..\01a_pretiled_layers\03_disturbances\02_future\outputs'.format(os.getcwd()))
        else:
            self.output_dir = output_dir

    def copyRollbackDistAsFuture(self,scenario):
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        output_directory = os.path.join(self.output_dir,'SCEN_{}'.format(scenario))
        name = 'projectedDist'
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        for file in self.scan_for_files_all_ext(self.rollbackDisturbances.getPath()):
            ext = file.split('.')[-1]
            shutil.copyfile(file, os.path.join(output_directory,'{}.{}'.format(name,ext)))
        projectedDistDBF = os.path.join(output_directory,'{}.dbf'.format(name))
        arcpy.AddField_management(projectedDistDBF, 'dist_year')
        arcpy.CalculateField_management(projectedDistDBF, 'dist_year', '!{}!+26'.format(self.inventory.getFieldNames()['new_disturbance_yr'][:10]),"PYTHON_9.3", "")
        projectedDistShp = os.path.join(output_directory,'{}.shp'.format(name))
        pp.finish()
        return projectedDistShp

    def scan_for_files_all_ext(self, file_path):
        return sorted(glob.glob('{}*'.format(file_path.split('.')[0])), key=os.path.basename)

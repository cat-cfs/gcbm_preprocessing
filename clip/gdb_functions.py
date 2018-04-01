import logging, glob, os, shutil

class GDBFunctions(object):

    def __init__(self, arcpy):
        self.arcpy = arcpy

    def createWorkspace(self, new_workspace):
        """
        create a new GDB workspace at the path specified by new_workspace
        param new_workspace the path to a gdb file
        """
        if '.gdb' in os.path.basename(new_workspace):
            if os.path.exists(os.path.dirname(new_workspace)):
                self.arcpy.CreateFileGDB_management(os.path.dirname(new_workspace), os.path.basename(new_workspace).split('.')[0])
            else:
                os.makedirs(os.path.dirname(new_workspace))
                self.arcpy.CreateFileGDB_management(os.path.dirname(new_workspace), os.path.basename(new_workspace).split('.')[0])
        else:
            os.makedirs(new_workspace)

    def reproject(self, orig_workspace, new_workspace, name=None):
        """
        Project the layer at path orig_workspace ( NAD 1983) into the layer at path new_workspace (WGS 1984)
        param orig_workspace path to a GDB in NAD 1983
        param new_workspace path to the new GDB layer created by this function
        """
        logging.info('Starting process: reproject from {} to {}'.format(orig_workspace, new_workspace))
        if not os.path.exists(new_workspace):
            self.createWorkspace(new_workspace)
        if new_workspace==self.getWorkspace() and name==None:
            raise ValueError('Error: Cannot overwrite. Specify a new workspace or a new layer name.')

        self.arcpy.env.overwriteOutput = True
        transform_method = "WGS_1984_(ITRF00)_To_NAD_1983"
        output_proj = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]"
        logging.info("Reprojecting {}".format(orig_workspace))
        for layer in self.scan_for_layers(orig_workspace):
            logging.info('Reprojecting {}'.format(os.path.basename(layer)))
            if name==None:
                if '.tif' in os.path.basename(layer):
                    self.arcpy.ProjectRaster_management(layer, os.path.join(new_workspace, os.path.basename(layer)), output_proj, "", "", transform_method, "", "")
                else:
                    self.arcpy.Project_management(layer, os.path.join(new_workspace, os.path.basename(layer)), output_proj, transform_method, "", "NO_PRESERVE_SHAPE", "","NO_VERTICAL")
            else:
                if '.tif' in os.path.basename(layer):
                    self.arcpy.ProjectRaster_management(layer, os.path.join(new_workspace, os.path.basename(layer)), output_proj, "", "", transform_method, "", "")
                else:
                    self.arcpy.Project_management(layer, os.path.join(new_workspace, name), output_proj, transform_method, "", "NO_PRESERVE_SHAPE", "","NO_VERTICAL")
                break
        self._workspace = new_workspace
        logging.info("Done")

    def clip(self, workspace, workspace_filter, clip_feature, clip_feature_filter, new_workspace, name=None):

        if not os.path.exists(new_workspace):
            self.createWorkspace(new_workspace)
        if new_workspace==workspace and name==None:
            raise ValueError('Error: Cannot overwrite. Specify a new workspace or a new layer name.')
        logging.info("Clipping {0} to {1}...".format(workspace, new_workspace))

        self.arcpy.env.workspace = workspace
        self.arcpy.env.overwriteOutput = True
        self.arcpy.MakeFeatureLayer_management(clip_feature, 'clip_to', clip_feature_filter)
        if int(self.arcpy.GetCount_management('clip_to').getOutput(0)) < 1:
            raise Exception('Invalid clip feature. No selection from filter')
        for layer in self.scan_for_layers(workspace, workspace_filter):
            self.arcpy.MakeFeatureLayer_management(layer, 'clip')
            if self.arcpy.GetInstallInfo()['Version'] == '10.1':
                self.arcpy.SelectLayerByLocation_management('clip', "INTERSECT", 'clip_to', "", "NEW_SELECTION")
            else:
                self.arcpy.SelectLayerByLocation_management('clip', "INTERSECT", 'clip_to', "", "NEW_SELECTION", "NOT_INVERT")
            if name==None:
                logging.info('Clipping {}, saving to {}'.format(os.path.basename(layer),os.path.join(new_workspace,os.path.basename(layer))))
                self.arcpy.FeatureClassToFeatureClass_conversion('clip', new_workspace, os.path.basename(layer))
            else:
                logging.info('Clipping {}, saving to {}'.format(os.path.basename(layer),os.path.join(new_workspace, name)))
                self.arcpy.FeatureClassToFeatureClass_conversion('clip', new_workspace, name)
                break
        self.arcpy.Delete_management('clip_to')
        self._workspace = new_workspace
        logging.info("Done")

    def clipCutPolys(self, workspace, workspace_filter, clip_feature, clip_feature_filter, new_workspace, name=None):
        if not os.path.exists(new_workspace):
            self.createWorkspace(new_workspace)
        if new_workspace==workspace and name==None:
            logging.error('Error: Cannot overwrite. Specify a new workspace or a new layer name.')
            raise Exception('Error: Cannot overwrite. Specify a new workspace or a new layer name.')
        logging.info("Clipping {0} to {1}".format(workspace, new_workspace))
        self.arcpy.env.workspace = workspace
        self.arcpy.env.overwriteOutput = True
        self.arcpy.MakeFeatureLayer_management(clip_feature, 'clip_to', clip_feature_filter)
        for layer in self.scan_for_layers(workspace, workspace_filter):
            self.arcpy.MakeFeatureLayer_management(layer, 'clip')
            if name==None:
                logging.info('Clipping(cut polygons) {}, saving to {}'.format(os.path.basename(layer),os.path.join(new_workspace, os.path.basename(layer))))
                self.arcpy.Clip_analysis('clip', 'clip_to', os.path.join(new_workspace, os.path.basename(layer)))
            else:
                logging.info('Clipping(cut polygons) {}, saving to {}'.format(os.path.basename(layer),os.path.join(new_workspace, name)))
                self.arcpy.Clip_analysis('clip', 'clip_to', os.path.join(new_workspace, name))
                break
        self.arcpy.Delete_management('clip_to')
        self._workspace = new_workspace
        logging.info("Done")

    def copy(self, workspace, workspace_filter, new_workspace):
        if not os.path.exists(new_workspace):
            self.createWorkspace(new_workspace)
        if new_workspace==workspace:
            logging.error('Error: Cannot overwrite. Specify a new workspace or a new layer name.')
            raise Exception('Error: Cannot overwrite. Specify a new workspace or a new layer name.')
        logging.info("copy {0} to {1}".format(workspace, new_workspace))
        for layer in self.scan_for_layers(workspace, workspace_filter):
            logging.info('Copying {}, saving to {}'.format(os.path.basename(layer),os.path.join(new_workspace, os.path.basename(layer))))
            if '.gdb' in workspace:
                self.arcpy.env.workspace = workspace
                self.arcpy.FeatureClassToFeatureClass_conversion(os.path.basename(layer), new_workspace, os.path.basename(layer))
            else:
                for file in self.scan_for_files(workspace, os.path.basename(layer).split('.')[0]):
                    shutil.copyfile(file, os.path.join(new_workspace, os.path.basename(file)))
        self._workspace = new_workspace
        logging.info('Done')

    def createWorkspace(self, new_workspace):
        """
        create a new GDB workspace at the path specified by new_workspace
        param new_workspace the path to a gdb file or directory
        """
        logging.info("creating workspace '{}'".format(new_workspace))
        if '.gdb' in os.path.basename(new_workspace):
            if os.path.exists(os.path.dirname(new_workspace)):
                self.arcpy.CreateFileGDB_management(os.path.dirname(new_workspace), os.path.basename(new_workspace).split('.')[0])
            else:
                os.makedirs(os.path.dirname(new_workspace))
                self.arcpy.CreateFileGDB_management(os.path.dirname(new_workspace), os.path.basename(new_workspace).split('.')[0])
        else:
            os.makedirs(new_workspace)

    def scan_for_layers(self, workspace, filter):
        if '.gdb' in workspace:
            self.arcpy.env.workspace = workspace
            all = self.arcpy.ListFeatureClasses()
            return [os.path.join(workspace, layer) for layer in all if layer==filter]
        return sorted(glob.glob(os.path.join(workspace, filter)), key=os.path.basename)

    def scan_for_files(self, workspace, name):
        return sorted(glob.glob(os.path.join(workspace, '{}*'.format(name))), key=os.path.basename)

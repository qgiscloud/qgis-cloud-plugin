from builtins import str
from . import raster.raster_upload as raster_upload
from osgeo import gdal
from osgeo import osr
import osgeo.gdalconst as gdalc
from optparse import OptionParser, OptionGroup
import binascii
import glob
import math
import numpy
import os
import sys
import tempfile
 
class RasterUpload(QObject):
    def __init__(self, iface, raster_layer,  status_bar, progress_label, api, db_connections):
        QObject.__init__(self)
        self.iface = iface
        self.status_bar = status_bar
        self.progress_label = progress_label
        self.api = api
        self.db_connections = db_connections
        self.out_file = tempfile.NamedTemporaryFile(delete=False)
    
        # BEGIN
        self.out_file.write('BEGIN;\n')
    
        # Base raster schema
    # DROP TABLE
        sql = raster_upload.make_sql_drop_raster_table(table)
        self.out_file.write(sql)

    # CREATE TABLE
        sql = raster_upload.make_sql_create_table(opts)
        self.out_file.write(sql)
                  
        # INSERT
        i = 0
    
        # Burn all specified input raster files into single WKTRaster table
        gt = None
        for infile in raster:
            filelist = glob.glob(infile)
            assert len(filelist) > 0, "No input raster files found for '" + str(infile) + "'"
    
            for filename in filelist:
                logit("MSG: Dataset #%d: %s\n" % (i + 1, filename))
                
                # Write raster data to WKB and send it to opts.output
                gt = raster_upload.wkblify_raster(opts, filename.replace( '\\', '/') , i, gt)
                i += 1
    
        # INDEX
        if opts.index and SUMMARY is not None:
            sql = raster_upload.make_sql_create_gist(SUMMARY[0][0], opts.column)
            opts.output.write(sql)
        
        # COMMIT
        opts.output.write('END;\n')
    
        # VACUUM
        if opts.vacuum and SUMMARY is not None:
            sql = raster_upload.make_sql_vacuum(SUMMARY[0][0])
            opts.output.write(sql)
    

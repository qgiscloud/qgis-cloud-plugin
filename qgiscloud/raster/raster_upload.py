################################################################################
# Copyright (C) 2009-2010 Mateusz Loskot <mateusz@loskot.net>
# Copyright (C) 2009-2011 Pierre Racine <pierre.racine@sbf.ulaval.ca>
# Copyright (C) 2009-2010 Jorge Arevalo <jorge.arevalo@deimos-space.com>
#
# Modified for QGIS Cloud Plugin April 2016 by Horst Duester <horst.duester@sourcepole.ch>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
################################################################################
#
from qgis.PyQt.QtCore import QObject, QFileInfo
from qgis.PyQt.QtWidgets import QApplication,  QMessageBox
from osgeo import gdal
import osgeo.gdalconst as gdalc
from io import StringIO
from psycopg2 import sql as psycopg2_sql
from qgiscloud.db_connections import DbConnections
import binascii
import math
import numpy
import os
import sys

################################################################################
# CONSTANTS - DO NOT CHANGE

# Endianness enumeration
NDR = 1 # Little-endian
XDR = 0 # Big-endian
g_rt_version = 0
g_rt_endian = NDR
g_rt_column = 'rast'
g_rt_catalog = ''
g_rt_schema = 'public'

################################################################################
# UTILITIES
VERBOSE = False
SUMMARY = []
CREATE_OVERVIEWS = True

class RasterUpload(QObject):
    def __init__(self, conn, cursor, raster, max_size, psycopg2_version, progress_label, progress_bar):
        QObject.__init__(self)
        self.cursor = cursor
        self.conn = conn
        self.psycopg2_version = psycopg2_version
        self.progress_label = progress_label
        self.progress_bar = progress_bar
        self.progress_bar.setValue(0)
        self.messages = ""

        opts = {}
        opts['version'] = g_rt_version
        opts['endian'] = NDR
        opts['column'] = 'rast'
        opts['create_table'] = 1
        opts['drop_table'] = 1
        opts['overview_level'] = 1
        opts['block_size'] = 'auto'
        opts['band'] = None
        opts['register'] = None

        # Create PostGIS Raster Tool Functions
        raster_tools_file = "%s/raster_tools.sql" % os.path.dirname(__file__)
        with open(raster_tools_file) as f:
            sql = f.read().encode('ascii',errors='ignore')
            f.close()

        self.cursor.execute(sql)
        self.conn.commit()

        i = 0

        # Burn all specified input raster files into single WKTRaster table
        gt = None
        layer_info = raster
        opts['srid'] = layer_info['layer'].dataProvider().crs().postgisSrid()
        infile = layer_info['data_source']

        file_info = QFileInfo(infile)
        file_size = file_info.size()
        size = DbConnections().db_size()
        file_size /= 1024 * 1024
        size = size + file_size

        if size > float(max_size):
            QMessageBox.warning(None, self.tr("Database full"), self.tr("Upload would exceeded the maximum database size for your current QGIS Cloud plan. Please free up some space or upgrade your QGIS Cloud plan."))
            return False

        opts['schema_table'] = "\"%s\".\"%s\"" % (layer_info['schema_name'],  layer_info['table_name'])
        opts['table'] = layer_info['table_name']
        opts['schema'] =  layer_info['schema_name']

        self.progress_label.setText(self.tr("Creating table '{table}'...").format(table=opts['schema_table'].replace('"',  '')))
        QApplication.processEvents()

        self.cursor.execute(self.make_sql_drop_raster_table(opts['schema_table']))
        self.conn.commit()

        self.cursor.execute(self.make_sql_create_table(opts,  opts['schema_table']))
        self.conn.commit()

        gt = self.wkblify_raster(opts,  infile.replace( '\\', '/') , i, gt)
        i += 1

        self.cursor.execute(self.make_sql_create_gist(opts['schema_table'],  opts['column']))
        self.conn.commit()

   # create raster overviews
        if CREATE_OVERVIEWS:
            for level in [2, 4, 8, 16, 32, 64, 128, 256]:

                sql = 'drop table if exists "%s"."o_%d_%s"' %(opts['schema'],  level,  opts['table'])
                self.cursor.execute(sql)
                self.conn.commit()

                sql = "select st_createoverview_qgiscloud('%s'::text, '%s'::name, %d)" % (opts['schema_table'].replace('"',  ''),  opts['column'],  level)
                self.progress_label.setText(self.tr("Creating overview-level {level} for table '{table}'...").format(level=level,  table=opts['schema_table'].replace('"',  '')))
                QApplication.processEvents()
                self.cursor.execute(sql)
                self.conn.commit()

                index_table = '"{schema}"."o_{level}_{table}"'.format(
                                    schema = opts['schema'],
                                    level = level,
                                    table = opts['table'])

                self.progress_label.setText(self.tr("Creating GIST Index for table '{table}'...").format(table=opts['schema_table'].replace('"',  '')))
                self.cursor.execute(self.make_sql_create_gist(index_table,  opts['column']))
                self.conn.commit()

        self.progress_label.setText(self.tr("Registering raster columns of table '%s'..." % (opts['schema_table'].replace('"',  ''))))
        QApplication.processEvents()
        self.cursor.execute(self.make_sql_addrastercolumn(opts))
        self.conn.commit()


    ################################################################################

    def is_nan(self,  x):
        if sys.hexversion < 0x02060000:
            return str(float(x)).lower() == 'nan'
        else:
            return math.isnan(x)

    def logit(self,  msg):
        """If verbose mode requested, sends extra progress information to stderr"""
        if VERBOSE is True:
            pass
#            sys.stderr.write(msg)


    def gdt2pt(self,  gdt):
        """Translate GDAL data type to WKT Raster pixel type."""
        pixtypes = {
            gdalc.GDT_Byte    : { 'name': 'PT_8BUI',  'id':  4 },
            gdalc.GDT_Int16   : { 'name': 'PT_16BSI', 'id':  5 },
            gdalc.GDT_UInt16  : { 'name': 'PT_16BUI', 'id':  6 },
            gdalc.GDT_Int32   : { 'name': 'PT_32BSI', 'id':  7 },
            gdalc.GDT_UInt32  : { 'name': 'PT_32BUI', 'id':  8 },
            gdalc.GDT_Float32 : { 'name': 'PT_32BF',  'id': 10 },
            gdalc.GDT_Float64 : { 'name': 'PT_64BF',  'id': 11 }
            }

        # XXX: Uncomment these logs to debug types translation
        #logit('MSG: Input GDAL pixel type: %s (%d)\n' % (gdal.GetDataTypeName(gdt), gdt))
        #logit('MSG: Output WKTRaster pixel type: %(name)s (%(id)d)\n' % (pixtypes.get(gdt, 13)))

        return pixtypes.get(gdt, 13)

    def pt2numpy(self,  pt):
        """Translate GDAL data type to NumPy data type"""
        ptnumpy = {
            gdalc.GDT_Byte   : numpy.uint8,
            gdalc.GDT_Int16  : numpy.int16,
            gdalc.GDT_UInt16  : numpy.uint16,
            gdalc.GDT_Int32  : numpy.int32,
            gdalc.GDT_UInt32 : numpy.uint32,
            gdalc.GDT_Float32: numpy.float32,
            gdalc.GDT_Float64: numpy.float64
            }
        return ptnumpy.get(pt, numpy.uint8)

    def pt2fmt(self,  pt):
        """Returns binary data type specifier for given pixel type."""
        fmttypes = {
            4: 'B', # PT_8BUI
            5: 'h', # PT_16BSI
            6: 'H', # PT_16BUI
            7: 'i', # PT_32BSI
            8: 'I', # PT_32BUI
            10: 'f', # PT_32BF
            11: 'd'  # PT_64BF
            }
        return fmttypes.get(pt, 'x')


    def fmt2printfmt(self,  fmt):
        """Returns printf-like formatter for given binary data type sepecifier."""
        fmttypes = {
            'B': '%d', # PT_8BUI
            'h': '%d', # PT_16BSI
            'H': '%d', # PT_16BUI
            'i': '%d', # PT_32BSI
            'I': '%d', # PT_32BUI
            'f': '%.15f', # PT_32BF
            'd': '%.15f', # PT_64BF
            's': '%s'
            }
        return fmttypes.get(fmt, 'f')

    def parse_block_size(self,  options,  ds):
        if options['block_size'] == 'auto':
            return self.calc_tile_size(ds)

        else:
          wh = options['block_size'].split('x')
          if len(wh) != 2:
              wh = options['block_size'].split('X')

          return ( int(wh[0]), int(wh[1]) )

    ################################################################################
    # SQL OPERATIONS

    def quote_sql_value(self,  value):

        if len(value) > 0 and value[0] != "'" and value[:-1] != "'":
            sql = "'" + str(value) + "'"
        else:
            sql = value
        return sql

    def quote_sql_name(self,  name):
        if name[0] != "\"" and name[:-1] != "\"":
            sql = "\"" + str(name) + "\""
        else:
            sql = name
        return sql

    def make_sql_value_array(self,  values):
        sql = "ARRAY["
        for v in values:
            if type(v) == str:
                sql += self.quote_sql_value(v) + ","
            else:
                sql += str(v) + ','
        sql = sql[:-1] # Trim comma
        sql += "]"
        return sql

    def make_sql_schema_table_names(self,  schema_table):
        st = schema_table.split('.')
        return (st[0], st[1])

    def make_sql_full_table_name(self,  schema_table):
        st = self.make_sql_schema_table_names(schema_table)
        table = "%s.%s" % (st[0], st[1])
        return table

    def make_sql_table_name(self,  schema_table):
        st = schema_table.split('.')
        return st[1].replace('"',  '')

    def make_sql_drop_table(self,  table):
        sql = "DROP TABLE IF EXISTS %s CASCADE;\n" \
              % self.make_sql_full_table_name(table)
        self.logit("SQL: %s" % sql)
        return sql

    def make_sql_drop_raster_table(self,  schema_table):

        st = self.make_sql_schema_table_names(schema_table)

        if len(st[0]) == 0:
            target = "public.%s" % st[1]
        else:
            target = "%s.%s" % (st[0], st[1])
        sql = "DROP TABLE IF EXISTS %s;\n" % target
        return sql


    def make_sql_create_table(self,  options, table,  is_overview = False):
        sql = "create schema if not exists \"%s\";" % options['schema']
        sql += "CREATE TABLE %s (rid bigserial PRIMARY KEY, %s RASTER);\n" \
              % (self.make_sql_full_table_name(table), self.quote_sql_name(options['column']))
        return sql


    def make_sql_create_gist(self,  table, column):
        gist_table = self.make_sql_table_name(table)
        target_table = self.make_sql_full_table_name(table)

        sql = "CREATE INDEX \"%s_%s_gist_idx\" ON %s USING GIST (st_convexhull(%s));\n" % \
              (gist_table, column, target_table, column)

        return sql;


    def make_sql_addrastercolumn(self,  options):
        ts = self.make_sql_schema_table_names(options['schema_table'])
        schema = ts[0].replace('"', '')
        table = ts[1].replace('"', '')

        sql = "SELECT AddRasterConstraints('%s','%s','%s',TRUE,TRUE,TRUE,TRUE,TRUE,TRUE,FALSE,TRUE,TRUE,TRUE,TRUE,TRUE);" \
                   % (schema,  table,  options['column'])
        return sql

#    def make_sql_create_raster_overviews(self,  options):
#
#        sql = ""
#
#        for level in options['overview_level'].split(","):
#          sql += "select st_createoverview('%s'::regclass, '%s'::name, %s);\n" % (options['schema_table'],  'rast',  level)
#
#        return sql


#    def make_sql_register_overview(self,  options, ov_table, ov_factor):
#
#        r_table = self.make_sql_table_name(ov_table)
#
#        sql = "SELECT AddOverviewConstraints('%s','%s', '%s', '%s','%s','%s',%d);" \
#            % (options['schema'],  r_table,  options['column'],  options['schema'],  options['table'],  options['column'],  ov_factor)
#
#        return sql
#
#    def make_sql_vacuum(self,  table):
#        sql = 'VACUUM ANALYZE ' + self.make_sql_full_table_name(table) + ';\n'
#        return sql

    ################################################################################
    # RASTER OPERATIONS

    def calculate_overviews(self,  ds, band_from = None, band_to = None):

        if band_from is None:
            band_from = 0
        if band_to is None:
            band_to = ds.RasterCount

        nov = 0
        for i in range(band_from, band_to + 1):
            n = ds.GetRasterBand(i).GetOverviewCount()
            if 0 == nov:
                nov = n

        return nov



    def calculate_grid_size(self,  raster_size, block_size):
        """Dimensions of grid made up with blocks of requested size"""
        # Exact number of grid dimensions
        nx = float(raster_size[0]) / float(block_size[0])
        ny = float(raster_size[1]) / float(block_size[1])

        return ( int(round(nx)), int(round(ny)))

    def calculate_block_pad_size(self,  band, xoff, yoff, block_size):
        """Calculates number of columns [0] and rows [1] of padding"""
        xpad = 0
        ypad= 0
        block_bound = ( xoff + block_size[0], yoff + block_size[1] )

        if block_bound[0] > band.XSize:
            xpad = block_bound[0] - band.XSize
        if block_bound[1] > band.YSize:
            ypad = block_bound[1] - band.YSize

        return (xpad, ypad)

    def get_gdal_geotransform(self,  ds):
        gt = list(ds.GetGeoTransform())
        return tuple(gt)

    def calculate_geoxy(self,  gt, xy):
        """Calculate georeferenced coordinate from given x and y"""

        xgeo = gt[0] + gt[1] * xy[0] + gt[2] * xy[1];
        ygeo = gt[3] + gt[4] * xy[0] + gt[5] * xy[1];

        return (xgeo, ygeo)

    def calculate_geoxy_level(self,  gt, xy, level):

        # Update pixel resolution according to overview level
        newgt = ( gt[0], gt[1] * float(level), gt[2], gt[3], gt[4], gt[5] * float(level) )

        return self.calculate_geoxy(newgt, xy)

    def calculate_bounding_box(self,  ds, gt):
        """Calculate georeferenced coordinates of spatial extent of raster dataset"""

        # UL, LL, UR, LR
        dim = ( (0,0),(0,ds.RasterYSize),(ds.RasterXSize,0),(ds.RasterXSize,ds.RasterYSize) )

        ext = (self.calculate_geoxy(gt, dim[0]), self.calculate_geoxy(gt, dim[1]),
               self.calculate_geoxy(gt, dim[2]), self.calculate_geoxy(gt, dim[3]))

        return ext

    def check_hex(self,  hex, bytes_size = None):
        size = len(hex)
        if bytes_size is not None:
            n = int(size / 2)

    def calc_tile_size(self,  ds):
        dimX = ds.RasterXSize
        dimY = ds.RasterYSize
        tileX = dimX
        tileY = dimY
        min = 30
        max = 100

        for j in range(0, 2):
                _i = 0
                _r = -1


                if j < 1 and dimX <= max:
                        tileX = dimX
                        continue
                elif dimY <= max:
                        tileY = dimY
                        continue


                for i in range (max,  min-1,  -1):
                        if j < 1:
                            d = dimX // i
                            r = dimX / i
                        else:
                            d = dimY // i
                            r = dimY /  i

                        r = r -  float (d)
                        if  abs(_r   -  (-1)) <= 0.001 or r < _r  or  abs(_r   -  r ) <= 0.001:
                            _r = r
                            _i = i

                if j < 1:
                   tileX = _i
                else:
                   tileY = _i

        return int (tileX),  int (tileY)



    def dump_block_numpy(self,  pixels):

        i = 0
        for row in range (0, len(pixels)):
            s = binascii.hexlify(pixels[row])
            i = i + 1

    def fetch_band_nodata(self,  band, default = 0):

        nodata = default
        try:
            if band.GetNoDataValue() is not None:
                nodata = band.GetNoDataValue()
        except:
            return 0

        return nodata

    def wkblify(self,  fmt, data):
        """Writes raw binary data into HEX-encoded string using binascii module."""
        import struct

        # Binary to HEX
        try:
            fmt_little = '<' +fmt
            hexstr = binascii.hexlify(struct.pack(fmt_little, data)).upper().decode('utf-8')
        except:
            if fmt in ['H',  'h',  'i',  'I', 'B']:
                data = int(data)
                fmt_little = '<' +fmt
                hexstr = binascii.hexlify(struct.pack(fmt_little, data)).upper().decode('utf-8')

        return hexstr

    def wkblify_raster_header(self,  options, ds, level, ulp, xsize = None, ysize = None):
        """Writes WKT Raster header based on given GDAL into HEX-encoded WKB."""

        if xsize is None or ysize is None:
            xsize = ds.RasterXSize
            ysize = ds.RasterYSize

        # Collect GeoReference information
        gt = self.get_gdal_geotransform(ds)
        ul = self.calculate_geoxy(gt, (ulp[0], ulp[1]))
        rt_ip = ( ul[0], ul[1] )
        rt_skew = ( gt[2], gt[4] )
        rt_scale = ( gt[1] * level, gt[5] * level )

        # Burn input raster as WKTRaster WKB format
        hexwkb = ''
        ### Endiannes
        hexwkb += self.wkblify('B', options['endian'])
        ### Version
        hexwkb += self.wkblify('H', options['version'])
        ### Number of bands
        if options['band'] is not None and options['band'] > 0:
            hexwkb += self.wkblify('H', 1)
        else:
            hexwkb += self.wkblify('H', ds.RasterCount)
#        self.check_hex(hexwkb, 5)
        ### Georeference
        hexwkb += self.wkblify('d', rt_scale[0])
        hexwkb += self.wkblify('d', rt_scale[1])
        hexwkb += self.wkblify('d', rt_ip[0])
        hexwkb += self.wkblify('d', rt_ip[1])
        hexwkb += self.wkblify('d', rt_skew[0])
        hexwkb += self.wkblify('d', rt_skew[1])
        hexwkb += self.wkblify('i', options['srid'])
#        self.check_hex(hexwkb, 57)
        ### Number of columns and rows
        hexwkb += self.wkblify('H', xsize)
        hexwkb += self.wkblify('H', ysize)
#        self.check_hex(hexwkb, 61)

        return hexwkb

    def wkblify_band_header(self,  options, band):
        """Writes band header into HEX-encoded WKB"""

        hexwkb = ""

        first4bits = 0

        # If the register option is enabled, set the first bit to 1
#        if options['register']:
#            first4bits = 128

        nodata = band.GetNoDataValue()
        # If there is no nodata value, set it to 0. Otherwise set the HasNodata bit to 1
        if nodata is not None:
            first4bits += 64
        else:
            nodata = 0

        # Encode pixel type
        pixtype = self.gdt2pt(band.DataType)['id']
        hexwkb += self.wkblify('B', pixtype + first4bits)

        # Encode nodata value (or Zero, if nodata unavailable)
        hexwkb += self.wkblify(self.pt2fmt(pixtype), nodata)

#        self.check_hex(hexwkb)
        return hexwkb

    def wkblify_band(self,  options, band, level, xoff, yoff, read_block_size, block_size, infile, bandidx):
        """Writes band of given GDAL dataset into HEX-encoded WKB for WKT Raster output."""

        hexwkb = ''

        if options['register']:
            hexwkb += self.wkblify('B', bandidx - 1)
            filepath = os.path.abspath(infile.replace('\\', '\\\\'))
            hexwkb += self.wkblify(str(len(filepath)) + 's', filepath)
            hexwkb += self.wkblify('B', 0)
        else:
            # In-db raster

            # Right most column and bottom most row of blocks have
            # portions that extend beyond the raster
            read_padding_size = self.calculate_block_pad_size(band, xoff, yoff, read_block_size)
            valid_read_block_size = ( read_block_size[0] - read_padding_size[0],
                                      read_block_size[1] - read_padding_size[1] )


            if read_padding_size[0] > 0 or read_padding_size[1] > 0:
                target_block_size = (valid_read_block_size[0] // level, valid_read_block_size[1] //level)
                target_padding_size = (read_padding_size[0] //level, read_padding_size[1] //level)
            else:
                target_block_size = block_size
                target_padding_size = ( 0, 0 )


            pixels = band.ReadAsArray(xoff, yoff, valid_read_block_size[0], valid_read_block_size[1],
                                      target_block_size[0], target_block_size[1])


            out_pixels = numpy.zeros((block_size[1], block_size[0]), self.pt2numpy(band.DataType))

            if target_padding_size[0] > 0 or target_padding_size[1] > 0:

                ysize_read_pixels = len(pixels)
                nodata_value = self.fetch_band_nodata(self,  band)

                # Apply columns padding
                pad_cols = numpy.full(target_padding_size[0],  nodata_value)

                for row in range (0, ysize_read_pixels):
                    out_line = numpy.append(pixels[row], pad_cols)
                    out_pixels[row] = out_line

                # Fill rows padding with nodata value
                for row in range(ysize_read_pixels, int(ysize_read_pixels + target_padding_size[1])):
                    out_pixels[row].fill(nodata_value)
            else:
                out_pixels = pixels

            hexwkb = binascii.hexlify(out_pixels).decode('utf-8')

#        self.check_hex(hexwkb)
        return hexwkb

    def wkblify_raster_level(self,  options, ds, level, band_range, infile, i):

        band_from = band_range[0]
        band_to = band_range[1]

        # Collect raster and block dimensions
        raster_size = ( ds.RasterXSize, ds.RasterYSize )
        if options['block_size'] is not None:
            block_size = self.parse_block_size(options,  ds)
            read_block_size = ( block_size[0] * level, block_size[1] * level)
            grid_size = self.calculate_grid_size(raster_size, read_block_size)
        else:
            block_size = raster_size # Whole raster as a single block
            read_block_size = block_size
            grid_size = (1, 1)

        gen_table = options['schema_table']

        # Write (original) raster to hex binary output
        tile_count = 0
        hexwkb = ''
        self.progress_label.setText(self.tr("Uploading tiles..."))
        importString = ""
        sum_tiles = grid_size[0]*grid_size[1]
        self.progress_bar.setMaximum(sum_tiles)

        copy_table_sql = ""
        if self.psycopg2_version >= 20900:
            # build SQL for copy_expert call
            copy_table_sql = psycopg2_sql.SQL(
                "COPY {schema}.{table} FROM STDIN"
            ).format(
                schema=psycopg2_sql.Identifier(options['schema']),
                table=psycopg2_sql.Identifier(options['table'])
            )

        copy_size = 500

        for ycell in range(0, grid_size[1]):
            for xcell in range(0, grid_size[0]):

                xoff = xcell * read_block_size[0]
                yoff = ycell * read_block_size[1]

                if options['block_size'] is not None:
                    hexwkb = '' # Reset buffer as single INSERT per tile is generated
                    hexwkb += self.wkblify_raster_header(options, ds, level, (xoff, yoff),
                                                    block_size[0], block_size[1])
                else:
                    hexwkb += self.wkblify_raster_header(options, ds, level, (xoff, yoff))

                for b in range(band_from, band_to):
                    band = ds.GetRasterBand(b)

                    hexwkb += self.wkblify_band_header(options, band)
                    hexwkb += self.wkblify_band(options, band, level, xoff, yoff, read_block_size, block_size, infile, b)

                # Creating COPY String
                importString += str(tile_count)+"\t"+hexwkb+"\n"
                tile_count = tile_count + 1

            # Periodically update ui
                if (tile_count % copy_size) == 0:
                    if self.psycopg2_version >= 20900:
                        self.cursor.copy_expert(copy_table_sql, StringIO(importString))
                    else:
                        self.cursor.copy_from(StringIO(importString), '%s' % gen_table)
                    importString = ""
                    self.progress_bar.setValue(tile_count)
#                    self.progress_label.setText(self.tr("{table}: {count} of {sum_tiles} tiles uploaded").format(
#                        table=gen_table,
#                        count=tile_count,
#                        sum_tiles= sum_tiles))

                    QApplication.processEvents()

        self.progress_bar.setValue(sum_tiles)
        if self.psycopg2_version >= 20900:
            self.cursor.copy_expert(copy_table_sql, StringIO(importString))
        else:
            self.cursor.copy_from(StringIO(importString), '%s' % gen_table)
        self.conn.commit()

        self.progress_label.setText(self.tr("Calculating raster params for {sum_tiles} tiles ...").format(
            sum_tiles= sum_tiles))
        QApplication.processEvents()

        self.cursor.execute(self.make_sql_addrastercolumn(options))
        self.conn.commit()

        return (gen_table, tile_count)

    def wkblify_raster(self,  options, infile, i, previous_gt = None):
        """Writes given raster dataset using GDAL features into HEX-encoded of
        WKB for WKT Raster output."""

        # Open source raster file
        ds = gdal.Open(infile, gdalc.GA_ReadOnly);
        if ds is None:
            QMessageBox.critical(None,'Error:','Cannot open input file: ' + str(infile))

# By default, translate all raster bands

# Calculate range for single-band request
        if options['band'] is not None and options['band'] > 0:
            band_range = ( options['band'], options['band'] + 1 )
        else:
            band_range = ( 1, ds.RasterCount + 1 )

        # Compare this px size with previous one
        current_gt = self.get_gdal_geotransform(ds)
        if previous_gt is not None:
            if previous_gt[1] != current_gt[1] or previous_gt[5] != current_gt[5]:
                QMessageBox.critical(None,'Error:', 'Cannot load raster with different pixel size in the same raster table')

        # Generate requested overview level (base raster if level = 1)
        summary = self.wkblify_raster_level(options, ds, options['overview_level'], band_range, infile, i)
        SUMMARY.append( summary )

        # Cleanup
        ds = None

        return current_gt

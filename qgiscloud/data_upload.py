# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DataUpload

 Copy local QGIS layers to QGISCloud database
                             -------------------
        begin                : 2011-09-21
        copyright            : (C) 2011 by Sourcepole
        email                : pka@sourcepole.ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

# NOTE: always convert features in OGR layers or PostGIS layers of type GEOMETRY to MULTI-type geometry, as geometry type detection of e.g. shapefiles is unreliable
"""
from qgis.PyQt.QtCore import Qt,  QObject, QVariant, QDate, QDateTime
from qgis.PyQt.QtWidgets import QMessageBox, QApplication,  QDialog
from qgis.PyQt.QtXml import QDomDocument
from qgis.core import *
from .db_connections import DbConnections
from .raster.raster_upload import RasterUpload
from .PGVectorLayerImport import PGVectorLayerImport
from .ui_overwrite_or_append_dialog import OverwriteOrAppendDialog
from psycopg2 import sql as psycopg2_sql
import re
from io import StringIO
import struct
import binascii


# get psycopg2 version
psycopg2_version = 0
try:
    from psycopg2 import __version__ as psycopg2_version_string
    m = re.match(r'\d+.\d+.\d+', psycopg2_version_string)
    if m:
        # convert version string to int, e.g. "2.9.1" -> 20901
        major, minor, micro = [int(v) for v in m.group(0).split('.')]
        psycopg2_version = major * 10000 + minor * 100 + micro
except Exception as e:
    QgsMessageLog.logMessage("Could not get psycopg2 version: %s" % e, "QGIS Cloud") 


class DataUpload(QObject):
    
    def __init__(self, iface, status_bar, progress_label, progress_bar,  api, db_connections):
        QObject.__init__(self)
        self.iface = iface
        self.status_bar = status_bar
        self.progress_label = progress_label
        self.progress_bar = progress_bar
        self.api = api
        self.db_connections = db_connections
        self.PROJECT_INSTANCE = QgsProject.instance()
        self.psycopg2_version = psycopg2_version

    def upload(self, db, data_sources_items, maxSize):
        import_ok = True
        layers_to_replace = {}
        raster_to_upload = {}

        self.status_bar.showMessage(self.tr("Uploading to database '{db}'...").format(db=db.database))
        QApplication.processEvents()

        messages = ""

        # Connect to database
        try:
            conn = db.psycopg_connection()
            cursor = conn.cursor()
        except Exception as e:
            raise RuntimeError("Connection to database failed %s" % str(e))

        for data_source, item in list(data_sources_items.items()):
            # Check available space, block if exceded
            size = DbConnections().db_size()

            if size > float(maxSize):
                QMessageBox.warning(None, self.tr("Database full"), self.tr("You have exceeded the maximum database size for your current QGIS Cloud plan. Please free up some space or upgrade your QGIS Cloud plan."))
                break

            # Layers contains all layers with shared data source
            layer = item['layers'][0]
            if layer.type() == QgsMapLayer.VectorLayer:
                if layer.isSpatial():
                    try:
                        auth = layer.crs().authid().split(':')[0]
                        srid = int(layer.crs().authid().split(':')[1])
                    except:
                        QMessageBox.warning(None, 
                                self.tr("Not Supported CRS %s" % layer.crs().authid()), 
                                self.tr("Layer %s does not have a supported CRS." % layer.name()))
                        srid = None
                        auth = None                                
                        break
                else:
                    srid = None
                    auth = None
                    
                geom_column = "wkb_geometry"
                wkbType = layer.wkbType()
                
                #Remove Virtual Fields from Layer Fieldlist
                fields = QgsFields()
                for f in QgsFields(layer.fields()):
                    i = layer.dataProvider().fieldNameIndex(f.name())
                    if i >= 0:
                        fields.append(f)
                        
# Check if database schema exists
                cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = '%s')" % item['schema'])
                schema_exists = cursor.fetchone()[0]
                
                if not schema_exists:
                    cursor.execute("create schema %s" % item['schema'])
                
                if wkbType == QgsWkbTypes.NoGeometry:
                    cloudUri = "dbname='%s' host=%s port=%d user='%s' password='%s' key='' table=\"%s\".\"%s\"" % (
                    db.database, db.host, db.port, db.username, db.password, item['schema'],  item['table'])
                    geom_column = ""
                else:
                    if not  QgsWkbTypes.isMultiType(wkbType):
                        wkbType = QgsWkbTypes.multiType(wkbType)

                    # Create table (pk='' => always generate a new primary key)
                    cloudUri = "dbname='%s' host=%s port=%d user='%s' password='%s' key='' table=\"%s\".\"%s\" (%s)" % (
                        db.database, db.host, db.port, db.username, db.password, item['schema'],  item['table'], geom_column
                    )

                self.progress_label.setText(self.tr("Creating table '{table}'...").format(table=item['table']))
                QApplication.processEvents()
                
                if wkbType != QgsWkbTypes.NoGeometry:
                    # Check if SRID is known on database, otherwise create record
                    cursor.execute("SELECT srid FROM public.spatial_ref_sys WHERE srid = %s" % srid)
                    if not cursor.fetchone():
                        try:
                            cursor.execute("INSERT INTO public.spatial_ref_sys VALUES ({srid},'{auth}',{srid},'{wktstr}','{projstr}')".format(
                                auth = auth, 
                                srid = srid,
                                wktstr = layer.crs().toWkt(),
                                projstr = layer.crs().toProj4()))
                            conn.commit()
                        except Exception as e:
                            conn.rollback()
                            import_ok &= False
                            messages += "Failed to create SRS record on database: " + str(e) + "\n"
                            continue

    #                cursor.close()

                # Ask user for overwriting existing table
                    sql = """SELECT exists( 
                                        SELECT table_name 
                                        FROM information_schema.tables 
                                        WHERE table_schema = '{}' and table_name = '{}')
                            """.format(item['schema'],  item['table'])
                cursor.execute(sql)
                table_exists = cursor.fetchone()[0]
                if table_exists:
                    dialog = OverwriteOrAppendDialog(item['schema'],  item['table'])
                    result = dialog.exec_()

                    if  result == QDialog.Accepted:
                        if dialog.choice == 'overwrite':
                            
                            # The postgres provider is terribly slow at creating tables with
                            # many attribute columns in QGIS < 2.9.0
                            vectorLayerImport = PGVectorLayerImport(db, conn,  cursor, cloudUri, fields, wkbType, srid, True)

                            if vectorLayerImport.hasError():
                                import_ok &= False
                                messages += "VectorLayerImport-Error: "+vectorLayerImport.errorMessage() + "\n"
                                continue
                        else:
                            vectorLayerImport = None

                copy_table_sql = ""
                if self.psycopg2_version >= 20900:
                    # build SQL for copy_expert call
                    copy_table_sql = psycopg2_sql.SQL(
                        "COPY {schema}.{table} FROM STDIN"
                    ).format(
                        schema=psycopg2_sql.Identifier(item['schema']),
                        table=psycopg2_sql.Identifier(item['table'])
                    )

                # Build import string
                attribs = list(range(0, fields.count()))
                count = 0
                importstr = bytearray()
                ok = True

                self.progress_label.setText(self.tr("Uploading features..."))
                QApplication.processEvents()
                n_layer_features = layer.featureCount()
                self.progress_bar.setMaximum(n_layer_features)
                
                for feature in layer.getFeatures():
                    f_geometry = feature.geometry()
                    f_geometry.convertToMultiType()
                    
                    # First field is primary key
                    importstr.extend(str(count).encode('utf-8'))
                    count += 1
                    if not feature.geometry():
                        if layer.isSpatial():
                            QgsMessageLog.logMessage(self.tr("Feature {id} of layer {layer} has no geometry").format(id=feature.id(), layer=layer.name()), "QGISCloud")
                            importstr.extend(b"\t" + b"\\N")
                    elif f_geometry.wkbType() != wkbType:
                        QgsMessageLog.logMessage(self.tr("Feature {id} of layer {layer} has wrong geometry type {type}").format(id=feature.id(), layer=layer.name(), type= QgsWkbTypes.displayString(feature.geometry().wkbType())), "QGISCloud")
                        importstr.extend(b"\t" + b"\\N")
                    else:
                        # Second field is geometry in EWKB Hex format
                        importstr.extend(b"\t" + self._wkbToEWkbHex(f_geometry.asWkb(), srid))

                    # Finally, copy data attributes
                    for attrib in attribs:
                        val = feature[attrib]
                        if val is None or isinstance(val, QVariant):
                            val = b"\\N"
                        elif isinstance(val, QDate) or isinstance(val, QDateTime):
                            val = bytearray(val.toString(Qt.ISODate).encode('utf-8'))
                            if not val:
                                val = b"\\N"
                        else:
                            if isinstance( val, list ):
                                listString = '{'
                                if len( val ) > 0:
                                    listString = listString + ('"' + '","'.join( val ) + '"')
                                listString = listString + '}'
                                val = listString

                            val = bytearray(str(val).encode('utf-8'))
                            val = val.replace(b'\x00', b'?')
                            val = val.replace(b'\\', b'\\\\')
                            val = val.replace(b'\t', b'\\t')
                            val = val.replace(b'\n', b'\\n')
                            val = val.replace(b'\r', b'\\r')

                        importstr += b"\t" + val

                    importstr += b"\n"

                    # Upload in chunks
                    self.progress_bar.setValue(count)
                    if (count % 100) == 0:
                        try:
                            if self.psycopg2_version >= 20900:
                                cursor.copy_expert(copy_table_sql, StringIO(importstr.decode('utf-8')))
                            else:
                                cursor.copy_from(StringIO(importstr.decode('utf-8')), '"%s"."%s"' % (item['schema'],  item['table']))
                        except Exception as e:
                            messages += str(e) + "\n"
                            ok = False
                            break
                            
                        importstr = bytearray()
                        self.progress_label.setText(self.tr("{table}: {count} features uploaded").format(
                            table=item['table'], count=count))
                        QApplication.processEvents()
                    # Periodically update ui
                    if (count % 10) == 0:
                        QApplication.processEvents()

                if ok and importstr:
                    try:
                        if self.psycopg2_version >= 20900:
                            cursor.copy_expert(copy_table_sql, StringIO(importstr.decode('utf-8')))
                        else:
                            cursor.copy_from(StringIO(importstr.decode('utf-8')), '"%s"."%s"' % (item['schema'],  item['table']))
                    except Exception as e:
                        messages += str(e) + "\n"
                        ok = False

                if ok:
                    try:
                        conn.commit()
                    except Exception as e:
                        messages += str(e) + "\n"
                        ok = False
                else:
                    conn.rollback()

                import_ok &= ok

                if ok:
                    for layer in item['layers']:
                        layers_to_replace[layer.id()] = {
                            'layer': layer,
                            'data_source': data_source,
                            'db_name': db.database,
                            'schema_name':item['schema'], 
                            'table_name': item['table'],
                            'geom_column': geom_column
                        }

                if dialog.choice == 'overwrite':
                    if wkbType != QgsWkbTypes.NoGeometry:
                        sql = 'create index "{1}_{2}_idx" on "{0}"."{1}" using gist ("{2}");'.format(item['schema'],  item['table'],  geom_column)
                        cursor.execute(sql)
                        conn.commit()
                    
            elif layer.type() == QgsMapLayer.RasterLayer:
                raster_to_upload = {
                            'layer': layer,
                            'data_source': layer.source(),
                            'db_name': db.database,
                            'schema_name': item['schema'], 
                            'table_name': item['table'],
                            'geom_column': 'rast'
                        }
                RasterUpload(conn, cursor, raster_to_upload, maxSize, self.psycopg2_version, self.progress_label, self.progress_bar)
                layers_to_replace[layer.id()] = raster_to_upload

        sql = """SELECT 'SELECT SETVAL(' || quote_literal(quote_ident(PGT.schemaname) || '.' || quote_ident(S.relname)) ||  
                            ', COALESCE(MAX(' ||quote_ident(C.attname)|| ')+1, 1) ) 
                                FROM ' || quote_ident(PGT.schemaname)|| '.' ||quote_ident(T.relname)|| ';' 
                        FROM pg_class AS S,      pg_depend AS D,      pg_class AS T,      pg_attribute AS C,      
                             pg_tables AS PGT, pg_namespace as PGNS 
                        WHERE S.relkind = 'S'     
                          AND S.oid = D.objid     
                          AND S.relnamespace = PGNS.oid 
                          AND PGNS.nspname = '{0}'     
                          AND D.refobjid = T.oid     
                          AND D.refobjid = C.attrelid     
                          AND D.refobjsubid = C.attnum     
                          AND T.relname = PGT.tablename     
                          AND schemaname = '{0}'     
                          AND tablename = '{1}' ORDER BY S.relname;""".format(item['schema'],  item['table'])
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        for row in rows:
            cursor.execute(row[0])
            

        cursor.close()
        conn.close()
        self._replace_local_layers(layers_to_replace)
        self.progress_label.setText("")
        if not import_ok:
            raise RuntimeError(str(messages))


    def _wkbToEWkbHex(self, wkb, srid, convertToMulti=False):
        try:
            wktType = struct.unpack("=i", wkb[1:5])[0] & 0xffffffff
            if not QgsWkbTypes.isMultiType(wktType):
                wktType = QgsWkbTypes.multiType(wktType) & 0xffffffff
                wkb = wkb[0] + struct.pack("=I", wktType) + struct.pack("=I", 1) + wkb                
        except:
            # Some platforms (Windows) complain when a long is passed to QGis.isMultiType
            # And some other platforms complain if not a long is passed...
            wktType = struct.unpack("=i", wkb[1:5])[0]

        # See postgis sources liblwgeom.h.in:
        # define WKBZOFFSET  0x80000000
        # define WKBMOFFSET  0x40000000
        # define WKBSRIDFLAG 0x20000000
        # define WKBBBOXFLAG 0x10000000
        if wktType >= 1000 and wktType < 2000:
            # Has Z
            wktType -= 1000
            wktType |= 0x80000000 | 0x20000000
        elif wktType >= 2000 and wktType < 3000:
            # Has M
            wktType -= 2000
            wktType |= 0x40000000 | 0x20000000
        elif wktType >= 3000 and wktType < 4000:
            # Has ZM
            wktType -= 3000
            wktType |= 0x80000000 | 0x40000000 | 0x20000000
        else:
            wktType |= 0x20000000
        try:
            ewkb = wkb[0:1] + struct.pack("=I", wktType) + struct.pack("=I", srid) + wkb[5:]
        except:
            ewkb = wkb[0:1] + struct.pack("=I", (wktType & 0xffffffff)) + struct.pack("=I", srid) + wkb[5:]
        return binascii.hexlify(ewkb)

    def _replace_local_layers(self, layers_to_replace):
        if len(layers_to_replace) > 0:
            root = QgsProject.instance().layerTreeRoot()
            
            #save custom layer order
            hasCustomLayerOrder = root.hasCustomLayerOrder()
            customLayerOrderIds = []
            if hasCustomLayerOrder:
                customLayerOrder = root.customLayerOrder()
                for layer in customLayerOrder:
                    customLayerOrderIds.append( layer.id() )
            
            self._replace_local_layers_in_layer_tree(root, layers_to_replace)
            
            #restore custom layer order
            if hasCustomLayerOrder:
                newCustomLayerOrder = []
                for oldId in customLayerOrderIds:
                    if oldId in layers_to_replace:
                        if 'new_layer_id' in layers_to_replace[oldId]:
                            newId = layers_to_replace[oldId]['new_layer_id']
                            newCustomLayerOrder.append( QgsProject.instance().mapLayer( newId ) )
                root.setCustomLayerOrder( newCustomLayerOrder )
        
    # recursive layer tree traversal
    def _replace_local_layers_in_layer_tree(self, node, layers_to_replace):
        if QgsLayerTree.isGroup(node):
            # traverse children of layer group
            for child_node in node.children():
                self._replace_local_layers_in_layer_tree(child_node, layers_to_replace)
        else:
            # layer node
            layer_id = node.layerId()
            if layer_id in layers_to_replace:
                layer_info = layers_to_replace[layer_id]
                newLayerId = self.replace_local_layer(
                    node,
                    layer_info['layer'],
                    layer_info['data_source'],
                    layer_info['db_name'],
                    layer_info['schema_name'], 
                    layer_info['table_name'],
                    layer_info['geom_column']
                )
                if newLayerId:
                    layer_info['new_layer_id'] = newLayerId

    def replace_local_layer(self, node, local_layer, data_source, db_name, schema_name,  table_name, geom_column):
        self.status_bar.showMessage(u"Replace layer %s ..." % local_layer.name())

        if local_layer.type() == QgsMapLayer.VectorLayer:
            # create remote layer
            uri = self.db_connections.cloud_layer_uri(db_name, schema_name,  table_name, geom_column)

            #Workaround for loading geometryless layers
            uri2 = QgsDataSourceUri(uri.uri().replace(' ()',  ''))

            remote_layer = QgsVectorLayer(uri2.uri(), local_layer.name(), 'postgres')
        elif local_layer.type() == QgsMapLayer.RasterLayer:
            uri = self.db_connections.cloud_layer_uri(db_name, schema_name,  table_name, geom_column)
            connString = "PG: dbname=%s host=%s user=%s password=%s port=%s mode=2 schema=%s column=rast table=%s" \
                  % (uri.database(), uri.host(),  uri.database(),  uri.password(),  uri.port(),  schema_name,  table_name )

            remote_layer = QgsRasterLayer( connString, local_layer.name() )

        if remote_layer.isValid():
            self.copy_layer_settings(local_layer, remote_layer)

            group_node = node.parent()

            # add remote layer
            self.PROJECT_INSTANCE.addMapLayer(remote_layer, False)
            idx = group_node.children().index(node)
            remote_layer_node = group_node.insertLayer(idx, remote_layer)
            remote_layer_node.setItemVisibilityChecked(node.isVisible())

            # remove local layer
            group_node.removeChildNode(node)

            self.status_bar.showMessage(u"Replaced layer %s" % remote_layer.name())
            return remote_layer.id()

    def copy_layer_settings(self, source_layer, target_layer):
        # copy filter

        if target_layer.type() == QgsVectorLayer:
            target_layer.setSubsetString(source_layer.subsetString())

        # copy symbology
        error = ""
        doc = QDomDocument()
        node = doc.createElement("symbology")
        doc.appendChild(node)
        source_layer.writeSymbology(node, doc, error,  QgsReadWriteContext())

        if not error:
            target_layer.readSymbology(node, error,  QgsReadWriteContext())
        if error:
            QMessageBox.warning(None, "Could not copy symbology", error)

        # copy scale based visibility
        try:
            target_layer.setScaleBasedVisibility(source_layer.hasScaleBasedVisibility())
        except:
            # Fall back to the deprecated function
            target_layer.toggleScaleBasedVisibility(source_layer.hasScaleBasedVisibility())
        target_layer.setMinimumScale(source_layer.minimumScale())
        target_layer.setMaximumScale(source_layer.maximumScale())

        #copy CRS
        target_layer.setCrs(source_layer.crs(), False)

    def schema_from_uri(self, uri):
        schema = uri.schema()
        if len(schema) == 0:
            schema = "public"
        return schema

    def show_api_error(self, result):
        if 'error' in result:
            QMessageBox.critical(None, "QGIS Cloud Error", "%s" % result['error'])
            self.status_bar.showMessage(u"Error")
            return True
        else:
            return False

    def table_exists_error(self, result):
        if 'error' in result:
            return re.search(r'PGError.*relation "([\w\s]*)" already exists', result['error']) != None
        else:
            return False

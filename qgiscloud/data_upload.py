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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtXml import *
from qgis.core import *
from db_connections import DbConnections
import os
import re
import psycopg2
from StringIO import StringIO
import struct
import binascii


class DataUpload:

    def __init__(self, iface, status_bar, progress_bar, progress_label, api, db_connections):
        self.iface = iface
        self.status_bar = status_bar
        self.progress_bar = progress_bar
        self.progress_label = progress_label
        self.api = api
        self.db_connections = db_connections
        pass

    def upload(self, db, data_sources_items, do_replace_local_layers):
        import_ok = True
        layers_to_replace = {}
        self.status_bar.showMessage(u"Uploading to database %s ..." % db.database)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.progress_label.setText("")
        self.progress_label.show()
        QApplication.processEvents()

        # Connect to database
        try:
            conn = db.psycopg_connection()
        except:
            return False

        for data_source, item in data_sources_items.iteritems():
            # Layers contains all layers with shared data source
            layer = item['layers'][0]
            fields = layer.pendingFields()
            srid = layer.crs().postgisSrid()
            geom_column = "wkb_geometry"
            wkbType = layer.wkbType()

            # Upload single types as multi-types
            convertToMulti = False
            if QGis.singleType(wkbType) == wkbType:
                    wkbType = QGis.multiType(wkbType)
                    convertToMulti = True

            # Create table (pk='' => always generate a new primary key)
            cloudUri = "dbname='%s' host=%s port=%d user='%s' password='%s' key='' table=\"public\".\"%s\" (%s)" % (
                db.database, db.host, db.port, db.username, db.password, item['table'], geom_column
            )

            self.progress_label.setText("Creating table '%s'..." % (item['table']))
            QApplication.processEvents()

            # TODO: Ask user for overwriting existing table
            vectorLayerImport = QgsVectorLayerImport(cloudUri, "postgres", fields, wkbType, layer.crs(), True)
            if vectorLayerImport.hasError():
                import_ok &= False
                continue
            # Create cursor
            cursor = conn.cursor()

            # Build import string
            attribs = [fields.field(i).name() for i in range(0, fields.count())]
            count = 0
            importstr = ""
            ok = True

            self.progress_label.setText("%s: %d features uploaded" % (item['table'], count))
            QApplication.processEvents()

            for feature in layer.getFeatures(QgsFeatureRequest()):
                # First field is primary key
                importstr += "%d" % count
                count += 1

                # Second field is geometry in EWKB Hex format
                importstr += "\t" + self._wkbToEWkbHex(feature.geometry().asWkb(), srid, convertToMulti)

                # Finally, copy data attributes
                for attrib in attribs:
                    val = feature.attribute(attrib)
                    if val is None or isinstance(val, QPyNullVariant):
                        importstr += "\t\\N"
                    else:
                        # Some strings
                        importstr += "\t" + unicode(val).encode('utf-8').replace('\x00', '?')

                importstr += "\n"

                # Upload in chunks
                if (count % 100) == 0:
                    try:
                        cursor.copy_from(StringIO(importstr), '"public"."%s"' % item['table'])
                    except Exception as e:
                        QgsMessageLog.logMessage(str(e), "QGISCloud")
                        ok = False
                        break
                    importstr = ""
                    self.progress_label.setText("%s: %d features uploaded" % (item['table'], count))
                    QApplication.processEvents()
                # Periodically update ui
                if (count % 10) == 0:
                    QApplication.processEvents()

            if ok and importstr:
                try:
                    cursor.copy_from(StringIO(importstr), '"public"."%s"' % item['table'])
                except Exception as e:
                    QgsMessageLog.logMessage(str(e), "QGISCloud")
                    ok = False

            cursor.close()

            if ok:
                try:
                    conn.commit()
                except Exception as e:
                    QgsMessageLog.logMessage(str(e), "QGISCloud")
                    ok = False
            else:
                conn.rollback()

            import_ok &= ok

            if ok and do_replace_local_layers:
                for layer in item['layers']:
                    layers_to_replace[layer.id()] = {
                        'layer': layer,
                        'data_source': data_source,
                        'db_name': db.database,
                        'table_name': item['table'],
                        'geom_column': geom_column
                    }

        conn.close()
        self.progress_bar.hide()
        self.progress_label.hide()
        self._replace_local_layers(layers_to_replace)
        return import_ok

    def _wkbToEWkbHex(self, wkb, srid, convertToMulti=False):
        wktType = struct.unpack("=I", wkb[1:5])[0]
        if not QGis.isMultiType(wktType):
            wktType = QGis.multiType(wktType)
            wkb = wkb[0] + struct.pack("=I", wktType) + struct.pack("=I", 1) + wkb

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
        ewkb = wkb[0] + struct.pack("=I", wktType) + struct.pack("=I", srid) + wkb[5:]
        return binascii.hexlify(ewkb)

    def _replace_local_layers(self, layers_to_replace):
        if len(layers_to_replace) > 0:
            # replace local layers while keeping layer order
            layers = self.iface.legendInterface().layers()
            layers.reverse()
            for layer in layers:
                layer_id = layer.id()
                if layer_id in layers_to_replace:
                    # replace local layer
                    layer_info = layers_to_replace[layer_id]
                    self.replace_local_layer(
                        layer_info['layer'],
                        layer_info['data_source'],
                        layer_info['db_name'],
                        layer_info['table_name'],
                        layer_info['geom_column']
                    )
                else:
                    # move remote vector layer
                    source_layer = QgsMapLayerRegistry.instance().mapLayer(layer_id)
                    if source_layer.type() == QgsMapLayer.VectorLayer:
                        target_layer = QgsVectorLayer(source_layer.source(), source_layer.name(), source_layer.providerType())
                        if target_layer.isValid():
                            self.copy_layer_settings(source_layer, target_layer)
                            QgsMapLayerRegistry.instance().addMapLayer(target_layer)
                            self.iface.legendInterface().setLayerVisible(target_layer, self.iface.legendInterface().isLayerVisible(source_layer))
                            QgsMapLayerRegistry.instance().removeMapLayer(layer_id)

    def replace_local_layer(self, local_layer, data_source, db_name, table_name, geom_column):
        self.status_bar.showMessage(u"Replace layer %s ..." % local_layer.name())

        # create remote layer
        uri = self.db_connections.cloud_layer_uri(db_name, table_name, geom_column)
        remote_layer = QgsVectorLayer(uri.uri(), local_layer.name(), 'postgres')
        if remote_layer.isValid():
            self.copy_layer_settings(local_layer, remote_layer)

            # add remote layer
            QgsMapLayerRegistry.instance().addMapLayer(remote_layer)
            remote_layer.updateExtents()
            self.iface.legendInterface().setLayerVisible(remote_layer, self.iface.legendInterface().isLayerVisible(local_layer))

            # remove local layer
            QgsMapLayerRegistry.instance().removeMapLayer(local_layer.id())

            self.status_bar.showMessage(u"Replaced layer %s" % remote_layer.name())

    def copy_layer_settings(self, source_layer, target_layer):
        # copy filter
        target_layer.setSubsetString(source_layer.subsetString())

        # copy symbology
        error = ""
        doc = QDomDocument()
        node = doc.createElement("symbology")
        doc.appendChild(node)
        source_layer.writeSymbology(node, doc, error)

        if not error:
            target_layer.readSymbology(node, error)
        if error:
            QMessageBox.warning(None, "Could not copy symbology", error)

        # copy scale based visibility
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

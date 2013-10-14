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
from pyogr.ogr2ogr import *
import os
import re


class DataUpload:

    def __init__(self, iface, status_bar, progress_bar, api, db_connections):
        self.iface = iface
        self.status_bar = status_bar
        self.progress_bar = progress_bar
        self.api = api
        self.db_connections = db_connections
        pass

    def ogr2ogr(self, db_name, data_sources_items, do_replace_local_layers):
        self.status_bar.showMessage(u"Uploading to database %s ..." % db_name)

        dest_geometry_types = {
            #QGis.WKBPoint: ogr.wkbMultiPoint,
            QGis.WKBLineString: ogr.wkbMultiLineString,
            QGis.WKBPolygon: ogr.wkbMultiPolygon
        }

        #PG options
        os.environ['PG_USE_COPY'] = 'YES'
        os.environ['PG_USE_BASE64'] = 'YES'

        layers_to_replace = {}
        for data_source, item in data_sources_items.iteritems():
            table_name = item['table']
            qgis_layers = item['layers'] #layers with shared data source
            data_layer = qgis_layers[0]
            srcLayer = self._ogrConnectionString(data_layer)
            #qDebug("ogr2ogr source: %s" % srcLayer)
            srcUri = QgsDataSourceURI(data_layer.source())
            papszLayers = []
            if srcUri.table() != '':
                papszLayers = [str(srcUri.table())]
                #qDebug("ogr2ogr layers: " + ' '.join(papszLayers))
            geometry_column = 'wkb_geometry'
            eGType = dest_geometry_types.get(data_layer.wkbType()) or -2 #single to multi geom
            destUri = self.db_connections.cloud_layer_uri(db_name, table_name, geometry_column)

            self.progress_bar.setFormat("Uploading " + table_name + ": %v%")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

            ok = ogr2ogr(pszFormat='PostgreSQL',
                pszDataSource=srcLayer,
                papszLayers=papszLayers,
                pszDestDataSource=self._ogrCloudConnectionString(destUri),
                pszNewLayerName=table_name,
                papszLCO = ['LAUNDER=NO'],
                eGType=eGType,
                bOverwrite=True, #TODO: Ask user for overwriting existing table
                bDisplayProgress=True,
                progress_func=self._progress,
                errfunc=self._ogrerr)

            self.progress_bar.hide()

            if not ok:
                raise Exception("Error in ogr2ogr")

            if do_replace_local_layers:
                for layer in qgis_layers:
                    layers_to_replace[layer.id()] = {
                        'layer': layer,
                        'data_source': data_source,
                        'db_name': db_name,
                        'table_name': table_name,
                        'geom_column': geometry_column
                    }

        self._replace_local_layers(layers_to_replace)

        return True

    def _ogrCloudConnectionString(self, uri):
        return "PG:host='%s' port='%s' dbname='%s' user='%s' password='%s'" % (
            uri.host(), uri.port(), uri.database(), uri.username(), uri.password())

    #OGR data source connection string (without table/layer)
    def _ogrConnectionString(self, layer):
        ogrstr = None

        provider = layer.providerType()
        if provider == 'spatialite':
            #dbname='/geodata/osm_ch.sqlite' table="places" (Geometry) sql=
            regex = re.compile("dbname='(.+)'")
            r = regex.search(str(layer.source()))
            ogrstr = r.groups()[0]
        elif provider == 'postgres':
            #dbname='geodb' host=localhost port=5432 user='xxxx' password='yyyy' sslmode=disable key='gid' estimatedmetadata=true srid=4326 type=MULTIPOLYGON table="t4" (geom) sql=
            parts = []
            for part in str(layer.source()).split():
                if part.find('=') >= 0:
                    k,v = part.split('=')
                    if k in ['dbname', 'host', 'port', 'user', 'password']:
                        parts.append(part)
            ogrstr = 'PG:' + ' '.join(parts)
        else:
            ogrstr = unicode(layer.source())
        return ogrstr

    def _progress(self, dfComplete, pszMessage, pProgressArg):
        self.progress_bar.show()
        self.progress_bar.setValue((int) (dfComplete * 100.0))
        QApplication.processEvents() # allow progress bar to scale properly

    def _ogrerr(self, text):
        qDebug(text) #TODO: user log

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

    def postgres_columns(self, pg_connection, uri, geom_column):
        """
            get all table columns except the geometry column
        """
        columns = []
        cursor = pg_connection.cursor()
        sql = "SELECT column_name, udt_name, character_maximum_length, numeric_precision \
            FROM information_schema.columns \
            WHERE table_schema = '%s' AND table_name = '%s' AND column_name != '%s' \
            ORDER BY ordinal_position" % (self.schema_from_uri(uri), uri.table(), geom_column)
        cursor.execute(sql)
        for name, type_name, length, precision in cursor:
            if length is None:
                length = -1
            if precision is None:
                precision = -1
            columns.append({
                'name': str(name),
                'type': str(type_name),
                'length': length,
                'precision': precision
            })
        cursor.close()
        return columns

    def postgres_geometry(self, pg_connection, uri):
        cursor = pg_connection.cursor()
        sql = "SELECT f_geometry_column, srid, type \
            FROM geometry_columns \
            WHERE f_table_schema = '%s' AND f_table_name = '%s'" % (self.schema_from_uri(uri), uri.table())
        cursor.execute(sql)
        geom_column, srid, geom_type = cursor.fetchone()

        # get column index of geometry column
        sql = "SELECT ordinal_position \
            FROM information_schema.columns \
            WHERE table_schema = '%s' AND table_name = '%s' AND column_name = '%s'" % (self.schema_from_uri(uri), uri.table(), geom_column)
        cursor.execute(sql)
        geom_column_index = cursor.fetchone()[0] - 1
        cursor.close()

        return str(geom_column), srid, str(geom_type), geom_column_index

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

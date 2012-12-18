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
from pg8000 import DBAPI
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

    # data_sources_items = Map<data_source, {table: table, layers: layers}>
    def upload_data(self, db_name, data_sources_items, do_replace_local_layers):
        geometry_types = {
            QGis.WKBPoint: "POINT",
            QGis.WKBMultiPoint: "MULTIPOINT",
            QGis.WKBLineString: "LINESTRING",
            QGis.WKBMultiLineString: "MULTILINESTRING",
            QGis.WKBPolygon: "POLYGON",
            QGis.WKBMultiPolygon: "MULTIPOLYGON",
        }

        geometry_types_to_multi = {
            QGis.WKBPoint: "MULTIPOINT",
            QGis.WKBMultiPoint: "MULTIPOINT",
            QGis.WKBLineString: "MULTILINESTRING",
            QGis.WKBMultiLineString: "MULTILINESTRING",
            QGis.WKBPolygon: "MULTIPOLYGON",
            QGis.WKBMultiPolygon: "MULTIPOLYGON",
        }

        self.status_bar.showMessage(u"Connecting to database %s ..." % db_name)
        QApplication.processEvents() # refresh status bar
        #DEACTIVATED (ssl problems): self.db_connections.wait_for_db(db_name)
        self.status_bar.showMessage(u"Setup database %s ..." % db_name)

        layers_to_replace = {}
        for data_source, item in data_sources_items.iteritems():
            table_name = item['table']
            layers = item['layers']
            provider = layers[0].providerType()
            columns = []
            srid = ""
            geometry_type = ""
            pkey = None
            geometry_column = "geom"
            geometry_column_index = None
            convert_to_multi_type = False
            if provider == 'postgres':
                uri = QgsDataSourceURI(layers[0].source())
                conn = self.postgres_connection(uri)
                pkey = str(uri.keyColumn())
                geometry_column, srid, geometry_type, geometry_column_index = self.postgres_geometry(conn, uri)
                if geometry_type == "GEOMETRY":
                    geometry_type = geometry_types_to_multi[layers[0].wkbType()]
                    convert_to_multi_type = True
                srid = "EPSG:%s" % srid
                columns = self.postgres_columns(conn, uri, geometry_column)
                conn.close()
            else:
                for index, field in layers[0].dataProvider().fields().iteritems():
                    columns.append({
                        'name': str(field.name()),
                        'type': str(field.typeName()),
                        'length': field.length(),
                        'precision': field.precision()
                    })

                srid = str(layers[0].crs().authid())
                geometry_type = geometry_types[layers[0].wkbType()]
                if provider == 'ogr':
                    geometry_type = geometry_types_to_multi[layers[0].wkbType()]
                    convert_to_multi_type = True

            self.status_bar.showMessage(u"Create table %s ..." % table_name)

            overwrite_table = False
            while True:
                result = self.api.create_table(db_name, table_name, overwrite_table, columns, srid, geometry_type, provider, pkey, geometry_column, geometry_column_index)
                if self.table_exists_error(result):
                    msgBox = QMessageBox()
                    msgBox.setWindowTitle("QGIS Cloud")
                    msgBox.setText("The table '%s' already exists in the database '%s'." % (table_name, db_name))
                    msgBox.setInformativeText("Do you want to overwrite the existing table?")
                    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.Abort)
                    msgBox.setDefaultButton(QMessageBox.Abort)
                    msgBox.setIcon(QMessageBox.Warning)
                    ret = msgBox.exec_()
                    if ret == QMessageBox.Yes:
                        overwrite_table = True
                    else:
                        return False
                elif self.show_api_error(result):
                    return False
                else:
                    break

            self.copy_features(data_source, provider, db_name, table_name, geometry_column, convert_to_multi_type)

            if do_replace_local_layers:
                for layer in layers:
                    layers_to_replace[layer.id()] = {
                        'layer': layer,
                        'data_source': data_source,
                        'db_name': db_name,
                        'table_name': table_name,
                        'geom_column': geometry_column
                    }

        if do_replace_local_layers:
            self._replace_local_layers(layers_to_replace)

        return True

    def copy_features(self, data_source, provider, db_name, table_name, geom_column, convert_to_multi_type):
        self.status_bar.showMessage(u"Copy features to table %s ..." % table_name)

        # add temp local layer
        local_layer = QgsVectorLayer(data_source, "temp local %s" % table_name, provider)
        if local_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(local_layer)

        # add temp remote layer
        uri = self.db_connections.cloud_layer_uri(db_name, table_name, geom_column)
        remote_layer = QgsVectorLayer(uri.uri(), "temp remote %s" % table_name, 'postgres')
        if remote_layer.isValid():
            QgsMapLayerRegistry.instance().addMapLayer(remote_layer)

        if local_layer.isValid() and remote_layer.isValid():
            # init progress bar
            self.progress_bar.setFormat("%v / %m features copied")
            self.progress_bar.setRange(0, local_layer.featureCount())
            self.progress_bar.setValue(0)
            self.progress_bar.show()
            progress_update = self.progress_bar.maximum() / 50
            if progress_update == 0:
                progress_update = 1
            feature_count = 1
            # commit every n features
            commit_update = local_layer.featureCount() / 20
            if commit_update == 0:
                commit_update = 1

            # copy features
            remote_layer.startEditing()
            local_layer.setSubsetString("") # all features
            local_layer.select(local_layer.pendingAllAttributesList(), QgsRectangle(), True, False);
            f = QgsFeature()
            shift_attribute_map = (local_layer.providerType() != 'postgres')
            while local_layer.nextFeature(f):
                if shift_attribute_map:
                    # first column in new table is new pkey, shift column index one to the right
                    new_attr_map = {}
                    for index, attr in f.attributeMap().iteritems():
                        new_attr_map[index + 1] = attr
                    f.setAttributeMap(new_attr_map)

                if convert_to_multi_type:
                    geom = f.geometry()
                    geom.convertToMultiType()
                    f.setGeometry(geom)

                remote_layer.addFeature(f, False);

                if feature_count % commit_update == 0:
                    remote_layer.commitChanges()
                    remote_layer.startEditing()

                # update progress bar 
                if feature_count % progress_update == 0 or feature_count == self.progress_bar.maximum():
                    self.progress_bar.setValue(feature_count)
                    QApplication.processEvents() # allow progress bar to scale properly
                feature_count += 1

            if remote_layer.commitChanges():
                self.status_bar.showMessage(u"Copied %d features to table %s" % (feature_count, table_name))
                QgsMapLayerRegistry.instance().removeMapLayer(remote_layer.id())

            QgsMapLayerRegistry.instance().removeMapLayer(local_layer.id())
            self.progress_bar.hide()

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
            qDebug("ogr2ogr source: %s" % srcLayer)
            srcUri = QgsDataSourceURI(data_layer.source())
            papszLayers = []
            if srcUri.table() != '':
                papszLayers = [str(srcUri.table())]
                qDebug("ogr2ogr layers: " + ' '.join(papszLayers))
            geometry_column = 'wkb_geometry'
            eGType = dest_geometry_types.get(data_layer.wkbType()) or -2 #single to multi geom
            destUri = self.db_connections.cloud_layer_uri(db_name, table_name, geometry_column)

            self.progress_bar.setFormat("Uploading " + table_name + ": %v%")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

            ogr2ogr(pszFormat='PostgreSQL',
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
            ogrstr = str(layer.source())
        return ogrstr

    def _progress(self, dfComplete, pszMessage, pProgressArg):
        self.progress_bar.show()
        self.progress_bar.setValue((int) (dfComplete * 100.0))
        QApplication.processEvents() # allow progress bar to scale properly

    def _ogrerr(self, text):
        raise Exception(text)

    def _replace_local_layers(self, layers_to_replace):
        if len(layers_to_replace) > 0:
            # replace local layers while keeping layer order
            layer_ids = list(self.iface.mapCanvas().mapRenderer().layerSet())
            layer_ids.reverse()
            for layer_id in layer_ids:
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

            # remove local layer
            QgsMapLayerRegistry.instance().removeMapLayer(local_layer.id())

            self.status_bar.showMessage(u"Replaced layer %s" % remote_layer.name())

    def copy_layer_settings(self, source_layer, target_layer):
        # copy filter
        target_layer.setSubsetString(source_layer.subsetString())

        # copy symbology
        error = QString("")
        doc = QDomDocument()
        node = doc.createElement("symbology")
        doc.appendChild(node)
        source_layer.writeSymbology(node, doc, error)

        if error.isEmpty():
            target_layer.readSymbology(node, error)
        if not error.isEmpty():
            QMessageBox.warning(None, "Could not copy symbology", error)

        # copy scale based visibility
        target_layer.toggleScaleBasedVisibility(source_layer.hasScaleBasedVisibility())
        target_layer.setMinimumScale(source_layer.minimumScale())
        target_layer.setMaximumScale(source_layer.maximumScale())

        #copy CRS
        target_layer.setCrs(source_layer.crs(), False)

    def postgres_connection(self, uri):
        return DBAPI.connect(
            host = str(uri.host()),
            port = uri.port().toInt()[0] if uri.port() != '' else 5432,
            database = str(uri.database()),
            user = str(uri.username()),
            password = str(uri.password()),
            ssl = (uri.sslMode() != QgsDataSourceURI.SSLdisable)
        )

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

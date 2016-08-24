# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LocalDataSources

 Collect local data sources from QGIS project layers
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
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from db_connection_cfg import DbConnectionCfg


class LocalDataSources:

    def __init__(self):
        # map<data source, layers>
        self._local_data_sources = {}

    def layers(self, data_source):
        if self._local_data_sources.has_key(data_source):
            return self._local_data_sources[data_source]
        else:
            return None

    def iteritems(self):
        return self._local_data_sources.iteritems()

    def count(self):
        return len(self._local_data_sources)

    def local_layers(self, skip_layer_id=None):
        unsupported_layers = []
        local_layers = []
        local_raster_layers = []
        for layer in QgsMapLayerRegistry.instance().mapLayers().values():
            if layer.id() == skip_layer_id:
                continue
            if layer.type() != QgsMapLayer.PluginLayer:
                provider = layer.dataProvider().name()
            else:
                provider = layer.pluginLayerType()

            if provider == "postgres":
                if QgsDataSourceURI(layer.publicSource()).host() not in DbConnectionCfg.CLOUD_DB_HOSTS:
                    if layer.wkbType() != 100: # FIXME: QGis.WKBNoGeometry
                        local_layers.append(layer)
                    else:
                        # geometryless tables not supported
                        unsupported_layers.append(layer)

            elif provider == "gdal":
                if layer.dataProvider().metadata()[0:13] == "PostGISRaster":
                    # FIXME: Temporary workaround for buggy QgsDataSourceURI parser which fails to parse URI strings starting with PG:
                    uri = layer.dataProvider().dataSourceUri()
                    uri = uri.strip("PG: ")
                    if QgsDataSourceURI(uri).host() not in DbConnectionCfg.CLOUD_DB_HOSTS:
                        unsupported_layers.append(layer)
                elif layer.customProperty('ol_layer_type', None) is not None:
                    # GDAL TMS layer from OpenLayers plugin (> 1.3.6)
                    pass
                elif layer.dataProvider().metadata()[0:5] == "GTiff":
                    local_raster_layers.append(layer)
                elif layer.dataProvider().metadata()[0:3] in ["JP2","VRT","ECW"]:
                    local_raster_layers.append(layer)
                else:
                    unsupported_layers.append(layer)

            elif provider not in ["wms", "openlayers"]:
                if layer.type() == QgsMapLayer.VectorLayer:
                    local_layers.append(layer)
                else:
                    unsupported_layers.append(layer)

        return local_layers, unsupported_layers,  local_raster_layers

    def update_local_data_sources(self, local_layers):
        # get unique local data sources
        self._local_data_sources = {}
        for layer in sorted(local_layers, key=lambda layer: layer.name()):
            #qDebug("local layer source: {0} (provider type: {1})".format(layer.source(), layer.providerType()))
            #Disabled because of UnicodeEncodeError: 'ascii' codec can't encode character u'\xf3' in position 18: ordinal not in range(128)
            # get layer source without filter
            ds = QgsDataSourceURI(layer.source())
            if len(ds.connectionInfo()) > 0:
                # Spatialite / Postgres
                ds.setSql("")
                data_source = unicode(ds.uri())
            else:
                data_source = unicode(layer.source())

            # group layers by source
            if self._local_data_sources.has_key(data_source):
                self._local_data_sources[data_source].append(layer)
            else:
                self._local_data_sources[data_source] = [layer]

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
from __future__ import absolute_import
from builtins import str
from builtins import object
from qgis.core import *
from .db_connection_cfg import DbConnectionCfg

class LocalDataSources(object):

    def __init__(self):
        # map<data source, layers>
        self._local_data_sources = {}

    def layers(self, data_source):
        if data_source in self._local_data_sources:
            return self._local_data_sources[data_source]
        else:
            return None

    def iteritems(self):
        return iter(list(self._local_data_sources.items()))

    def count(self):
        return len(self._local_data_sources)

    def local_layers(self, skip_layer_id=None):
        unsupported_layers = []
        local_layers = []
        local_raster_layers = []
        layer_list = list(QgsProject.instance().mapLayers().values()) 
           
        for layer in layer_list:
            if layer.id() == skip_layer_id:
                continue
            if layer.type() != QgsMapLayer.PluginLayer:
                provider = layer.dataProvider().name()
            else:
                provider = layer.pluginLayerType()

            if provider == "postgres":
                host = QgsDataSourceUri(layer.publicSource()).host()
                if host not in DbConnectionCfg.CLOUD_DB_HOSTS:
                    if layer.wkbType() != 0: 
                        local_layers.append(layer)
                    else:
                        # geometryless tables not supported
                        unsupported_layers.append(layer)

            elif provider in ["gdal"] and layer.dataProvider().crs().srsid() != 0:
                if  "PostGISRaster" in layer.dataProvider().htmlMetadata():
                    # FIXME: Temporary workaround for buggy QgsDataSourceURI parser which fails to parse URI strings starting with PG:
                    uri = layer.dataProvider().dataSourceUri()
                    uri = uri.strip("PG: ")
                    host = QgsDataSourceUri(uri).host()
                        
                    if host not in DbConnectionCfg.CLOUD_DB_HOSTS:
                        unsupported_layers.append(layer)
                elif layer.customProperty('ol_layer_type', None) is not None:
                    # GDAL TMS layer from OpenLayers plugin (> 1.3.6)
                    pass
                else:
                    local_raster_layers.append(layer)

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
            ds = QgsDataSourceUri(layer.source())
                
            if len(ds.connectionInfo()) > 0:
                # Spatialite / Postgres
                ds.setSql("")
                data_source = str(ds.uri())
            else:
                data_source = str(layer.source())

            # group layers by source
            if data_source in self._local_data_sources:
                self._local_data_sources[data_source].append(layer)
            else:
                self._local_data_sources[data_source] = [layer]

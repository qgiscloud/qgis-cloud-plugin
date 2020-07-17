# -*- coding: utf-8 -*-
"""
/***************************************************************************
OpenLayers Plugin
A QGIS plugin

                             -------------------
begin                : 2009-11-30
copyright            : (C) 2009 by Pirmin Kalberer, Sourcepole
email                : pka at sourcepole.ch
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

# Import the PyQt and QGIS libraries
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import *
from qgis.core import *
# import resources_rc
import imp


try:
    from openlayers_plugin.openlayers_layer import OpenlayersLayer
    from openlayers_plugin.openlayers_plugin_layer_type import OpenlayersPluginLayerType
    from openlayers_plugin.weblayers.weblayer_registry import WebLayerTypeRegistry
    from openlayers_plugin.weblayers.google_maps import OlGooglePhysicalLayer, OlGoogleStreetsLayer, OlGoogleHybridLayer, OlGoogleSatelliteLayer
except:
    pass


class BackgroundLayersMenu(QMenu):
    def __init__(self, iface, parent=None):
        QMenu.__init__(self, parent)
        self.iface = iface

        self.add_google_layergroup()
        self.add_XYZ_layergroups()

    def add_google_layergroup(self):
        try:
            self._olLayerTypeRegistry = WebLayerTypeRegistry(self)
        except:
            return

        self._olLayerTypeRegistry.register(OlGooglePhysicalLayer())
        self._olLayerTypeRegistry.register(OlGoogleStreetsLayer())
        self._olLayerTypeRegistry.register(OlGoogleHybridLayer())
        self._olLayerTypeRegistry.register(OlGoogleSatelliteLayer())

        for group in self._olLayerTypeRegistry.groups():
            groupMenu = group.menu()
            for layer in self._olLayerTypeRegistry.groupLayerTypes(group):
                layer.addMenuEntry(groupMenu, self.iface.mainWindow())

            add_api_key_action = QAction("Set api Key", groupMenu)
            add_api_key_action.triggered.connect(
                self.showGoogleApiKeyDialog)
            groupMenu.addAction(add_api_key_action)

            self.addMenu(groupMenu)

        # Register plugin layer type
        self.pluginLayerType = OpenlayersPluginLayerType(
            self.iface, self.setReferenceLayer, self._olLayerTypeRegistry)
        QgsApplication.pluginLayerRegistry().addPluginLayerType(
            self.pluginLayerType)

    def add_XYZ_layergroups(self):
        xyz_layers = {
            "OpenStreetMap": {
                "OpenStreetMap": 'http://tile.openstreetmap.org/{z}/{x}/{y}.png',
                "OSM Humanitarian Data Model": 'http://a.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png'
            },
            "OSM/Stamen": {
                "Stamen Toner / OSM": 'http://tile.stamen.com/toner/{z}/{x}/{y}.png',
                "Stamen Toner Lite / OSM": 'http://tile.stamen.com/toner-lite/{z}/{x}/{y}.png',
                "Stamen Watercolor / OSM": 'http://tile.stamen.com/watercolor/{z}/{x}/{y}.jpg',
                "Stamen Terrain / OSM": 'http://tile.stamen.com/terrain/{z}/{x}/{y}.png'
            },
            "OSM/Thunderforest": {
                "OpenCycleMap": 'https://tile.thunderforest.com/cycle/{z}/{x}/{y}.png',
                "OCM Landscape": 'https://tile.thunderforest.com/landscape/{z}/{x}/{y}.png',
                "OCM Public Transport": 'https://tile.thunderforest.com/transport/{z}/{x}/{y}.png',
                "Outdoors": 'https://tile.thunderforest.com/outdoors/{z}/{x}/{y}.png',
                "Transport Dark": 'https://tile.thunderforest.com/transport-dark/{z}/{x}/{y}.png',
                "Spinal Map": 'https://tile.thunderforest.com/spinal-map/{z}/{x}/{y}.png',
                "Pioneer": 'https://tile.thunderforest.com/pioneer/{z}/{x}/{y}.png',
                "Mobile Atlas": 'https://tile.thunderforest.com/mobile-atlas/{z}/{x}/{y}.png',
                "Neighbourhood": 'https://tile.thunderforest.com/neighbourhood/{z}/{x}/{y}.png'
            },
            "Wikipedia Maps": {
                "Wikipedia Labelled Layer": 'https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png',
                "Wikipedia Unlabelled Layer": 'https://maps.wikimedia.org/osm/{z}/{x}/{y}.png'
            },
            "Bing Maps": {
                "Bing Roads": 'http://ecn.t3.tiles.virtualearth.net/tiles/r{q}.jpeg?g=1',
                "Bing Aerial": 'http://ecn.t3.tiles.virtualearth.net/tiles/a{q}.jpeg?g=1',
                "Bing Aerial with labels": 'http://ecn.t3.tiles.virtualearth.net/tiles/h{q}.jpeg?g=1'
            }
        }

        for layer_type in xyz_layers:
            menu = QMenu(layer_type, self)
            for layer in xyz_layers[layer_type]:
                action = self.create_add_layer_action(
                    xyz_layers[layer_type][layer], layer, menu)
                menu.addAction(action)
            if "Thunderforest" in layer_type:
                add_api_key_action = QAction("Set api Key", menu)
                add_api_key_action.triggered.connect(
                    self.showThunderforestApiKeyDialog)
                menu.addAction(add_api_key_action)
            self.addMenu(menu)

    def create_add_layer_action(self, url, title, parent):
        action = QAction(title, parent)
        action.triggered.connect(
                    lambda: self.addLayer(
                        None, xyzUrl=url, displayName=title))
        return action

    def showThunderforestApiKeyDialog(self):
        apiKey = QSettings().value("qgis-cloud-plugin/thunderforestApiKey")
        newApiKey, ok = QInputDialog.getText(
            self.iface.mainWindow(), "API key",
            "Enter your API key (<a href=\"https://thunderforest.com/pricing/\">https://thunderforest.com</a>)", QLineEdit.Normal, apiKey)
        if ok:
            QSettings().setValue("qgis-cloud-plugin/thunderforestApiKey",
                                 newApiKey)

    def showGoogleApiKeyDialog(self):
        apiKey = QSettings().value("Plugin-OpenLayers/googleMapsApiKey")
        newApiKey, ok = QInputDialog.getText(
            self.iface.mainWindow(), "API key",
            "Enter your API key", QLineEdit.Normal, apiKey)
        if ok:
            QSettings().setValue("Plugin-OpenLayers/googleMapsApiKey",
                                 newApiKey)

    def addLayer(self, layerType, xyzUrl=None, displayName=None):
        if layerType is None:
            thunderforest_api_key = QSettings().value(
                    "qgis-cloud-plugin/thunderforestApiKey")

            google_api_key = QSettings().value(
                    "Plugin-OpenLayers/googleMapsApiKey")

            if "thunderforest" in xyzUrl and thunderforest_api_key:
                xyzUrl = xyzUrl + "?apikey=%s" % thunderforest_api_key
            elif "google" in xyzUrl and google_api_key:
                xyzUrl = xyzUrl + "?key=%s" % google_api_key

            layer = QgsRasterLayer(
                'type=xyz' + '&url=' + xyzUrl, displayName, 'wms')
        else:
            layer = OpenlayersLayer(self.iface, self._olLayerTypeRegistry)
            layer.setName(layerType.displayName)
            layer.setLayerType(layerType)

        if not layer.isValid():
            return

        coordRefSys = QgsCoordinateReferenceSystem()
        coordRefSys.createFromOgcWmsCrs("EPSG:3857")
        self.setMapCrs(coordRefSys)
        QgsProject.instance().addMapLayer(layer, False)
        legendRootGroup = self.iface.layerTreeView().layerTreeModel().rootGroup()
        legendRootGroup.insertLayer(len(legendRootGroup.children()), layer)

        # last added layer is new reference
        self.setReferenceLayer(layer)

    def setReferenceLayer(self, layer):
        self.layer = layer

    def removeLayer(self, layerId):
        if self.layer is not None and self.layer.id() == layerId:
            self.layer = None

    def canvasCrs(self):
        mapCanvas = self.iface.mapCanvas()
        crs = mapCanvas.mapSettings().destinationCrs()
        return crs

    def setMapCrs(self, coordRefSys):
        mapCanvas = self.iface.mapCanvas()
        canvasCrs = self.canvasCrs()
        if canvasCrs != coordRefSys:
            coordTrans = QgsCoordinateTransform(
                canvasCrs,
                coordRefSys,
                QgsProject.instance())
            extMap = mapCanvas.extent()
            extMap = coordTrans.transform(
                extMap, QgsCoordinateTransform.ForwardTransform)
            QgsProject.instance().setCrs(coordRefSys)
            mapCanvas.freeze(False)
            mapCanvas.setExtent(extMap)

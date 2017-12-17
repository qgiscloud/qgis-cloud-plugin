# coding=utf-8
import qgis.core
import qgis.utils
from qgis2compat import log


log('Monkeypatching QgsMapThemeCollection')

# Class rename

qgis.core.QgsMapThemeCollection = qgis.core.QgsVisibilityPresetCollection
qgis.core.QgsMapThemeCollection.MapThemeRecord = qgis.core.QgsVisibilityPresetCollection.PresetRecord

def presets(self):
    return self.presets()

qgis.core.QgsMapThemeCollection.mapThemes = presets

def removePreset(self, name):
    return self.removePreset(name)

qgis.core.QgsMapThemeCollection.removeMapTheme = removePreset

def hasPreset(self, name):
    return self.hasPreset(name)

qgis.core.QgsMapThemeCollection.hasMapTheme = hasPreset

def presetState(self, name):
    return self.presetState(name)

qgis.core.QgsMapThemeCollection.mapThemeState = presetState

def presetVisibleLayers(self, name):
    return self.presetVisibleLayers(name)

qgis.core.QgsMapThemeCollection.mapThemeVisibleLayers = presetVisibleLayers

def applyPresetCheckedLegendNodesToLayer(self, name, layerId):
    return self.applyPresetCheckedLegendNodesToLayer(name, layerId)

qgis.core.QgsMapThemeCollection.applyMapThemeCheckedLegendNodesToLayer = applyPresetCheckedLegendNodesToLayer

def presetStyleOverrides(self, name):
    return self.presetStyleOverrides(name)

qgis.core.QgsMapThemeCollection.mapThemeStyleOverrides = presetStyleOverrides

def addVisibleLayersToPreset(self, parent, rec):
    return self.addVisibleLayersToPreset(parent, rec)

qgis.core.QgsMapThemeCollection.addVisibleLayersToMapTheme = addVisibleLayersToPreset

qgis.core.QgsMapThemeCollection.mapThemesChanged = qgis.core.QgsMapThemeCollection.presetsChanged


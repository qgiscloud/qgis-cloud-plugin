# coding=utf-8
import qgis.core
import qgis.utils
from qgis2compat import log


log('Monkeypatching QgsVectorLayer')


def writeLayerXML(self, XMLMapLayer, XMLDocument):
    self.writeLayerXML(XMLMapLayer, XMLDocument)

qgis.core.QgsVectorLayer.writeLayerXml = writeLayerXML


def readLayerXML(self, XMLMapLayer):
    self.readLayerXML(XMLMapLayer)

qgis.core.QgsVectorLayer.readLayerXml = readLayerXML


def editorWidgetV2Config(self, index):
    self.editorWidgetV2Config(index)

qgis.core.QgsVectorLayer.editorWidgetSetup = editorWidgetV2Config


def setEditorWidgetV2Config(self, index, config):
    self.setEditorWidgetV2Config(index, config)

qgis.core.QgsVectorLayer.setEditorWidgetSetup = setEditorWidgetV2Config

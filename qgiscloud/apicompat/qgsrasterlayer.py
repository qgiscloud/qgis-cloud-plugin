# coding=utf-8
import qgis.core
import qgis.utils
from qgis2compat import log


log('Monkeypatching QgsRasterLayer')


def writeLayerXML(self, XMLMapLayer, XMLDocument):
    self.writeLayerXML(XMLMapLayer, XMLDocument)

qgis.core.QgsRasterLayer.writeLayerXml = writeLayerXML


def readLayerXML(self, XMLMapLayer):
    self.readLayerXML(XMLMapLayer)

qgis.core.QgsRasterLayer.readLayerXml = readLayerXML

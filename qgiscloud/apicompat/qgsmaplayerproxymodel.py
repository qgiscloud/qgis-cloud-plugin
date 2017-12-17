# coding=utf-8
import qgis.core
import qgis.gui
import qgis.utils
from qgis2compat import log


log('Monkeypatching QgsMapLayerProxyModel')

qgis.core.QgsMapLayerProxyModel = qgis.gui.QgsMapLayerProxyModel

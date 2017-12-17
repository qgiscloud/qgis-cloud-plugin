# coding=utf-8
import qgis.core
import qgis.utils
from qgis2compat import log


log('Monkeypatching QgsDataSourceUri')

# Class rename

qgis.core.QgsDataSourceUri = qgis.core.QgsDataSourceURI
qgis.core.QgsDataSourceURI.SslMode = qgis.core.QgsDataSourceUri.SSLmode

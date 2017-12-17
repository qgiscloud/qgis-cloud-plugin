# coding=utf-8
import sys
import qgis.utils
import qgis.core
from qgis2compat import log


log('Monkeypatching qgis.utils.QGis')

qgis.core.Qgis = qgis.utils.QGis


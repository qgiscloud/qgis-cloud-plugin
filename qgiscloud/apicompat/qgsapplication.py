# coding=utf-8
import qgis.core
import qgis.utils
from qgis2compat import log
from PyQt4.QtGui import QApplication


log('Monkeypatching QgsApplication')

# QgsApplication.instance() will return a QApplication instance in QGIS 2

def messageLog(self):
    return qgis.core.QgsMessageLog.instance()

QApplication.messageLog = messageLog

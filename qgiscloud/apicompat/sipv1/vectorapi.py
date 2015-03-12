# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ApiCompat
                                 A QGIS plugin
 API compatibility layer
                              -------------------
        begin                : 2013-07-02
        copyright            : (C) 2013 by Pirmin Kalberer, Sourcepole
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
# Import the PyQt and QGIS libraries
import qgis.core
from PyQt4.QtCore import *
from qgis.core import *


from decorators import *


def vectorapiv1():
    return not hasattr(QgsVectorLayer, 'getFeatures')


class QgsFields:
    def __init__(self, fieldmap):
        self.fieldmap = fieldmap

    def __getitem__(self, idx):
        return self.fieldmap[idx]

    def field(self, idx):
        return self.fieldmap[idx]

    def at(self, idx):
        return self.fieldmap[idx]

    def count(self):
        return len(self.fieldmap)

    def size(self):
        return len(self.fieldmap)

qgis.core.QgsFields = QgsFields


@add_method(QgsVectorLayer)
def getFeatures(self):
    self.select(self.pendingAllAttributesList())
    feature = QgsFeature()
    while self.nextFeature(feature):
        yield feature


@add_method(QgsFeature)
def __getitem__(self, idx):
    return self.attributeMap()[idx]

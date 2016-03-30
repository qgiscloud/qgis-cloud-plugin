# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ApiCompat
                                 A QGIS plugin
 QGis class compatibility layer
                              -------------------
        begin                : 2015-03-12
        copyright            : (C) 2015 by Sandro Mani, Sourcepole
        email                : smani@sourcepole.ch
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

import qgis.core
from qgis.core import *


def multiType(wkbType):
    if wkbType == QGis.WKBPoint:
        return QGis.WKBMultiPoint
    if wkbType == QGis.WKBLineString:
        return QGis.WKBMultiLineString
    if wkbType == QGis.WKBPolygon:
        return QGis.WKBMultiPolygon
    if wkbType == QGis.WKBPoint25D:
        return QGis.WKBMultiPoint25D
    if wkbType == QGis.WKBLineString25D:
        return QGis.WKBMultiLineString25D
    if wkbType == QGis.WKBPolygon25D:
        return QGis.WKBMultiPolygon25D
    return wkbType
#    
#            QgsWKBTypes.MultiCurve: "MultiCurve",
#            QgsWKBTypes.MultiSurface: "MultiSurface",
#            QgsWKBTypes.MultiCurveZ: "MultiCurveZ",
#            QgsWKBTypes.MultiSurfaceZ: "MultiSurfaceZ",
#            QgsWKBTypes.MultiCurveM: "MultiCurveM",
#            QgsWKBTypes.MultiSurfaceM: "MultiSurfaceM",
#            QgsWKBTypes.MultiCurveZM: "MultiCurveZM",
#            QgsWKBTypes.MultiSurfaceZM: "MultiSurfaceZM",    


def isMultiType(wkbType):
    return multiType(wkbType) == wkbType


qgis.core.QGis.multiType = staticmethod(multiType)
qgis.core.QGis.isMultiType = staticmethod(isMultiType)

# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PGVectorLayerImport.py

 Temporary Python port of functionality needed to create an empty PostGIS
 layer, a stable version of qgis with necessary performance enhancements
 has been released.
                             -------------------
        begin                : 2015-10-15
        copyright            : (C) 2015 by Sourcepole
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
from builtins import str
from builtins import range
from builtins import object

from qgis.PyQt.QtCore import QVariant
from qgis.core import *
from numbers import Number

class PGVectorLayerImport(object):  
    
    def __quotedIdentifier(self, ident):
        return '"' + ident.replace('"', '""') + '"'

    def __quotedValue(self, value):
        if not value:
            return "NULL"
        if isinstance(value, Number):
            return value
        else:
            try:
                v = value.toString()
            except:
                v = value
            v = v.replace("'", "''")
            if v.find("\\") != -1:
                return "E'" + v.replace("\\", "\\\\") + "'"
            else:
                return "'" + v + "'"

    def __convertField(self, field):
        # determine field type to use for strings
        stringFieldType = "varchar"

        fieldType = stringFieldType
        fieldSize = field.length()
        fieldPrec = field.precision()
        if field.type() == QVariant.LongLong:
            fieldType = "int8"
            fieldPrec = 0
        elif field.type() == QVariant.DateTime:
            fieldType = "timestamp without time zone"
        elif field.type() == QVariant.Time:
            fieldType = "time"
        elif field.type() == QVariant.String:
            fieldType = stringFieldType
            fieldPrec = -1
        elif field.type() == QVariant.Int:
            if fieldPrec < 10:
                fieldType = "int4"
            else:
                fieldType = "numeric"
            fieldPrec = 0
        elif field.type() == QVariant.Date:
            fieldType = "date"
            fieldPrec = 0
        elif field.type() == QVariant.Double:
            if fieldSize > 18:
                fieldType = "numeric"
                fieldSize = -1
            else:
                fieldType = "float8"
            fieldPrec = -1
        else:
            return False

        field.setTypeName(fieldType)
        field.setLength(fieldSize)
        field.setPrecision(fieldPrec)
        return True

    def __postgisWkbType(self, wkbType):
        if wkbType == QgsWkbTypes.Unknown:
            return ("Unknown", 0)
        elif wkbType == QgsWkbTypes.Point:
            return ("POINT",  2)
        elif wkbType == QgsWkbTypes.LineString:
             return ("LINESTRING",  2)
        elif wkbType == QgsWkbTypes.Polygon:
            return ("POLYGON",  2)
        elif wkbType ==  QgsWkbTypes.MultiPoint:
            return ("MULTIPOINT",  2)
        elif wkbType ==  QgsWkbTypes.MultiLineString:
            return ("MULTILINESTRING",  2)
        elif wkbType ==  QgsWkbTypes.MultiPolygon:
            return ("MULTIPOLYGON",  2)
        elif wkbType ==  QgsWkbTypes.PointZ:
            return ("POINT",  3)
        elif wkbType ==  QgsWkbTypes.LineStringZ:
            return ("LINESTRING",  3)
        elif wkbType ==  QgsWkbTypes.PolygonZ:
            return ("POLYGON",  3)
        elif wkbType ==  QgsWkbTypes.MultiPointZ:
            return ("MULTIPOINT",  3)
        elif wkbType ==  QgsWkbTypes.MultiLineStringZ:
            return ("MULTILINESTRING",  3)
        elif wkbType ==  QgsWkbTypes.MultiLineStringM:
            return ("MULTILINESTRING",  3)            
        elif wkbType ==  QgsWkbTypes.MultiPolygonZ:
            return ("MULTIPOLYGON",  3)
        elif wkbType ==  QgsWkbTypes.PointM:
            return ("POINT",  3)
        elif wkbType ==  QgsWkbTypes.LineStringM:
           return ("LINESTRING", 3)
        elif wkbType ==  QgsWkbTypes.PolygonM:
            return ("POLYGON",  3)
        elif wkbType ==  QgsWkbTypes.MultiPointM:
           return ("MULTIPOINT",  3)
        elif wkbType ==  QgsWkbTypes.MultiPolygonM:
            return ("MULTIPOLYGON",  3)
        elif wkbType ==  QgsWkbTypes.PointZM:
            return ("POINT",  4)
        elif wkbType == QgsWkbTypes.LineStringZM:
            return ("LINESTRING", 4)
        elif wkbType ==  QgsWkbTypes.PolygonZM:
            return ("POLYGON",  4)
        elif wkbType ==  QgsWkbTypes.MultiPointZM:
            return ("MULTIPOINT",  4)
        elif wkbType == QgsWkbTypes.MultiLineStringZM:
            return ("MULTILINESTRING", 4)
        elif wkbType ==  QgsWkbTypes.MultiPolygonZM:
            return ("MULTIPOLYGON",  4)
        elif wkbType ==  QgsWkbTypes.Point25D:
            return ("POINT",  3)
        elif wkbType ==  QgsWkbTypes.LineString25D:
            return ("LINESTRING", 3)
        elif wkbType ==  QgsWkbTypes.Polygon25D:
            return ("POLYGON",  3)
        elif wkbType ==  QgsWkbTypes.MultiPoint25D:
            return ("MULTIPOINT",  3)
        elif wkbType ==  QgsWkbTypes.MultiLineString25D:
            return ("MULTILINESTRING",  3)
        elif wkbType ==  QgsWkbTypes.MultiPolygon25D:
            return ("MULTIPOLYGON",  3)
        elif wkbType ==  QgsWkbTypes.CircularString:
            return ("CIRCULARSTRING",  2)
        elif wkbType ==  QgsWkbTypes.CompoundCurve:
            return ("COMPOUNDCURVE",  2)
        elif wkbType ==  QgsWkbTypes.CurvePolygon:
            return ("CURVEPOLYGON",  2)
        elif wkbType ==  QgsWkbTypes.MultiCurve:
            return ("MULTICURVE",  2)
        elif wkbType ==  QgsWkbTypes.MultiSurface:
            return ("MULTISURFACE",  2)
        elif wkbType ==  QgsWkbTypes.CircularStringZ:
            return ("CIRCULARSTRING",  3)
        elif wkbType ==  QgsWkbTypes.CompoundCurveZ:
            return ("COMPOUNDCURVE",  3)
        elif wkbType ==  QgsWkbTypes.MultiCurveZ:
            return ("MULTICURVE",  3)
        elif wkbType ==  QgsWkbTypes.MultiSurfaceZ:
            return ("MULTISURFACE",  3)
        elif wkbType ==  QgsWkbTypes.CurvePolygonZ:
            return ("CURVEPOLYGON",  3)
        elif wkbType ==  QgsWkbTypes.CircularStringM:
            return ("CIRCULARSTRING",  3)
        elif wkbType ==  QgsWkbTypes.CompoundCurveM:
            return ("COMPOUNDCURVE",  3)
        elif wkbType ==  QgsWkbTypes.MultiCurveM:
            return ("MULTICURVE",  3)
        elif wkbType ==  QgsWkbTypes.MultiSurfaceM:
            return ("MULTISURFACE",  3)
        elif wkbType ==  QgsWkbTypes.CurvePolygonM:
            return ("CURVEPOLYGON",  3)
        elif wkbType ==  QgsWkbTypes.CircularStringZM:
            return ("CIRCULARSTRING",  4)
        elif wkbType ==  QgsWkbTypes.CompoundCurveZM:
            return ("COMPOUNDCURVE",  4)
        elif wkbType ==  QgsWkbTypes.CurvePolygonZM:
            return ("CURVEPOLYGON",  4)
        elif wkbType ==  QgsWkbTypes.MultiCurveZM:
            return ("MULTICURVE",  4)
        elif wkbType ==  QgsWkbTypes.MultiSurfaceZM:
            return ("MULTISURFACE",  4)
        elif wkbType ==  QgsWkbTypes.NoGeometry:
            return ("",  0)
            

    def __addAttributes(self, attributes, query, cursor):
        delim = ""
        sql = "ALTER TABLE %s " % query
        for field in attributes:
            type = field.typeName()
            if type == "char" or type == "varchar":
                if field.length() > 0:
                    type = "%s(%d)" % (type, field.length()+20)
            elif type == "numeric" or type == "decimal":
                if field.length() > 0 and field.precision() >= 0:
                    type = "%s(%d,%d)" % (type, field.length(), field.precision())
            sql += "%sADD COLUMN %s %s" % (delim, self.__quotedIdentifier(field.name().lower()), type)
            delim = ","

        # send sql statement and do error handling
        cursor.execute(sql)

        for field in attributes:
            if field.comment():
                sql = "COMMENT ON COLUMN %s.%s IS %s" % (
                    query,
                    self.__quotedIdentifier(field.name()),
                    self.__quotedValue(field.comment()))
                cursor.execute(sql)

    def __init__(self, db, conn, cursor,  uri, fields, wkbType, srs, overwrite):
        self._errorMessage = ""
        self._hasError = False

        # populate members from the uri structure
        dsUri = QgsDataSourceUri(uri)
            
        schemaName = dsUri.schema()
        tableName = dsUri.table()
        
        if wkbType == QgsWkbTypes.NoGeometry:
            geometryColumn = ""
        else:
            geometryColumn = dsUri.geometryColumn()            

        primaryKey = dsUri.keyColumn()
        primaryKeyType = ""

        schemaTableName = ""
        if schemaName:
            schemaTableName += self.__quotedIdentifier(schemaName) + "."
        schemaTableName += self.__quotedIdentifier(tableName)
        # Create the table

        # get the pk's name and type
        if not primaryKey:
            index = 0
            pk = "qc_id"
            primaryKey = "qc_id"
            fldIdx = 0
            while fldIdx < fields.count():
                if fields[fldIdx].name().lower() == primaryKey:
                    # it already exists, try again with a new name
                    primaryKey = "%s_%d" % (pk, index)
                    index += 1
                    fldIdx = 0
                else:
                    fldIdx += 1
        else:
            # search for the passed field
            for fldIdx in range(0, fields.count()):
                if fields[fldIdx].name() == primaryKey:
                    # found, get the field type
                    fld = fields[fldIdx]
                    if self.__convertField(fld):
                        primaryKeyType = fld.typeName()

        # if the field doesn't not exist yet, create it as a serial field
        if not primaryKeyType:
            primaryKeyType = "serial"

        try:
            sql = ("SELECT 1 FROM pg_class AS cls JOIN pg_namespace AS nsp"
                   " ON nsp.oid=cls.relnamespace "
                   " WHERE cls.relname={tableName} AND nsp.nspname={schemaName}").format(
                       tableName=self.__quotedValue(tableName),
                       schemaName=self.__quotedValue(schemaName))

            cursor.execute(sql)
            if cursor.fetchone() and overwrite:
                # delete the table if exists, then re-create it
                sql = ("SELECT DropGeometryTable({schemaName},{tableName})"
                       " FROM pg_class AS cls JOIN pg_namespace AS nsp"
                       " ON nsp.oid=cls.relnamespace "
                       " WHERE cls.relname={tableName} AND nsp.nspname={schemaName}").format(
                           tableName=self.__quotedValue(tableName),
                           schemaName=self.__quotedValue(schemaName))
                cursor.execute(sql)

            sql = ("CREATE TABLE {schemaTableName}({primaryKey} {primaryKeyType} PRIMARY KEY)").format(
                schemaTableName=schemaTableName,
                primaryKey=self.__quotedIdentifier(primaryKey),
                primaryKeyType=primaryKeyType)

            cursor.execute(sql)
            
            
            # get geometry type, dim and srid
            (geometryType, dim) = self.__postgisWkbType(wkbType)
            srid = srs.postgisSrid()

            # create geometry column
            if geometryType:
                sql = ("SELECT AddGeometryColumn({schemaName},{tableName},{geometryColumn},{srid},{geometryType},{dim})").format(
                    schemaName=self.__quotedValue(schemaName),
                    tableName=self.__quotedValue(tableName),
                    geometryColumn=self.__quotedValue(geometryColumn),
                    srid=srid,
                    geometryType=self.__quotedValue(geometryType),
                    dim=dim)
                cursor.execute(sql)
            else:
                geometryColumn = ""

            conn.commit()
        except Exception as e:
            conn.rollback()
            self._errorMessage = ("Creation of data source {schemaTableName} failed:\n{errorMessage}").format(
                schemaTableName=schemaTableName,
                errorMessage=str(e))
            self._hasError = True
            return

        if fields.size() > 0:
            offset = 1

            # get the list of fields
            flist = []
            for fldIdx in range(0, fields.count()):
                fld = fields[fldIdx]

                if fld.name() == geometryColumn:
                    # the "lowercaseFieldNames" option does not affect the name of the geometry column, so we perform
                    # this test before converting the field name to lowercase
                    continue

                if fld.name() == primaryKey:
                    continue

                if not self.__convertField(fld):
                    self._errorMessage = "Unsupported attribute type"
                    self._hasError = True
                    return

                flist.append(fld)

            if not schemaName and tableName[0] == "(" and tableName[-1] == ")":
                query = tableName
            else:
                if schemaName:
                    query = self.__quotedIdentifier(schemaName) + "."
                if tableName:
                    query += self.__quotedIdentifier(tableName)

#            try:
            self.__addAttributes(flist, query, cursor)
            conn.commit()
#            except Exception as e:
#                conn.rollback()
#                exc_type, exc_obj, exc_tb = sys.exc_info()
#                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
#                self._errorMessage = "Creation of fields failed: %s (%s:%d)" % (str(e), fname, exc_tb.tb_lineno)
#                self._hasError = True


    def hasError(self):
        return self._hasError

    def errorMessage(self):
        return self._errorMessage

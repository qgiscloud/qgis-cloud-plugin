# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DbConnectionCfg

 DB Connection configuration handling
                             -------------------
        begin                : 2011-09-21
        copyright            : (C) 2011 by Sourcepole
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

from PyQt4.QtCore import *
from pg8000 import DBAPI
from qgis.core import *


class DbConnectionCfg:

    CLOUD_DB_HOSTS = ['db.qgiscloud.com', 'spacialdb.com']

    def __init__(self, host, port, database, username, password,
                 sslmode=0, estimatedMetadata=True):  # sslmode 0 = prefer
        self.name = DbConnectionCfg.conn_name(database)
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.sslmode = sslmode
        self.estimatedMetadata = estimatedMetadata

    @staticmethod
    def conn_name(db_name):
        return "QGISCloud %s" % db_name

    @staticmethod
    def connection_key(conn_name):
        return u"/PostgreSQL/connections/%s" % conn_name

    def key(self):
        return self.connection_key(self.name)

    @classmethod
    def from_settings(cls, conn_name):
        settings = QSettings()
        key = DbConnectionCfg.connection_key(conn_name)
        settings.beginGroup(key)
        host = settings.value("host", type=str)
        port = settings.value("port", type=str)
        database = settings.value("database", type=str)
        username = settings.value("username", type=str)
        password = settings.value("password", type=str)
        sslmode = settings.value("sslmode", type=int)
        estimatedMetadata = settings.value("estimatedMetadata", type=bool)
        return cls(host, port, database, username, password, sslmode, estimatedMetadata)

    def store_connection(self):
        settings = QSettings()
        settings.setValue(self.key() + "/host", self.host)
        settings.setValue(self.key() + "/port", self.port)
        settings.setValue(self.key() + "/database", self.database)
        settings.setValue(self.key() + "/username", self.username)
        settings.setValue(self.key() + "/password", self.password)
        settings.setValue(self.key() + "/sslmode", self.sslmode)
        settings.setValue(self.key() + "/saveUsername", True)
        settings.setValue(self.key() + "/savePassword", True)
        settings.setValue(self.key() + "/geometryColumnsOnly", True)
        settings.setValue(self.key() + "/estimatedMetadata", self.estimatedMetadata)

    @staticmethod
    def remove_connection(conn_name):
        settings = QSettings()
        settings.remove(DbConnectionCfg.connection_key(conn_name))

    #Find matching connections in settings
    @staticmethod
    def get_cloud_db_connections(db_name):
        connection_names = []
        settings = QSettings()
        settings.beginGroup(u"/PostgreSQL/connections")
        for name in settings.childGroups():
            settings.beginGroup(name)
            db = settings.value("database", type=str)
            host = settings.value("host", type=str)
            if db == db_name and host in DbConnectionCfg.CLOUD_DB_HOSTS:
                connection_names.append(name)
            settings.endGroup()
        settings.endGroup()
        return connection_names

    def description(self):
        return unicode(QCoreApplication.translate("QgisCloudPluginDialog",
                       "host: %s port: %s database: %s username: %s password: %s")) % \
            (self.host, self.port, self.database, self.username, self.password)

    def ogr_connection_descr(self):
        return "PG:host='%s' port='%s' dbname='%s' user='%s' password='%s'" % (
            self.host, self.port, self.database, self.username, self.password)

    def data_source_uri(self):
        uri = QgsDataSourceURI()
        uri.setConnection(
            self.host,
            self.port,
            self.database,
            self.username,
            self.password,
            QgsDataSourceURI.SSLmode(self.sslmode)
        )
        uri.setUseEstimatedMetadata(self.estimatedMetadata)
        return uri

    def dbapi_connection(self, timeout=3):
        return DBAPI.connect(
            host=self.host,
            port=int(self.port),
            database=self.database,
            user=self.username,
            password=self.password,
            socket_timeout=timeout,  # s
            ssl=(self.sslmode != QgsDataSourceURI.SSLdisable)
        )

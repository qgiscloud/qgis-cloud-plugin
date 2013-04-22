# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DbConnections

 Manage QGIS connections to QGISCloud databases
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
from PyQt4.QtGui import *
from pg8000 import DBAPI
from qgis.core import *
import time
import socket

class DbConnections:

    CLOUD_DB_HOSTS = ['spacialdb.com',  'beta.spacialdb.com']

    def __init__(self):
        pass

    def get_cloud_db_connections(self, db_name):
        connection_names = []
        settings = QSettings()
        settings.beginGroup(u"/PostgreSQL/connections")
        for name in settings.childGroups():
            settings.beginGroup(name)
            db = settings.value("database").toString()
            host = settings.value("host").toString()
            if db == db_name and host in self.CLOUD_DB_HOSTS:
                connection_names.append(name)
            settings.endGroup()
        settings.endGroup()
        return connection_names

    def add(self, name, host, port, database, username, password):
        settings = QSettings()
        key = u"/PostgreSQL/connections/" + name
        settings.setValue(key + "/host", QVariant(host))
        settings.setValue(key + "/port", port)
        settings.setValue(key + "/database", QVariant(database))
        settings.setValue(key + "/username", QVariant(username))
        settings.setValue(key + "/password", QVariant(password))
        settings.setValue(key + "/sslmode", 0) # prefer
        settings.setValue(key + "/saveUsername", True)
        settings.setValue(key + "/savePassword", True)
        settings.setValue(key + "/geometryColumnsOnly", True)
        settings.setValue(key + "/estimatedMetadata", True)

    def remove(self, name):
        settings = QSettings()
        key = u"/PostgreSQL/connections/" + name
        settings.remove(key)

    def refresh(self, dbs, user):
        cloud_connections_key = u"/qgiscloud/connections/%s" % user
        settings = QSettings()

        cloud_dbs_from_server = dbs.keys()
        cloud_dbs_from_settings = map(lambda conn: str(conn), settings.value(cloud_connections_key).toStringList())

        # remove obsolete connections
        for db_name in (set(cloud_dbs_from_settings) - set(cloud_dbs_from_server)):
            for connection in self.get_cloud_db_connections(db_name):
                self.remove(connection)

        # add missing connections
        for db_name in cloud_dbs_from_server:
            if len(self.get_cloud_db_connections(db_name)) == 0:
                connection = "QGISCloud %s" % db_name
                self.add(connection, dbs[db_name]['host'], dbs[db_name]['port'], db_name, dbs[db_name]['username'], dbs[db_name]['password'])

        # store cloud db names in settings
        if len(cloud_dbs_from_server) > 0:
            settings.setValue(cloud_connections_key, cloud_dbs_from_server)
        else:
            settings.remove(cloud_connections_key)

    def cloud_layer_uri(self, db_name, table_name, geom_column):
        # find db connection and create uri
        uri = QgsDataSourceURI()
        settings = QSettings()
        settings.beginGroup(u"/PostgreSQL/connections")
        connections = self.get_cloud_db_connections(db_name)
        if len(connections) > 0:
            settings.beginGroup(connections[0])
            # create uri
            uri.setConnection(
                settings.value("host").toString(),
                settings.value("port").toString(),
                settings.value("database").toString(),
                settings.value("username").toString(),
                settings.value("password").toString(),
                QgsDataSourceURI.SSLmode(settings.value("sslmode").toInt()[0])
            )
            uri.setUseEstimatedMetadata(settings.value("estimatedMetadata").toBool())
            uri.setDataSource("", table_name, geom_column)

            settings.endGroup()
        settings.endGroup()

        return uri

    def isPortOpen(self, db_name):
        uri = self.cloud_layer_uri(db_name, "", "")
        host = str(uri.host())
        port = uri.port().toInt()[0]
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((host, port))
            s.shutdown(2)
            return True
        except:
            return False

    # workaround: wait until SpacialDB database is available
    def wait_for_db(self, db_name):
        uri = self.cloud_layer_uri(db_name, "", "")
        ok = False
        retries = 5
        while not ok and retries > 0:
            try:
                connection = DBAPI.connect(
                     host = str(uri.host()),
                     port = uri.port().toInt()[0],
                     database = str(uri.database()),
                     user = str(uri.username()),
                     password = str(uri.password()),
                     socket_timeout = 3, #3s
                     ssl = (uri.sslMode() != QgsDataSourceURI.SSLdisable)
                )
                connection.close()
                ok = True
            except Exception: # as err:
                retries -= 1
                if retries == 0:
                    raise
                else:
                    time.sleep(3)

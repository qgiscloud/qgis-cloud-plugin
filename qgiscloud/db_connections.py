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
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import *
from .db_connection_cfg import DbConnectionCfg
import time
import socket


class DbConnections(object):

    def __init__(self):
        self._dbs = {}  # Map<dbname, DbConnectionCfg>
        self._dbs_refreshed = False

    def add_from_json(self, db):
        self._dbs[db['name']] = DbConnectionCfg(
            db['host'], db['port'], db['name'], db['username'], db['password'])

        # add DB host to list of supported cloud DB hosts
        if db['host'] not in DbConnectionCfg.CLOUD_DB_HOSTS:
            DbConnectionCfg.CLOUD_DB_HOSTS.append(db['host'])

    def count(self):
        return len(self._dbs)

    def iteritems(self):
        return iter(list(self._dbs.items()))

    def db(self, dbname):
        return self._dbs[str(dbname)]
        
        
    def db_size(self):
        usedSpace = 0
        self.numDbs = len(list(self._dbs.keys()))
        for db in list(self._dbs.keys()):
            try:
                conn = self.db(db).psycopg_connection()
            except:
                continue
            cursor = conn.cursor()
            sql = "SELECT pg_database_size('" + str(db) + "')"
            cursor.execute(sql)
            usedSpace += int(cursor.fetchone()[0])
            cursor.close()
            conn.close

        # Used space in MB
        usedSpace /= 1024 * 1024
        return usedSpace

    def refreshed(self):
        return self._dbs_refreshed
        
    def refresh(self, user):
        cloud_connections_key = u"/qgiscloud/connections/%s" % user
        settings = QSettings()

        cloud_dbs_from_server = list(self._dbs.keys())
        stored_connections = settings.value(cloud_connections_key) or []
        cloud_dbs_from_settings = [str(conn) for conn in stored_connections]

        # remove obsolete connections
        for db_name in (set(cloud_dbs_from_settings) - set(cloud_dbs_from_server)):
            for connection in DbConnectionCfg.get_cloud_db_connections(db_name):
                DbConnectionCfg.remove_connection(connection)

        # add missing or changed connections
        for db_name in cloud_dbs_from_server:
            cfg = self.db(db_name)
            if len(DbConnectionCfg.get_cloud_db_connections(db_name)) == 0 or \
                    cfg.changed:
                cfg.store_connection()

        # store cloud db names in settings
        if len(cloud_dbs_from_server) > 0:
            settings.setValue(cloud_connections_key, cloud_dbs_from_server)
        else:
            settings.remove(cloud_connections_key)

        self._dbs_refreshed = True

    def cloud_layer_uri(self, db_name, schema_name,  table_name, geom_column):
        uri = None
        # find db connection and create uri
        connections = DbConnectionCfg.get_cloud_db_connections(db_name)
        if len(connections) > 0:
            conn = DbConnectionCfg.from_settings(connections[0])
            uri = conn.data_source_uri()
            uri.setDataSource(schema_name,  table_name, geom_column)
        return uri

    def isPortOpen(self, db_name):
        uri = self.cloud_layer_uri(db_name, "", "", "")
        if not uri.port():
            return False
        host = str(uri.host())
        port = int(uri.port())
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((host, port))
            s.shutdown(2)
            return True
        except:
            return False

    @staticmethod
    def wait_for_new_db(db):
        """Wait until new cloud database is available after creation
        (creation is asynchronous).

        :param dict db: new DB connection as
            {
                host: '<host>',
                port: <port>,
                name: '<DB name>',
                username: '<username>',
                password: '<password>'
            }
        """
        conn_cfg = DbConnectionCfg(db['host'], db['port'], db['name'], db['username'], db['password'])
        new_db_ready = False
        tries = 20
        while not new_db_ready and tries > 0:
            tries -= 1
            QApplication.processEvents()
            time.sleep(2)
            conn = conn_cfg.psycopg_connection(silent=True)
            if conn is not None:
                conn.close()
                new_db_ready = True

        return new_db_ready

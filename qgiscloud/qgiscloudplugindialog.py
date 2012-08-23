# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QgisCloudPluginDialog
                                 A QGIS plugin
 Publish maps on qgiscloud.com
                             -------------------
        begin                : 2011-04-04
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
from PyQt4.QtXml import *
from qgis.core import *
from ui_qgiscloudplugin import Ui_QgisCloudPlugin
from ui_login import Ui_LoginDialog
from qgiscloudapi.qgiscloudapi import *
from db_connections import DbConnections
from local_data_sources import LocalDataSources
from data_upload import DataUpload
import os.path
import sys
import urllib
import traceback
import re
import time
import platform

class QgisCloudPluginDialog(QDockWidget):
    COLUMN_LAYERS = 0
    COLUMN_DATA_SOURCE = 1
    COLUMN_TABLE_NAME = 2
    COLUMN_GEOMETRY_TYPE = 3
    COLUMN_SRID = 4

    def __init__(self, iface, version):
        QDockWidget.__init__(self, None)
        self.iface = iface
        self.version = version
        # Set up the user interface from Designer.
        self.ui = Ui_QgisCloudPlugin()
        self.ui.setupUi(self)

        self.ui.tblLocalLayers.setColumnCount(5)
        header = ["Layers", "Data source", "Table name", "Geometry type", "SRID"]
        self.ui.tblLocalLayers.setHorizontalHeaderLabels(header)
        self.ui.tblLocalLayers.resizeColumnsToContents()
        # TODO; delegate for read only columns

        self.ui.btnUploadData.setEnabled(False)
        self.ui.uploadProgressBar.hide()
        self.ui.btnPublishMapUpload.hide()
        self.ui.lblLoginStatus.hide()

        # map<data source, table name>
        self.data_sources_table_names = {}
        self.dbs_refreshed = False
        # flag to disable update of local data sources during upload
        self.do_update_local_data_sources = True

        QObject.connect(self.ui.btnLogin, SIGNAL("clicked()"), self.refresh_databases)
        QObject.connect(self.ui.btnDbCreate, SIGNAL("clicked()"), self.create_database)
        QObject.connect(self.ui.btnDbDelete, SIGNAL("clicked()"), self.delete_database)
        QObject.connect(self.ui.btnDbRefresh, SIGNAL("clicked()"), self.refresh_databases)
        QObject.connect(self.ui.tabDatabases, SIGNAL("itemSelectionChanged()"), self.select_database)
        QObject.connect(self.ui.btnPublishMap, SIGNAL("clicked()"), self.publish_map)
        QObject.connect(self.ui.btnRefreshLocalLayers, SIGNAL("clicked()"), self.refresh_local_data_sources)
        QObject.connect(self.iface, SIGNAL("newProjectCreated()"), self.reset_load_data)
        QObject.connect(QgsMapLayerRegistry.instance(), SIGNAL("layerWillBeRemoved(QString)"), self.remove_layer)
        QObject.connect(QgsMapLayerRegistry.instance(), SIGNAL("layerWasAdded(QgsMapLayer *)"), self.add_layer)
        QObject.connect(self.ui.cbUploadDatabase, SIGNAL("currentIndexChanged(int)"), self.upload_database_selected)
        QObject.connect(self.ui.btnUploadData, SIGNAL("clicked()"), self.upload_data)
        QObject.connect(self.ui.btnPublishMapUpload, SIGNAL("clicked()"), self.publish_map)

        self.read_settings()
        self.update_urls()
        self.api = API()
        self.db_connections = DbConnections()
        self.local_data_sources = LocalDataSources()
        self.data_upload = DataUpload(self.iface, self.statusBar(), self.ui.uploadProgressBar, self.api, self.db_connections)

        self.ui.editServer.setText(self.api.api_url())

    def __del__(self):
        QObject.disconnect(self.iface, SIGNAL("newProjectCreated()"), self.reset_load_data)
        QObject.disconnect(QgsMapLayerRegistry.instance(), SIGNAL("layerWillBeRemoved(QString)"), self.remove_layer)
        QObject.disconnect(QgsMapLayerRegistry.instance(), SIGNAL("layerWasAdded(QgsMapLayer *)"), self.add_layer)

    def statusBar(self):
        return self.iface.mainWindow().statusBar()

    def map(self):
        project = QgsProject.instance()
        name = ''
        try:
            name = re.search(r'.*/(.+).qgs', project.fileName()).group(1)
        except:
            name = ''
        return name

    def store_settings(self):
        s = QSettings()
        s.setValue("qgiscloud/user", self.user)

    def read_settings(self):
        s = QSettings()
        self.user = s.value("qgiscloud/user").toString()

    def _version_info(self):
        return {'versions': {'plugin': self.version, 'QGIS': QGis.QGIS_VERSION, 'OS': platform.platform()}}

    def check_login(self):
        if not self.api.check_auth():
            login_dialog = QDialog(self)
            login_dialog.ui = Ui_LoginDialog()
            login_dialog.ui.setupUi(login_dialog)
            login_dialog.ui.editUser.setText(self.user)
            login_ok = False
            while not login_ok:
                if not login_dialog.exec_():
                    self.api.set_auth(user=login_dialog.ui.editUser.text(), password=None)
                    return login_ok
                self.api.set_auth(user=login_dialog.ui.editUser.text(), password=login_dialog.ui.editPassword.text())
                try:
                    self.api.check_login(version_info=self._version_info())
                    self.user = login_dialog.ui.editUser.text()
                    self.ui.serviceLinks.setCurrentIndex(1)
                    self.update_urls()
                    self.store_settings()
                    self.ui.btnLogin.hide()
                    self.ui.lblSignup.hide()
                    self.ui.lblLoginStatus.setText("Logged in as %s" % self.user)
                    self.ui.lblLoginStatus.show()
                    QMessageBox.information(self, "Login successful", "Logged in as %s" % self.user)
                    login_ok = True
                except (UnauthorizedError, TokenRequiredError, ConnectionException):
                    QMessageBox.critical(self, "Login failed", "Wrong user name or password")
                    login_ok = False
        return True

    def create_database(self):
        if self.check_login():
            db = self.api.create_database()
            # {u'username': u'jhzgpfwi_qgiscloud', u'host': u'beta.spacialdb.com', u'password': u'11d7338c', u'name': u'jhzgpfwi_qgiscloud', u'port': 9999}
            self.show_api_error(db)
            self.refresh_databases()

    def delete_database(self):
        if self.check_login():
            name = self.ui.tabDatabases.currentItem().text()
            msgBox = QMessageBox()
            msgBox.setText("Delete QGIS Cloud database.")
            msgBox.setInformativeText("Do you want to delete the database \"%s\"?" % name)
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msgBox.setDefaultButton(QMessageBox.Cancel)
            msgBox.setIcon(QMessageBox.Question)
            ret = msgBox.exec_()
            if ret == QMessageBox.Ok:
                self.setCursor(Qt.WaitCursor)
                result = self.api.delete_database(name)
                self.show_api_error(result)
                self.ui.btnDbDelete.setEnabled(False)
                self.refresh_databases()
                while name in self.dbs.keys():
                  # wait until db is deleted on server
                  time.sleep(2)
                  self.refresh_databases()
                self.unsetCursor()

    def select_database(self):
        self.ui.btnDbDelete.setEnabled(len(self.ui.tabDatabases.selectedItems()) > 0)

    def refresh_databases(self):
        if self.check_login():
            db_list = self.api.read_databases()
            if self.show_api_error(db_list):
              return
            self.dbs = {} # Map<dbname, {dbattributes}>
            for db in db_list:
                #db example: {"host":"spacialdb.com","connection_string":"postgres://sekpjr_jpyled:d787b609@spacialdb.com:9999/sekpjr_jpyled","name":"sekpjr_jpyled","username":"sekpjr_jpyled","port":9999,"password":"d787b609"}
                self.dbs[db['name']] = {'host': db['host'], 'port': db['port'], 'username': db['username'], 'password': db['password']}

            self.ui.tabDatabases.clear()
            self.ui.btnDbDelete.setEnabled(False)
            self.ui.cbUploadDatabase.clear()
            if len(self.dbs) == 0:
                self.ui.cbUploadDatabase.addItem("Create new database")
            elif len(self.dbs) > 1:
                self.ui.cbUploadDatabase.addItem("Select database")
            #import rpdb2; rpdb2.start_embedded_debugger("dbg")
            for name, db in self.dbs.iteritems():
                it = QListWidgetItem(name)
                it.setToolTip("host: %s port: %s database: %s username: %s password: %s" % (db['host'], db['port'], name, db['username'], db['password']))
                self.ui.tabDatabases.addItem(it)
                self.ui.cbUploadDatabase.addItem(name)
            self.db_connections.refresh(self.dbs, self.user)
            self.dbs_refreshed = True

    def update_urls(self):
        self.update_url(self.ui.lblWMS, self.user, self.map())
        self.update_url(self.ui.lblWebmap, self.user, self.map())
        self.update_url(self.ui.lblMobileMap, self.user, self.map())
        #self.update_url(self.ui.lblWFS, self.user, self.map())

    def update_url(self, label, user, map):
        text = re.sub(r'qgiscloud.com/.*?/[^/"<>]*', 'qgiscloud.com/%s/%s' % (user, map), unicode(label.text()))
        label.setText(text)

    def read_maps(self):
        #map = self.api.read_map("1")
        if self.check_login():
            maps = self.api.read_maps()

    def check_project_saved(self):
        cancel = False
        project = QgsProject.instance()
        if project.isDirty():
            msgBox = QMessageBox()
            msgBox.setText("The project has been modified.")
            msgBox.setInformativeText("Do you want to save your changes?")
            msgBox.setStandardButtons(QMessageBox.Save | QMessageBox.Ignore | QMessageBox.Cancel)
            msgBox.setDefaultButton(QMessageBox.Save)
            ret = msgBox.exec_()
            if ret == QMessageBox.Save:
                project.write()
            elif ret == QMessageBox.Cancel:
                cancel = True
        return cancel

    def publish_map(self):
        cancel = self.check_project_saved()
        if cancel:
            return
        fname = unicode(QgsProject.instance().fileName())
        if self.check_login() and self.check_layers():
            self.statusBar().showMessage(u"Publishing map")
            try:
                fullExtent = self.iface.mapCanvas().fullExtent()
                config = { 'fullExtent': {
                    'xmin': fullExtent.xMinimum(), 'ymin': fullExtent.yMinimum(),
                    'xmax': fullExtent.xMaximum(), 'ymax': fullExtent.yMaximum()
                }}
                map = self.api.create_map(self.map(), fname, config)['map']
                #QMessageBox.information(self, "create_map", str(map['config']))
                self.show_api_error(map)
                if map['config']['missingSvgSymbols']:
                    self.publish_symbols(map['config']['missingSvgSymbols'])
                self.update_urls()
                self.ui.btnPublishMapUpload.hide()
                self.statusBar().showMessage(u"Map successfully published")
            except Exception:
                self.statusBar().showMessage("")
                self._exception_message("Error uploading project")

    def _exception_message(self, title):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        stack = traceback.format_exc().splitlines()
        msgBox = QMessageBox(QMessageBox.Critical, title, "")
        msgBox.setTextFormat(Qt.RichText)
        msgBox.setText("<b>%s</b><br/>%s" % (stack[-1], stack[1]))
        maillink = "<a href=\"mailto:%s?subject=QGISCloud exception: %s&body=%s\">Mail to support</a>" % \
            ("support@qgiscloud.com", title, urllib.quote(traceback.format_exc() + str(self._version_info())))
        msgBox.setInformativeText(maillink)
        msgBox.exec_()

    def publish_symbols(self, missingSvgSymbols):
        self.statusBar().showMessage(u"Uploading SVG symbols")
        #Search and upload symbol files
        for sym in missingSvgSymbols:
            for path in QgsApplication.svgPaths():
                fullpath = path + sym
                if os.path.isfile(fullpath):
                    self.api.create_graphic(sym, fullpath)


    def reset_load_data(self):
        self.update_local_data_sources([])
        self.ui.btnUploadData.setEnabled(False)
        self.ui.btnPublishMapUpload.hide()

    def remove_layer(self, layer_id):
        if self.dbs_refreshed and self.do_update_local_data_sources:
            # skip layer if layer will be removed
            self.update_local_layers(layer_id)
            self.activate_upload_button()

    def add_layer(self):
        if self.dbs_refreshed and self.do_update_local_data_sources:
            self.update_local_layers()
            self.activate_upload_button()

    def update_local_layers(self, skip_layer_id=None):
        local_layers, unsupported_layers = self.local_data_sources.local_layers(skip_layer_id)
        self.update_local_data_sources(local_layers)

        return local_layers, unsupported_layers

    def check_layers(self):
        local_layers, unsupported_layers = self.update_local_layers()
        if local_layers or unsupported_layers:
            message = ""

            if local_layers:
                title = "Local layers found"
                message += "Some layers are using local data. You can upload local layers to your cloud database in the 'Upload Data' tab.\n\n"

            if unsupported_layers:
                title = "Unsupported layers found"
                message += "Raster, plugin or geometryless layers are not supported:\n\n"
                layer_types = ["No geometry", "Raster", "Plugin"]
                for layer in sorted(unsupported_layers, key=lambda layer: layer.name()):
                    message += "  -  %s (%s)\n" % (layer.name(), layer_types[layer.type()])
                message += "\nPlease remove or replace above layers before publishing your map.\n"
                message += "For raster data you can use public WMS layers or the OpenLayers Plugin."

            QMessageBox.information(self, title, message)

            self.refresh_databases()
            self.ui.tabWidget.setCurrentIndex(1)
            return False

        return True

    def update_local_data_sources(self, local_layers):
        # update table names lookup
        self.update_data_sources_table_names()

        self.local_data_sources.update_local_data_sources(local_layers)

        # update GUI
        while self.ui.tblLocalLayers.rowCount() > 0:
            self.ui.tblLocalLayers.removeRow(0)

        geometry_types = {
            QGis.WKBUnknown: "Unknown",
            QGis.WKBPoint: "Point",
            QGis.WKBMultiPoint: "MultiPoint",
            QGis.WKBLineString: "LineString",
            QGis.WKBMultiLineString: "MultiLineString",
            QGis.WKBPolygon: "Polygon",
            QGis.WKBMultiPolygon: "MultiPolygon",
            100: "No geometry" # FIXME: QGis.WKBNoGeometry
            # FIXME: 2.5d
        }

        for data_source, layers in self.local_data_sources.iteritems():
            layer_names = []
            for layer in layers:
                layer_names.append(str(layer.name()))
            layers_item = QTableWidgetItem(", ".join(layer_names))
            layers_item.setToolTip("\n".join(layer_names))
            data_source_item = QTableWidgetItem(data_source)
            data_source_item.setToolTip(data_source)
            table_name = layers[0].name() # find a better table name if there are multiple layers with same data source?
            if data_source in self.data_sources_table_names:
                # use current table name if available to keep changes by user
                table_name = self.data_sources_table_names[data_source]
            table_name_item = QTableWidgetItem(QgisCloudPluginDialog.launder_pg_name(table_name))
            wkbType = layers[0].wkbType() #FIXME: message for unsupported types (2.5D)
            geometry_type_item = QTableWidgetItem(geometry_types[wkbType])
            if layers[0].providerType() == "ogr":
                geometry_type_item.setToolTip("Note: OGR features will be converted to MULTI-type")
            srid_item = QTableWidgetItem(layers[0].crs().authid())

            row = self.ui.tblLocalLayers.rowCount()
            self.ui.tblLocalLayers.insertRow(row)
            self.ui.tblLocalLayers.setItem(row, self.COLUMN_LAYERS, layers_item)
            self.ui.tblLocalLayers.setItem(row, self.COLUMN_DATA_SOURCE, data_source_item)
            self.ui.tblLocalLayers.setItem(row, self.COLUMN_TABLE_NAME, table_name_item)
            self.ui.tblLocalLayers.setItem(row, self.COLUMN_GEOMETRY_TYPE, geometry_type_item)
            self.ui.tblLocalLayers.setItem(row, self.COLUMN_SRID, srid_item)

        if self.local_data_sources.count() > 0:
            self.ui.tblLocalLayers.resizeColumnsToContents()
            self.ui.tblLocalLayers.setColumnWidth(self.COLUMN_LAYERS, 100)
            self.ui.tblLocalLayers.setColumnWidth(self.COLUMN_DATA_SOURCE, 100)
            self.ui.tblLocalLayers.sortItems(self.COLUMN_DATA_SOURCE)
            self.ui.tblLocalLayers.setSortingEnabled(False)
        else:
            self.ui.btnUploadData.setEnabled(False)

        self.statusBar().showMessage(u"Updated local data sources")

    @staticmethod
    def launder_pg_name(name):
        return re.sub(r"[#'-]", '_', str(name).lower()) #OGRPGDataSource::LaunderName

    def refresh_local_data_sources(self):
        if not self.dbs_refreshed:
            # get dbs on first refresh
            self.refresh_databases()
        self.do_update_local_data_sources = True
        self.update_local_layers()
        self.activate_upload_button()

    def update_data_sources_table_names(self):
        if self.local_data_sources.count() == 0:
            self.data_sources_table_names.clear()
        else:
            # remove table names without data sources
            keys_to_remove = []
            for key in self.data_sources_table_names.iterkeys():
                if self.local_data_sources.layers(key) == None:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.data_sources_table_names[key]

            # update table names
            for row in range(0, self.ui.tblLocalLayers.rowCount()):
                data_source = str(self.ui.tblLocalLayers.item(row, self.COLUMN_DATA_SOURCE).text())
                table_name = str(self.ui.tblLocalLayers.item(row, self.COLUMN_TABLE_NAME).text())
                self.data_sources_table_names[data_source] = table_name

    def upload_database_selected(self, index):
        self.activate_upload_button()

    def activate_upload_button(self):
        self.ui.btnUploadData.setEnabled((len(self.dbs) <= 1 or self.ui.cbUploadDatabase.currentIndex() > 0) and self.local_data_sources.count() > 0)
        self.ui.btnPublishMapUpload.hide()

    def upload_data(self):
        if self.check_login():
            if self.local_data_sources.count() == 0:
                return

            if len(self.dbs) == 0:
                # create db
                self.statusBar().showMessage(u"Create new database...")
                QApplication.processEvents() # refresh status bar
                self.create_database()

            db_name = self.ui.cbUploadDatabase.currentText()

            # disable update of local data sources during upload, as there are temporary layers added and removed
            self.do_update_local_data_sources = False
            self.setCursor(Qt.WaitCursor)

            # Map<data_source, {table: table, layers: layers}>
            data_sources_items = {}
            for row in range(0, self.ui.tblLocalLayers.rowCount()):
                data_source = str(self.ui.tblLocalLayers.item(row, self.COLUMN_DATA_SOURCE).text())
                layers = self.local_data_sources.layers(data_source)
                if layers != None:
                    table_name = str(self.ui.tblLocalLayers.item(row, self.COLUMN_TABLE_NAME).text())
                    data_sources_items[data_source] = {'table': table_name, 'layers': layers}

            try:
                #Via QGIS providers:
                #success = self.data_upload.upload_data(db_name, data_sources_items, self.ui.cbReplaceLocalLayers.isChecked())
                #Via OGR:
                success = self.data_upload.ogr2ogr(db_name, data_sources_items, self.ui.cbReplaceLocalLayers.isChecked())
            except Exception:
                success = False
                self._exception_message("Data upload error")

            self.unsetCursor()
            self.statusBar().showMessage("")
            self.do_update_local_data_sources = True

            if success and self.ui.cbReplaceLocalLayers.isChecked():
                self.update_local_layers()

                # show save project dialog
                msgBox = QMessageBox()
                msgBox.setWindowTitle("QGIS Cloud")
                msgBox.setText("The project is ready for publishing.")
                msgBox.setInformativeText("Do you want to save your changes?")
                msgBox.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
                msgBox.setDefaultButton(QMessageBox.Save)
                ret = msgBox.exec_()
                if ret == QMessageBox.Save:
                    self.iface.actionSaveProjectAs().trigger()
                    self.ui.btnPublishMapUpload.show()

    def show_api_error(self, result):
        if 'error' in result:
            QMessageBox.critical(self, "QGIS Cloud Error", "%s" % result['error'])
            self.statusBar().showMessage(u"Error")
            return True
        else:
            return False

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
from builtins import str
from builtins import range
from qgis.PyQt.QtCore import Qt, QSettings, QFileInfo, pyqtSlot
from qgis.PyQt.QtWidgets import QApplication, QDockWidget,   QTableWidgetItem, QListWidgetItem, \
                                                        QDialog, QMessageBox, QAbstractItemView, QWidget, QLabel,  QVBoxLayout,  \
                                                        QFileDialog
from qgis.PyQt.QtGui import QPalette, QColor
from qgis.core import *
from .ui_qgiscloudplugin import Ui_QgisCloudPlugin
from .ui_login import Ui_LoginDialog
from .qgiscloudapi.qgiscloudapi import *
from .db_connections import DbConnections
from .local_data_sources import LocalDataSources
from .data_upload import DataUpload
from .doAbout import DlgAbout
from .error_report_dialog import ErrorReportDialog
import os.path
import sys
import traceback
import string
import re
import time
import platform
import tempfile
from distutils.version import StrictVersion
from .mapsettingsdialog import MapSettingsDialog

class QgisCloudPluginDialog(QDockWidget):
    COLUMN_LAYERS = 0
    COLUMN_DATA_SOURCE = 1
    COLUMN_TABLE_NAME = 2
    COLUMN_GEOMETRY_TYPE = 3
    COLUMN_SRID = 4

    GEOMETRY_TYPES = {
        QgsWkbTypes.Unknown: "Unknown",
        QgsWkbTypes.NoGeometry: "No geometry",
        QgsWkbTypes.Point: "Point",
        QgsWkbTypes.MultiPoint: "MultiPoint",
        QgsWkbTypes.PointZ: "PointZ",
        QgsWkbTypes.MultiPointZ: "MultiPointZ",
        QgsWkbTypes.PointM: "PointM",
        QgsWkbTypes.MultiPointM: "MultiPointM",
        QgsWkbTypes.PointZM: "PointZM",
        QgsWkbTypes.MultiPointZM: "MultiPointZM",
        QgsWkbTypes.Point25D: "Point25D",
        QgsWkbTypes.MultiPoint25D: "MultiPoint25D",
        QgsWkbTypes.LineString: "LineString",
        QgsWkbTypes.MultiLineString: "LineString",
        QgsWkbTypes.LineStringZ: "LineStringZ",
        QgsWkbTypes.MultiLineStringZ: "LineStringZ",
        QgsWkbTypes.LineStringM: "LineStringM",
        QgsWkbTypes.MultiLineStringM: "LineStringM",
        QgsWkbTypes.LineStringZM: "LineStringZM",
        QgsWkbTypes.MultiLineStringZM: "LineStringZM",
        QgsWkbTypes.LineString25D: "LineString25D",
        QgsWkbTypes.MultiLineString25D: "MultiLineString25D",
        QgsWkbTypes.Polygon: "Polygon",
        QgsWkbTypes.MultiPolygon: "MultiPolygon",
        QgsWkbTypes.PolygonZ: "PolygonZ",
        QgsWkbTypes.MultiPolygonZ: "MultiPolygonZ",
        QgsWkbTypes.PolygonM: "PolygonM",
        QgsWkbTypes.MultiPolygonM: "MultiPolygonM",
        QgsWkbTypes.PolygonZM: "PolygonZM",
        QgsWkbTypes.MultiPolygonZM: "MultiPolygonZM",
        QgsWkbTypes.Polygon25D: "Polygon25D",
        QgsWkbTypes.MultiPolygon25D: "MultiPolygon25D",
        QgsWkbTypes.CircularString: "CircularString",
        QgsWkbTypes.CompoundCurve: "CompoundCurve",
        QgsWkbTypes.CurvePolygon: "CurvePolygon",
        QgsWkbTypes.MultiCurve: "MultiCurve",
        QgsWkbTypes.MultiSurface: "MultiSurface",
        QgsWkbTypes.CircularStringZ: "CircularStringZ",
        QgsWkbTypes.CompoundCurveZ: "CompoundCurveZ",
        QgsWkbTypes.CurvePolygonZ: "CurvePolygonZ",
        QgsWkbTypes.MultiCurveZ: "MultiCurveZ",
        QgsWkbTypes.MultiSurfaceZ: "MultiSurfaceZ",
        QgsWkbTypes.CircularStringM: "CircularStringM",
        QgsWkbTypes.CompoundCurveM: "CompoundCurveM",
        QgsWkbTypes.CurvePolygonM: "CurvePolygonM",
        QgsWkbTypes.MultiCurveM: "MultiCurveM",
        QgsWkbTypes.MultiSurfaceM: "MultiSurfaceM",
        QgsWkbTypes.CircularStringZM: "CircularStringZM",
        QgsWkbTypes.CompoundCurveZM: "CompoundCurveZM",
        QgsWkbTypes.CurvePolygonZM: "CurvePolygonZM",
        QgsWkbTypes.MultiCurveZM: "MultiCurveZM",
        QgsWkbTypes.MultiSurfaceZM: "MultiSurfaceZM",
    }

    PROJECT_INSTANCE = QgsProject.instance()


    def __init__(self, iface, version):
        QDockWidget.__init__(self, None)
        self.iface = iface
        self.clouddb = True
        self.version = version
        # Set up the user interface from Designer.
        self.ui = Ui_QgisCloudPlugin()
        self.ui.setupUi(self)
        self.storage_exceeded = True

        myAbout = DlgAbout()
        self.ui.aboutText.setText(
            myAbout.aboutString() +
            myAbout.contribString() +
            myAbout.licenseString() +
            "<p>Versions:<ul>" +
            "<li>QGIS: %s</li>" % str(Qgis.QGIS_VERSION).encode("utf-8") +
            "<li>Python: %s</li>" % sys.version.replace("\n", " ") +
            "<li>OS: %s</li>" % platform.platform() +
            "</ul></p>")

        data_protection_link = """<a href="http://qgiscloud.com/pages/privacy">%s</a>""" % (self.tr("Privacy Policy"))

        self.ui.lblVersionPlugin.setText("%s &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;%s" % (self.version,  data_protection_link))
        self.ui.lblVersionPlugin.setOpenExternalLinks(True)
#        self.ui.lblVersionPlugin.setText(self.version)

        self.ui.tblLocalLayers.setColumnCount(5)
        header = ["Layers", "Data source",
                  "Table name", "Geometry type", "SRID"]
        self.ui.tblLocalLayers.setHorizontalHeaderLabels(header)
        self.ui.tblLocalLayers.resizeColumnsToContents()
        self.ui.tblLocalLayers.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.ui.btnUploadData.setEnabled(False)
        self.ui.btnPublishMap.setEnabled(False)
        self.ui.btnMapDelete.setEnabled(False)
        self.ui.btnMapEdit.setEnabled(False)
        self.ui.progressWidget.hide()
        self.ui.btnLogout.hide()
        self.ui.lblLoginStatus.hide()
        self.ui.widgetServices.hide()
        self.ui.widgetDatabases.setEnabled(False)
        self.ui.widgetMaps.setEnabled(False)
        self.ui.labelOpenLayersPlugin.hide()

        try:
            from .openlayers_menu import OpenlayersMenu
            self.ui.btnBackgroundLayer.setMenu(OpenlayersMenu(self.iface))
        except:
                self.ui.btnBackgroundLayer.hide()
                self.ui.labelOpenLayersPlugin.show()

        # map<data source, table name>
        self.data_sources_table_names = {}
        # flag to disable update of local data sources during upload
        self.do_update_local_data_sources = True

        self.ui.btnLogin.clicked.connect(self.check_login)
        self.ui.btnDbCreate.clicked.connect(self.create_database)
        self.ui.btnDbDelete.clicked.connect(self.delete_database)
        self.ui.btnDbRefresh.clicked.connect(self.refresh_databases)
        self.ui.btnMapDelete.clicked.connect(self.delete_map)
        self.ui.btnMapEdit.clicked.connect(self.edit_map)
        self.ui.btnMapLoad.clicked.connect(self.map_load)
        self.ui.tabMaps.itemDoubleClicked.connect(self.map_load)
        self.ui.tabDatabases.itemSelectionChanged.connect(self.select_database)
        self.ui.tabMaps.itemSelectionChanged.connect(self.select_map)
        self.ui.btnPublishMap.clicked.connect(self.publish_map)
        self.ui.btnRefreshLocalLayers.clicked.connect(self.refresh_local_data_sources)
        self.iface.newProjectCreated.connect(self.reset_load_data)
        self.iface.projectRead.connect(self.reset_load_data)

        self.PROJECT_INSTANCE.layerWillBeRemoved.connect(self.remove_layer)
        self.PROJECT_INSTANCE.layerWasAdded.connect(self.add_layer)

        self.ui.cbUploadDatabase.currentIndexChanged.connect(lambda idx: self.activate_upload_button())
        self.ui.btnUploadData.clicked.connect(self.upload_data)

        self.ui.editServer.textChanged.connect(self.serverURL)
        self.ui.resetUrlBtn.clicked.connect(self.resetApiUrl)

        self.read_settings()
        self.api = API()
        self.db_connections = DbConnections()
        self.local_data_sources = LocalDataSources()
        self.data_upload = DataUpload(
            self.iface, self.statusBar(), self.ui.lblProgress, self.api,
            self.db_connections)

        if self.URL == "":
            self.ui.editServer.setText(self.api.api_url())
        else:
            self.ui.editServer.setText(self.URL)

        self.palette_red = QPalette(self.ui.lblVersionPlugin.palette())
        self.palette_red.setColor(QPalette.WindowText, Qt.red)

    def unload(self):
        self.do_update_local_data_sources = False
        if self.iface:
            self.iface.newProjectCreated.disconnect(self.reset_load_data)
            self.iface.projectRead.disconnect(self.reset_load_data)

        if self.PROJECT_INSTANCE:
            self.PROJECT_INSTANCE.layerWillBeRemoved.disconnect(self.remove_layer)
            self.PROJECT_INSTANCE.layerWasAdded.disconnect(self.add_layer)


    def statusBar(self):
        return self.iface.mainWindow().statusBar()

    def map(self):
        project = QgsProject.instance()
        name = os.path.splitext(os.path.basename(str(project.fileName())))[0]

        # Allowed chars for QGISCloud map name: /\A[A-Za-z0-9\_\-]*\Z/
        name = str(name).encode('ascii', 'replace')  # Replace non-ascii chars

        # Replace withespace
        name = name.replace(b" ",  b"_")
        return name

    def resetApiUrl(self):
        self.ui.editServer.setText(self.api.api_url())

    def serverURL(self, URL):
        self.URL = URL
        self.store_settings()

    def store_settings(self):
        s = QSettings()
        s.setValue("qgiscloud/user", self.user)
        s.setValue("qgiscloud/URL", self.URL)

    def read_settings(self):
        s = QSettings()
        self.user = s.value("qgiscloud/user", "")
        self.URL = s.value("qgiscloud/URL", "")

    def _update_clouddb_mode(self, clouddb):
        self.clouddb = clouddb
        self.ui.widgetDatabases.setVisible(self.clouddb)
        tab_index = 1
        tab_name = QApplication.translate("QgisCloudPlugin", "Upload Data")
        visible = (self.ui.tabWidget.indexOf(self.ui.uploadTab) == tab_index)
        if visible and not self.clouddb:
            self.ui.tabWidget.removeTab(tab_index)
        elif not visible and self.clouddb:
            self.ui.tabWidget.insertTab(tab_index, self.ui.uploadTab, tab_name)

    def _version_info(self):
        return {
            'versions': {
                'plugin': self.version.encode('utf-8').decode('utf-8'),
                'QGIS': Qgis.QGIS_VERSION.encode('utf-8').decode('utf-8'),
                'OS': platform.platform().encode('utf-8').decode('utf-8'),
                'Python': sys.version.encode('utf-8').decode('utf-8')
            }
        }

    def check_login(self):
        version_ok = True
        if not self.api.check_auth():
            login_dialog = QDialog(self)
            login_dialog.ui = Ui_LoginDialog()
            login_dialog.ui.setupUi(login_dialog)
            login_dialog.ui.editUser.setText(self.user)
            login_ok = False
            while not login_ok and version_ok:
                self.api.set_url(self.api_url())
                if not login_dialog.exec_():
                    self.api.set_auth(
                        user=login_dialog.ui.editUser.text(), password=None)
                    return login_ok
                self.api.set_auth(
                    user=login_dialog.ui.editUser.text(),
                    password=login_dialog.ui.editPassword.text())
                try:
                    login_info = self.api.check_login(
                        version_info=self._version_info())

                    if not login_info['tos_accepted']:
                        result = QMessageBox.information(
                            None,
                            self.tr("Accept new Privacy Policy"),
                            self.tr("""Due to the GDPR qgiscloud.com has a new <a href='http://qgiscloud.com/en/pages/privacy'> Privacy Policy </a>.
                            To continue using qgiscloud.com, you must accept the new policy. """),
                            QMessageBox.StandardButtons(
                                QMessageBox.No |
                                QMessageBox.Yes))

                        if result == QMessageBox.No:
                            login_ok = False
                            return
                        else:
                            result = self.api.accept_tos()

                    self.user = login_dialog.ui.editUser.text()
                    self._update_clouddb_mode(login_info['clouddb'])
                    version_ok = StrictVersion(self.version) >= StrictVersion(login_info['current_plugin'])
                    if not version_ok:
                        self.ui.lblVersionPlugin.setPalette(self.palette_red)
                        QMessageBox.information(None, self.tr('New Version'),  self.tr('New plugin release {version} is available! Please upgrade the QGIS Cloud plugin.').format(version=login_info['current_plugin']))
                    self.store_settings()
                    self.ui.btnLogin.hide()
                    self.ui.lblSignup.hide()
                    self.ui.btnLogout.show()
                    self.ui.widgetDatabases.setEnabled(True)
                    self.ui.widgetMaps.setEnabled(True)

                    self.ui.lblLoginStatus.setText(
                        self.tr("Logged in as {0} ({1})").format(self.user, login_info['plan']))
                    self.ui.lblLoginStatus.show()
                    self._push_message(
                        self.tr("QGIS Cloud"),
                        self.tr("Logged in as {0}").format(self.user),
                        level=0, duration=2)
                    self.refresh_databases()
                    self.refresh_maps()
                    if not version_ok:
                        self._push_message(self.tr("QGIS Cloud"), self.tr(
                            "Unsupported versions detected. Please check your versions first!"), level=1)
                        version_ok = False
                        self.ui.tabWidget.setCurrentWidget(self.ui.aboutTab)
                    login_ok = True
                    self.update_local_layers()

                except ForbiddenError:
                    QMessageBox.critical(
                        self, self.tr("Account Disabled"),
                        self.tr("Account {username} is disabled! Please contact support@qgiscloud.com").format(username=login_dialog.ui.editUser.text()))
                    login_ok = False
                except UnauthorizedError:
                    QMessageBox.critical(
                        self, self.tr("Login for user {username} failed").format(username=login_dialog.ui.editUser.text()),
                        self.tr("Wrong user name or password"))
                    login_ok = False
                except (TokenRequiredError, ConnectionException) as e:
                    QMessageBox.critical(
                        self, self.tr("Login failed"),
                        self.tr("Login failed: %s") % str(e))
                    login_ok = False
        return version_ok

    def create_database(self):
        if self.numDbs < self.maxDBs:
            db = self.api.create_database()
            self.show_api_error(db)
            self.refresh_databases()
        else:
            QMessageBox.warning(None, self.tr('Warning!'),  self.tr('Number of %s permitted databases exceeded! Please upgrade your account!') % self.maxDBs)

    def delete_database(self):
        name = self.ui.tabDatabases.currentItem().text()

        answer = False

        for layer in list(self.PROJECT_INSTANCE.mapLayers().values()):
            if QgsDataSourceUri(layer.publicSource()).database() == name:

                if not answer:
                    answer = QMessageBox.question(
                        self,
                        self.tr("Warning"),
                        self.tr('You have layers from database "{name}" loaded in your project! Do you want to remove them before you delete database "{name}"?').format(name=name),
                        QMessageBox.StandardButtons(
                            QMessageBox.Cancel |
                            QMessageBox.Yes))

                if answer == QMessageBox.Yes:
                     self.PROJECT_INSTANCE.removeMapLayer(layer.id())

        if answer == QMessageBox.Cancel:
            QMessageBox.warning(None,  self.tr('Warning'),  self.tr('Deletion of database "{name}" interrupted!').format(name=name))
            return

        msgBox = QMessageBox()
        msgBox.setWindowTitle(self.tr("Delete QGIS Cloud database."))
        msgBox.setText(
            self.tr("Do you want to delete the database \"%s\"?") % name)
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msgBox.setDefaultButton(QMessageBox.Cancel)
        msgBox.setIcon(QMessageBox.Question)
        ret = msgBox.exec_()

        if ret == QMessageBox.Ok:
            self.setCursor(Qt.WaitCursor)
            result = self.api.delete_database(name)
            self.show_api_error(result)
            self.ui.btnDbDelete.setEnabled(False)
            time.sleep(2)
            self.refresh_databases()
            self.unsetCursor()

    def select_database(self):
        self.ui.btnDbDelete.setEnabled(len(self.ui.tabDatabases.selectedItems()) > 0)

    def select_map(self):
        self.ui.btnMapDelete.setEnabled(len(self.ui.tabMaps.selectedItems()) > 0)
        self.ui.btnMapEdit.setEnabled(len(self.ui.tabMaps.selectedItems()) > 0)
        self.ui.btnMapLoad.setEnabled(len(self.ui.tabMaps.selectedItems()) > 0)
        self.update_urls(map=self.ui.tabMaps.currentItem().text())

    @pyqtSlot()
    def on_btnLogout_clicked(self):
        self.api.reset_auth()
        self.ui.btnLogout.hide()
        self.ui.lblLoginStatus.hide()
        self.ui.btnLogin.show()
        self.ui.widgetServices.hide()
        self.ui.tabDatabases.clear()
        self.ui.tabMaps.clear()
        self.ui.lblDbSize.setText("")
        self.ui.lblDbSizeUpload.setText("")
        self.ui.cbUploadDatabase.clear()
        self.ui.widgetDatabases.setEnabled(False)
        self.activate_upload_button()

    def refresh_databases(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        if self.clouddb:
            db_list = self.api.read_databases()
            if self.show_api_error(db_list):
                QApplication.restoreOverrideCursor()
                return
            self.db_connections = DbConnections()
            for db in db_list:
                self.db_connections.add_from_json(db)

            self.ui.tabDatabases.clear()
            self.ui.btnDbDelete.setEnabled(False)
            self.ui.cbUploadDatabase.clear()
            self.ui.cbUploadDatabase.setEditable(True)
            self.ui.cbUploadDatabase.lineEdit().setReadOnly(True)
            if self.db_connections.count() == 0:
                self.ui.cbUploadDatabase.setEditText(self.tr("No databases"))
            else:
                for name, db in list(self.db_connections.iteritems()):
                    it = QListWidgetItem(name)
                    it.setToolTip(db.description())
                    self.ui.tabDatabases.addItem(it)
                    self.ui.cbUploadDatabase.addItem(name)
                if self.ui.cbUploadDatabase.count() > 1:
                    # Display the "Select database" text if more than one db is available
                    self.ui.cbUploadDatabase.setCurrentIndex(-1)
                    self.ui.cbUploadDatabase.setEditText(self.tr("Select database"))
            self.db_connections.refresh(self.user)

        self.db_size(self.db_connections)
        QApplication.restoreOverrideCursor()

    def map_load(self,  item=None,  row=None):
        self.ui.widgetServices.close()
        self.setCursor(Qt.WaitCursor)
        map_id = self.ui.tabMaps.currentItem().data(Qt.UserRole)
        map_name = self.ui.tabMaps.currentItem().text()
        result = self.api.load_map_project(map_name,  map_id)
        qgs_file_name = '%s/%s.qgs' % (tempfile.gettempdir(), map_name)
        qgs_file = open(qgs_file_name,  'w')
        qgs_file.write(result)
        qgs_file.close()
        project = QgsProject.instance()
        if project.isDirty():
            ok = QMessageBox.information(
                self,
                self.tr("Save Project"),
                self.tr("""Your actual project has changes. Do you want to save the project?"""),
                QMessageBox.StandardButtons(
                    QMessageBox.Abort |
                    QMessageBox.Discard |
                    QMessageBox.Save))
            if ok:
                project.write()

        project.read(qgs_file_name)
        project.setDirty(False)
        self.iface.mainWindow().setWindowTitle("QGIS %s - %s" % (Qgis.QGIS_VERSION,  map_name))
        self.unsetCursor()

    def delete_map(self):
        name = self.ui.tabMaps.currentItem().text()
        map_id = self.ui.tabMaps.currentItem().data(Qt.UserRole)

        msgBox = QMessageBox()
        msgBox.setWindowTitle(self.tr("Delete QGIS Cloud map."))
        msgBox.setText(
            self.tr("Do you want to delete the map \"%s\"?") % name)
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msgBox.setDefaultButton(QMessageBox.Cancel)
        msgBox.setIcon(QMessageBox.Question)
        ret = msgBox.exec_()

        if ret == QMessageBox.Ok:
            self.ui.widgetServices.close()
            self.setCursor(Qt.WaitCursor)
            success = self.api.delete_map(map_id)

            if success:
                self.ui.btnMapDelete.setEnabled(False)
                self.refresh_maps()
            else:
                self.show_api_error(success)

            self.unsetCursor()
            self.ui.widgetServices.close()
        else:
            QMessageBox.warning(None,  self.tr('Warning'),  self.tr('Deletion of map "{name}" interrupted!').format(name=name))

    def edit_map(self):
        map_id = self.ui.tabMaps.currentItem().data(Qt.UserRole)
        plan = self.api.check_login(
            version_info=self._version_info())["plan"]

        mapsettings = MapSettingsDialog(self.api, map_id, self.db_connections,
                                        plan)

        mapsettings.exec_()

    def refresh_maps(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        if self.clouddb:
            map_list = self.api.read_maps()
            if self.show_api_error(map_list):
                QApplication.restoreOverrideCursor()
                return

            self.ui.tabMaps.clear()
            self.ui.btnMapDelete.setEnabled(False)
            self.ui.btnMapEdit.setEnabled(False)
            self.ui.btnMapLoad.setEnabled(False)

            for map in map_list:
                it = QListWidgetItem(map['map']['name'])
                self.ui.tabMaps.addItem(it)
                it.setData(Qt.UserRole,  map['map']['id'])

        QApplication.restoreOverrideCursor()

    def api_url(self):
        return str(self.ui.editServer.text())

    def update_urls(self,  map=None):

        if map == None:
            map = self.map()

        try:
            map = map.decode('utf-8')
        except:
            pass

        self.update_url(self.ui.lblWebmap, self.api_url(),
                        'https://', u'{0}/{1}/'.format(self.user, map))

        if self.clouddb:
            self.update_url(
                self.ui.lblWMS, self.api_url(),
                'https://wms.', u'{0}/{1}/'.format(self.user, map))
        else:
            self.update_url(self.ui.lblWMS, self.api_url(
            ), 'https://', u'{0}/{1}/wms'.format(self.user, map))
        self.update_url(self.ui.lblMaps, self.api_url(), 'https://', 'maps')
        self.ui.widgetServices.show()

    def update_url(self, label, api_url, prefix, path):
        try:
            base_url = string.replace(api_url, 'https://api.', prefix)
        except:
            base_url = api_url.replace('https://api.', prefix)

        url = u'{0}/{1}'.format(base_url, path)
        text = re.sub(r'http[^"]+', url, str(label.text()))
        label.setText(text)

    def read_maps(self):
        if self.check_login():
            self.api.read_maps()

    def check_project_saved(self):
        project = QgsProject.instance()
        fname = project.fileName()
        if project.isDirty() or fname == '':
            msgBox = QMessageBox()
            msgBox.setWindowTitle(self.tr("Project Modified"))
            msgBox.setText(self.tr("The project has been modified."))
            msgBox.setInformativeText(
                self.tr("The project needs to be saved before it can be published. Proceed?"))
            msgBox.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
            msgBox.setDefaultButton(QMessageBox.Save)
            if msgBox.exec_() == QMessageBox.Save:
                self.iface.actionSaveProject().trigger()
                return not project.isDirty()
            else:
                return False
        return True

    def publish_map(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        canvas = self.iface.mapCanvas()
        srs=QgsMapSettings().destinationCrs()

        if "USER" in srs.authid():
            QMessageBox.warning(None, self.tr('Warning!'),  self.tr("The project has a user defined CRS. The use of user defined CRS is not supported. Please correct the project CRS before publishing!"))
            QApplication.restoreOverrideCursor()
            return

        layer_dict = QgsProject.instance().mapLayers()
        layers = list(layer_dict.values())
        layerList = ''

        for layer in layers:
            if "USER" in layer.crs().authid():
                 layerList += "'"+layer.name()+"' "

        if len(layerList) > 0:
            QMessageBox.warning(None, self.tr('Warning!'),  self.tr("The layer(s) {layerlist}have user defined CRS. The use of user defined CRS is not supported. Please correct the CRS before publishing!").format(layerlist=layerList))
            QApplication.restoreOverrideCursor()
            return

        saved = self.check_project_saved()
        if not saved:
            self.statusBar().showMessage(self.tr("Cancelled"))
        elif self.check_login() and self.check_layers():
            self.statusBar().showMessage(self.tr("Publishing map"))
            try:
                fullExtent = self.iface.mapCanvas().fullExtent()
                config = {
                    'fullExtent': {
                        'xmin': fullExtent.xMinimum(),
                        'ymin': fullExtent.yMinimum(),
                        'xmax': fullExtent.xMaximum(),
                        'ymax': fullExtent.yMaximum()
                        #},
                        # 'svgPaths': QgsApplication.svgPaths() #For resolving absolute symbol paths in print composer
                    }
                }
                fname = str(QgsProject.instance().fileName())
                map = self.api.create_map(self.map(), fname, config)['map']
                self.show_api_error(map)
                if map['config']['missingSvgSymbols']:
                    self.publish_symbols(map['config']['missingSvgSymbols'])
                self.update_urls()
                self._push_message(self.tr("QGIS Cloud"), self.tr(
                    "Map successfully published"), level=0, duration=2)
                self.statusBar().showMessage(
                    self.tr("Map successfully published"))
            except Exception as e:
                self.statusBar().showMessage("")
                ErrorReportDialog(self.tr("Error uploading project"), self.tr("An error occured."), str(e) + "\n" + traceback.format_exc(), self.user, self).exec_()
        self.refresh_maps()
        QApplication.restoreOverrideCursor()

    def publish_symbols(self, missingSvgSymbols):
        self.statusBar().showMessage(self.tr("Uploading SVG symbols"))
        search_paths = QgsApplication.svgPaths()
        if hasattr(QgsProject.instance(), 'homePath'):
            search_paths += [QgsProject.instance().homePath()]
        # Search and upload symbol files
        for sym in missingSvgSymbols:
            # Absolute custom path
            if os.path.isfile(sym):
                self.api.create_graphic(sym, sym)
            else:
                for path in search_paths:
                    fullpath = os.path.join(str(path), sym)
                    if os.path.isfile(fullpath):
                        self.api.create_graphic(sym, fullpath)
        self.statusBar().showMessage("")

    def reset_load_data(self):
        self.ui.widgetServices.hide()
        self.update_local_data_sources([],  [])
        self.ui.btnUploadData.setEnabled(False)
        self.ui.tabMaps.clearSelection()

    def remove_layer(self, layer_id):
        if self.do_update_local_data_sources:
            # skip layer if layer will be removed
            self.update_local_layers(layer_id)
            self.activate_upload_button()

    def add_layer(self):
        if self.do_update_local_data_sources:
            self.update_local_layers()
            self.activate_upload_button()

    def update_local_layers(self, skip_layer_id=None):
        local_layers, unsupported_layers,  local_raster_layers = self.local_data_sources.local_layers(skip_layer_id)
        try:
            self.update_local_data_sources(local_layers,  local_raster_layers)
        except Exception as e:
            ErrorReportDialog(self.tr("Error checking local data sources"), self.tr("An error occured."), str(e) + "\n" + traceback.format_exc(), self.user, self).exec_()

        return local_layers, unsupported_layers,  local_raster_layers

    def check_layers(self):
        local_layers, unsupported_layers,  local_raster_layers = self.update_local_layers()


        if ((local_layers or local_raster_layers) and self.clouddb) or unsupported_layers:
            message = ""

            if local_layers or local_raster_layers:
                title = self.tr("Local layers found")
                message += self.tr(
                    "Some layers are using local data. Please upload local layers to your cloud database in the 'Upload Data' tab before publishing.\n\n")

            if unsupported_layers:
                title = self.tr("Unsupported layers found")
                message += self.tr(
                    "Raster, plugin or geometryless layers are not supported:\n\n")
                layer_types = ["No geometry", "Raster", "Plugin"]
                for layer in sorted(unsupported_layers, key=lambda layer: layer.name()):
                    message += self.tr_uni("  -  %s (%s)\n") % (
                        layer.name(), layer_types[layer.type()])
                message += self.tr(
                    "\nPlease remove or replace above layers before publishing your map.\n")
                message += self.tr(
                    "For raster data you can use public WMS layers or the OpenLayers Plugin.")

            QMessageBox.warning(self, title, message)

            self.refresh_databases()
            self.ui.tabWidget.setCurrentWidget(self.ui.uploadTab)
            return False

        return True

    def update_local_data_sources(self, local_layers,  local_raster_layers):
        # update table names lookup
        local_layers += local_raster_layers
        self.update_data_sources_table_names()

        self.local_data_sources.update_local_data_sources(local_layers)

        # update GUI
        self.ui.tblLocalLayers.setRowCount(0)

        for data_source, layers in list(self.local_data_sources.iteritems()):
            layer_names = []
            for layer in layers:
                layer_names.append(str(layer.name()))
            layers_item = QTableWidgetItem(", ".join(layer_names))
            layers_item.setToolTip("\n".join(layer_names))
            data_source_item = QTableWidgetItem(data_source)
            data_source_item.setToolTip(data_source)
            # find a better table name if there are multiple layers with same
            # data source?
            table_name = layers[0].name()
            if data_source in self.data_sources_table_names:
                # use current table name if available to keep changes by user
                table_name = self.data_sources_table_names[data_source]

            table_name_item = QTableWidgetItem(self.launder_pg_name(table_name).decode('utf-8'))

            if layers[0].providerType() == 'gdal':
                geometry_type_item = QTableWidgetItem('Raster')
            else:
                wkbType = layers[0].wkbType()

                if wkbType not in self.GEOMETRY_TYPES:
                    QMessageBox.warning(self.iface.mainWindow(), self.tr("Unsupported geometry type"), self.tr(
                        "Unsupported geometry type '{type}' in layer '{layer}'").format(type=self.__wkbTypeString(wkbType), layer=layers[0].name()))
                    continue
                geometry_type_item = QTableWidgetItem(self.GEOMETRY_TYPES[wkbType])
                if layers[0].providerType() == "ogr":
                    geometry_type_item.setToolTip(
                        self.tr("Note: OGR features will be converted to MULTI-type"))

            srid_item = QTableWidgetItem(layers[0].crs().authid())

            row = self.ui.tblLocalLayers.rowCount()
            self.ui.tblLocalLayers.insertRow(row)
            self.ui.tblLocalLayers.setItem(
                row, self.COLUMN_LAYERS, layers_item)
            self.ui.tblLocalLayers.setItem(
                row, self.COLUMN_DATA_SOURCE, data_source_item)
            self.ui.tblLocalLayers.setItem(
                row, self.COLUMN_TABLE_NAME, table_name_item)
            self.ui.tblLocalLayers.setItem(
                row, self.COLUMN_GEOMETRY_TYPE, geometry_type_item)
            self.ui.tblLocalLayers.setItem(row, self.COLUMN_SRID, srid_item)

        if self.local_data_sources.count() > 0:
            self.ui.tblLocalLayers.resizeColumnsToContents()
            self.ui.tblLocalLayers.setColumnWidth(self.COLUMN_LAYERS, 100)
            self.ui.tblLocalLayers.setColumnWidth(self.COLUMN_DATA_SOURCE, 100)
            self.ui.tblLocalLayers.sortItems(self.COLUMN_DATA_SOURCE)
            self.ui.tblLocalLayers.setSortingEnabled(False)
        else:
            self.ui.btnUploadData.setEnabled(False)

        self.statusBar().showMessage(self.tr("Updated local data sources"))

    def __wkbTypeString(self, wkbType):
        if wkbType == Qgis.WkbUnknown:
            return "WkbUnknown"
        elif wkbType == Qgis.WkbPoint:
            return "WkbPoint"
        elif wkbType == Qgis.WkbLineString:
            return "WkbLineString"
        elif wkbType == Qgis.WkbMultiLineString:
            return "WkbMultiLineString"
        elif wkbType == Qgis.WkbPolygon:
            return "WkbPolygon"
        elif wkbType == Qgis.WkbMultiPoint:
            return "WkbMultiPoint"
        elif wkbType == Qgis.WkbMultiPolygon:
            return "WkbMultiPolygon"
        elif wkbType == Qgis.WkbNoGeometry:
            return "WkbNoGeometry"
        elif wkbType == Qgis.WkbPoint25D:
            return "WkbPoint25D"
        elif wkbType == Qgis.WkbLineString25D:
            return "WkbLineString25D"
        elif wkbType == Qgis.WkbPolygon25D:
            return "WkbPolygon25D"
        elif wkbType == Qgis.WkbMultiPoint25D:
            return "WkbMultiPoint25D"
        elif wkbType == Qgis.WkbMultiLineString25D:
            return "WkbMultiLineString25D"
        elif wkbType == Qgis.WkbMultiPolygon25D:
            return "WkbMultiPolygon25D"
        elif wkbType == QgsWkbTypes.LineStringZM:
            return "WkbLineStringZM"
        elif wkbType == QgsWkbTypes.MultiLineStringZM:
            return "WkbMultiLineStringZM"

        return self.tr("Unknown type")

#    @staticmethod
    def launder_pg_name(self,  name):
        # OGRPGDataSource::LaunderName
        # return re.sub(r"[#'-]", '_', unicode(name).lower())
        input_string = str(name).lower().encode('ascii', 'replace')
        input_string = input_string.replace(b" ",b"_")
        input_string = input_string.replace(b".",b"_")

        # check if table_name starts with number

        if re.search("^\d", input_string.decode('utf-8')):
           input_string = '_'+input_string.decode('utf-8')
           input_string = input_string.decode('utf-8')

        return input_string

    def refresh_local_data_sources(self):
        self.do_update_local_data_sources = True
        self.update_local_layers()
        self.activate_upload_button()
#
    def update_data_sources_table_names(self):
        if self.local_data_sources.count() == 0:
            self.data_sources_table_names.clear()
        else:
            # remove table names without data sources
            keys_to_remove = []
            for key in list(self.data_sources_table_names.keys()):
                if self.local_data_sources.layers(key) is None:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.data_sources_table_names[key]

            # update table names
            for row in range(0, self.ui.tblLocalLayers.rowCount()):
                data_source = str(
                    self.ui.tblLocalLayers.item(row, self.COLUMN_DATA_SOURCE).text())
                table_name = str(
                    self.ui.tblLocalLayers.item(row, self.COLUMN_TABLE_NAME).text())
                self.data_sources_table_names[data_source] = table_name

    def activate_upload_button(self):
        if not self.storage_exceeded:
            self.ui.btnUploadData.setEnabled(self.local_data_sources.count() > 0)
            self.ui.btnPublishMap.setDisabled(self.storage_exceeded)
        else:
            self.ui.btnUploadData.setDisabled(self.storage_exceeded)
            self.ui.btnPublishMap.setDisabled(self.storage_exceeded)

    def upload_data(self):
        if self.check_login():
            if self.local_data_sources.count() == 0:
                return

            if self.db_connections.count() == 0:
                QMessageBox.warning(self, self.tr("No database available"), self.tr("Please create a database in the 'Account' tab."))
                return

            if not self.ui.cbUploadDatabase.currentIndex() >= 0:
                QMessageBox.warning(self, self.tr("No database selected"), self.tr("Please select a database to upload data."))
                return

            db_name = self.ui.cbUploadDatabase.currentText()

            if not self.db_connections.isPortOpen(db_name):
                uri = self.db_connections.cloud_layer_uri(db_name, "", "")
                host = str(uri.host())
                port = uri.port()
                QMessageBox.critical(self, self.tr("Network Error"),
                                     self.tr("Could not connect to database server ({0}) on port {1}. Please contact your system administrator or internet provider to open port {1} in the firewall".format(host, port)))
                return

            # disable update of local data sources during upload, as there are
            # temporary layers added and removed
            self.do_update_local_data_sources = False
            self.statusBar().showMessage(self.tr("Uploading data..."))
            self.setCursor(Qt.WaitCursor)
            self.ui.btnUploadData.hide()
            self.ui.spinner.start()
            self.ui.progressWidget.show()

            # Map<data_source, {table: table, layers: layers}>
            data_sources_items = {}
            for row in range(0, self.ui.tblLocalLayers.rowCount()):
                data_source = unicode(
                    self.ui.tblLocalLayers.item(
                        row, self.COLUMN_DATA_SOURCE).text())
                layers = self.local_data_sources.layers(data_source)
                if layers is not None:
                    table_name = unicode(
                        self.ui.tblLocalLayers.item(
                            row, self.COLUMN_TABLE_NAME).text())
                    data_sources_items[data_source] = {
                        u'table': unicode(table_name), u'layers': layers}

            login_info = self.api.check_login(version_info=self._version_info())
            try:
                self.maxSize = login_info['max_storage']
                self.maxDBs = login_info['max_dbs']
            except:
                self.maxSize = 50
                self.maxDBs = 5

            try:
                self.data_upload.upload(self.db_connections.db(unicode(db_name)), data_sources_items, unicode(self.maxSize))
                upload_ok = True
            except Exception as e:
                ErrorReportDialog(self.tr("Upload errors occurred"), self.tr("Upload errors occurred. Not all data could be uploaded."), str(e) + "\n" + traceback.format_exc(), self.user, self).exec_()
                upload_ok = False

            self.ui.spinner.stop()
            self.ui.progressWidget.hide()
            self.ui.btnUploadData.show()
            self.unsetCursor()
            self.statusBar().showMessage("")
            # Refresh local layers
            self.do_update_local_data_sources = True
            self.update_local_layers()
            # Refresh used space after upload
            self.db_size(self.db_connections)

            if upload_ok:
                # Show save project dialog
                save_dialog = QDialog(self)
                save_dialog.setWindowTitle(self.tr("Save Project"))
                save_dialog.setLayout(QVBoxLayout())
                header = QWidget()
                header.setLayout(QVBoxLayout())
                label = QLabel(self.tr("Upload complete. The local layers in the project were replaced with the layers uploaded to the qgiscloud database."))
                label.setWordWrap(True)
                header.layout().addWidget(label)
                label = QLabel(self.tr("Choose were to save the modified project:"))
                label.setWordWrap(True)
                header.layout().addWidget(label)
                save_dialog.layout().setContentsMargins(0, 0, 0, 0)
                save_dialog.layout().addWidget(header)
                initialPath = QgsProject.instance().fileName()
                if not initialPath:
                    initialPath = QSettings().value("/UI/lastProjectDir", ".")
                fd = QFileDialog(None, self.tr("Save Project"), initialPath, "%s (*.qgs)" % self.tr("QGIS Project Files"))
                fd.setParent(save_dialog, Qt.Widget)
                fd.setOption(QFileDialog.DontUseNativeDialog)
                fd.setAcceptMode(QFileDialog.AcceptSave)
                save_dialog.layout().addWidget(fd)
                header.layout().setContentsMargins(fd.layout().contentsMargins())
                fd.accepted.connect(save_dialog.accept)
                fd.rejected.connect(save_dialog.reject)
                if save_dialog.exec_() == QDialog.Accepted:
                    files = list(fd.selectedFiles())
                    if files:
                        QgsProject.instance().setFileName(files[0])
                        self.iface.actionSaveProject().trigger()

                # Switch to map tab
                self.ui.tabWidget.setCurrentWidget(self.ui.mapTab)

    def _push_message(self, title, text, level=0, duration=0):
        # QGIS >= 2.0
        if hasattr(self.iface, 'messageBar') and hasattr(self.iface.messageBar(), 'pushMessage'):
            self.iface.messageBar().pushMessage(title, text, level, duration)
        else:
            QMessageBox.information(self, title, text)

    def show_api_error(self, result):
        if 'error' in result:
            QMessageBox.critical(
                self, self.tr("QGIS Cloud Error"), "%s" % result['error'])
            self.statusBar().showMessage(self.tr("Error"))
            return True
        else:
            return False

    def tr_uni(self, str):
        return str(self.tr(str))

    def db_size(self,  db_connections):
        usedSpace = 0
        self.numDbs = len(list(db_connections._dbs.keys()))
        for db in list(db_connections._dbs.keys()):
            try:
                conn = db_connections.db(db).psycopg_connection()
            except:
                continue
            cursor = conn.cursor()
            sql = "SELECT pg_database_size('" + str(db) + "')"
            cursor.execute(sql)
            usedSpace += int(cursor.fetchone()[0])-(11*1024*1024)
            cursor.close()
            conn.close

        # Used space in MB
        usedSpace /= 1024 * 1024

        login_info = self.api.check_login(version_info=self._version_info())

        try:
            self.maxSize = login_info['max_storage']
            self.maxDBs = login_info['max_dbs']
        except:
            self.maxSize = 50
            self.maxDBs = 5

        lblPalette = QPalette(self.ui.lblDbSize.palette())
        usage = usedSpace / float(self.maxSize)
        self.storage_exceeded = False

        if usage < 0.8:
            bg_color = QColor(255, 0, 0, 0)
            text_color = QColor(Qt.black)
        elif usage >= 0.8 and usage < 1:
            bg_color = QColor(255, 0, 0, 100)
            text_color = QColor(Qt.white)
        elif usage >= 1:
            bg_color = QColor(255, 0, 0, 255)
            text_color = QColor(Qt.white)
            self.storage_exceeded = True

        lblPalette.setColor(QPalette.Window, QColor(bg_color))
        lblPalette.setColor(QPalette.Foreground,QColor(text_color))

        self.ui.lblDbSize.setAutoFillBackground(True)
        self.ui.lblDbSize.setPalette(lblPalette)
        self.ui.lblDbSize.setText(
            self.tr("Used DB Storage: ") + "%d / %d MB" % (usedSpace, self.maxSize))

        self.ui.lblDbSizeUpload.setAutoFillBackground(True)
        self.ui.lblDbSizeUpload.setPalette(lblPalette)
        self.ui.lblDbSizeUpload.setText(
            self.tr("Used DB Storage: ") + "%d / %d MB" % (usedSpace, self.maxSize))
        self.ui.btnUploadData.setDisabled(self.storage_exceeded)
        self.ui.btnPublishMap.setDisabled(self.storage_exceeded)

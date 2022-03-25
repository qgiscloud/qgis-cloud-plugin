# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MapSettingsDialog
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
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.gui import QgsCodeEditorSQL
from qgis.PyQt import uic

import re
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'mapsettings.ui'))


class MapSettingsDialog(QDialog, FORM_CLASS):

    def __init__(self, api, map_id, map_name,  db_connections, plan):
        """
        This is the contructor of the MapSettingsDialog class.
        """
        QDialog.__init__(self)
        self.setupUi(self)
        self.api = api
        self.map_id = map_id
        self.setWindowTitle(self.tr("Map settings for map: %s") % map_name)
        self.db_connections = db_connections
        self.plan = plan
        # get map settings
        self.map_settings = self.api.read_map(map_id)
        # get all map options
        self.map_options = self.api.read_map_options()

    def prepare_ui(self):
        QGuiApplication.setOverrideCursor(Qt.WaitCursor)
        self.set_checkboxes()
        self.set_combobox_options()
        self.set_scales()
        self.set_search_type()
        self.enable_user_management()
        self.fill_users_listWidget()
        self.set_icons()

        self.viewer_active_chkb.stateChanged.connect(
            self.enable_user_management)
        self.wms_public_chkb.stateChanged.connect(
            self.enable_user_management)
        self.map_public_chkb.stateChanged.connect(
            self.enable_user_management)
        self.search_type_combobox.currentIndexChanged.connect(
            self.enable_DBsearch)
        self.sql_preview_btn.clicked.connect(self.validate_sql_query)
        self.add_users_btn.clicked.connect(
            lambda: self.add_user())
        self.delete_user_btn.clicked.connect(self.delete_user)
        self.dialog_buttonBox.button(
            QDialogButtonBox.Save).clicked.connect(self.save_options)

        self.toggle_disabled_fields()

        QGuiApplication.restoreOverrideCursor()

    def set_checkboxes(self):
        """
        This method sets the checkboxes to their right state.
        """
        self.viewer_active_chkb.setChecked(
            self.map_settings["map"]["viewer_active"])
        self.wms_public_chkb.setChecked(
            self.map_settings["map"]["wms_public"])
        self.map_public_chkb.setChecked(
            self.map_settings["map"]["map_public"])

    def set_combobox_options(self):
        """
        This method filles all comboboxes with the available options and
        selects the right option
        """
        # get all databases owned by the user
        user_databases = self.api.read_databases()
        # get viewer information
        viewers = self.api.read_viewers()
        # fill comboboxes and choose the right option
        viewer_id = self.map_settings["map"]["viewer_id"]
        for view in viewers:
            self.viewer_combobox.addItem(view["viewer"]["name"])
            if viewer_id == view["viewer"]["id"]:
                self.viewer_combobox.setCurrentIndex(
                    self.viewer_combobox.findText(view["viewer"]["name"]))

        search_db_name = self.map_settings["map"]["search_db"]
        for db in user_databases:
            self.search_db_combobox.addItem(db["name"])
            if db["name"] == search_db_name:
                self.search_db_combobox.setCurrentIndex(
                    self.search_db_combobox.findText(db["name"]))

        language = self.map_settings["map"]["lang"]
        for locale in self.map_options["locales"]:
            self.language_combobox.addItem(locale)
            self.language_combobox.setCurrentIndex(
                self.language_combobox.findText(language))

    def set_scales(self):
        """
        This method sets the scales.
        """
        # get scales
        scales = self.map_settings["map"]["scales"]
        self.scales_lineedit.setText(",".join(scales))

    def set_icons(self):
        add_icon = QIcon(":images/themes/default/mActionAdd.svg")
        delete_icon = QIcon(":images/themes/default/symbologyRemove.svg")
        preview_icon = QIcon(":images/themes/default/mActionShowAllLayers.svg")

        self.add_users_btn.setIcon(add_icon)
        self.delete_user_btn.setIcon(delete_icon)
        self.sql_preview_btn.setIcon(preview_icon)

    def get_viewer_id(self, viewer_name):
        """
        This method is needed to save the selected viewer. It returns the
        viewerid of the selected viewer.
        """
        viewers = self.api.read_viewers()
        viewer_id = None
        for view in viewers:
            if viewer_name == view["viewer"]["name"]:
                viewer_id = view["viewer"]["id"]

        return viewer_id

    def set_search_type(self):
        """
        This method selects the right search option in the listwidget.
        """
        self.search_type_combobox.addItems(
            self.map_options["search_types"])

        self.search_type_combobox.setCurrentIndex(
            self.search_type_combobox.findText(
                self.map_settings["map"]["search_type"]))

    def enable_DBsearch(self):
        """
        This method disables UI elements, based on the search type selection.
        """
        if self.search_type_combobox.currentText() == "DBSearch":
            self.set_sql_query()
            self.search_db_combobox.setEnabled(True)
            self.search_sql_textedit.setEnabled(True)
            self.sql_preview_btn.setEnabled(True)
        else:
            self.search_db_combobox.setEnabled(False)
            self.search_sql_textedit.setEnabled(False)
            self.sql_preview_btn.setEnabled(False)

    def set_sql_query(self):
        """
        This metohd sets the rights sql query in the textedit
        """
        if self.map_settings["map"]["search_sql"]:
            self.search_sql_textedit.setText(
                self.map_settings["map"]["search_sql"])

    def validate_sql_query(self):
        """
        This method validates the sql and enables the preview button for
        the user
        """
        # get db object
        db_name = self.search_db_combobox.currentText()
        db = self.db_connections.db(db_name)
        # create db connection
        conn = db.psycopg_connection()
        cursor = conn.cursor()
        sql_results = False

        # split sql query and execute it
        sql_query = self.search_sql_textedit.text()
        try:
            cursor.execute(
                re.split("where", sql_query, flags=re.IGNORECASE)[0])
            sql_results = cursor.fetchall()
        except Exception as e:
            msg = e.args

        if sql_results:
            self.create_sql_preview(sql_results)
        else:
            QMessageBox.warning(
                self,
                self.tr("Sql Error"),
                self.tr(msg[0]))

    def create_sql_preview(self, sql_results):
        """
        This method open a new Dialog, where the sql query is executed and if
        the query is valid, a preview of the result is shown.
        """
        preview_dialog = QDialog(self)
        gridLayout = QGridLayout(preview_dialog)
        sql_preview_view = QTableView(preview_dialog)
        gridLayout.addWidget(sql_preview_view)
        preview_dialog.setLayout(gridLayout)

        # add all valid results to model
        data = []
        header = ["displaytext", "bbox"]
        for result in sql_results:
            if result[0] and result[1]:
                data.append([result[0], result[1]])
            else:
                continue
        model = TableModel(data, header)
        # set model tableview
        sql_preview_view.setModel(model)
        # set size of row
        sql_preview_view.resizeColumnsToContents()
        preview_dialog.resize(1000, 600)
        preview_dialog.exec_()

    def enable_user_management(self):
        if self.viewer_active_chkb.isChecked() \
            or(not self.wms_public_chkb.isChecked()
                and not self.map_public_chkb.isChecked()):
            self.users_listWidget.setEnabled(True)
            self.add_users_btn.setEnabled(True)
            self.delete_user_btn.setEnabled(True)
        else:
            self.users_listWidget.setEnabled(False)
            self.add_users_btn.setEnabled(False)
            self.delete_user_btn.setEnabled(False)

    def add_user(self, username=""):
        """
        This method trys to add a new user and if the user exists then it adds
        him to the user list, but if he doesn't exist, an error message is
        shown.
        """

        # String object
        users_list, ok = QInputDialog.getText(
            self, self.tr("Add user(s)"),
            self.tr("Usernames:"), QLineEdit.Normal, username)

        if ok is False:
            return

        QGuiApplication.setOverrideCursor(Qt.WaitCursor)
        map_settings = self.api.read_map(self.map_id)
        # current user list
        current_user_list = []
        # list with the users that will be added
        users_to_add = re.sub(
            r"\s+", "", users_list).split(",")
        # list for users that don't exist
        nonexistent_users = []
        # create list of all users
        for old_user in map_settings["map"]["users"]:
            current_user_list.append(old_user)

        new_user_list = ",".join(current_user_list + users_to_add)

        updated_user_list = self.api.update_map(
            self.map_id, {"map[users]": new_user_list})

        for user in users_to_add:
            if user not in updated_user_list["map"]["users"]:
                nonexistent_users.append(user)

        if users_list \
                and users_list.isspace() is False:
            if nonexistent_users:
                QGuiApplication.restoreOverrideCursor()
                QMessageBox.warning(
                    self,
                    self.tr("User error"),
                    self.tr("The user(s): %s don't exist.") %
                    (", ".join(nonexistent_users)))
                self.add_user(", ".join(nonexistent_users))
            else:
                QGuiApplication.restoreOverrideCursor()
                QMessageBox.information(
                    self,
                    self.tr("Success"),
                    self.tr("The user(s): %s have been added.") % (
                        ", ".join(users_to_add)))
                self.fill_users_listWidget()
        else:
            QGuiApplication.restoreOverrideCursor()
            QMessageBox.warning(
                self,
                self.tr("Error"),
                self.tr("No username given."))
            self.add_user()

    def delete_user(self):
        """
        This metohd removes a user. If the user isn't in the list of the users,
        then an error message is shown.
        """
        # String object
        QGuiApplication.setOverrideCursor(Qt.WaitCursor)
        map_settings = self.api.read_map(self.map_id)

        users_to_delete = [self.users_listWidget.currentItem().text()]
        current_user_list = []
        new_user_list = []
        deleted_users = []
        # create list of all users
        for user in map_settings["map"]["users"]:
            current_user_list.append(user)
        # create list of all users without the user that's going to be deleted
        for user in current_user_list:
            if user in users_to_delete:
                continue
            else:
                new_user_list.append(user)

        QGuiApplication.restoreOverrideCursor()
        res = QMessageBox.information(
            self,
            self.tr(""),
            self.tr("Do you really want to delete the user: %s?") %
            (", ".join(users_to_delete)), QMessageBox.Yes | QMessageBox.No)

        if res == QMessageBox.No:
            return

        QGuiApplication.setOverrideCursor(Qt.WaitCursor)
        updated_user_list = self.api.update_map(
            self.map_id, {"map[users]": ",".join(new_user_list)})

        for deleted_user in users_to_delete:
            if deleted_user not in updated_user_list:
                deleted_users.append(deleted_user)

        QGuiApplication.restoreOverrideCursor()
        QMessageBox.information(
            self,
            self.tr("Success"),
            self.tr("The user: %s has been deleted.") %
            (", ".join(deleted_users)))
        self.fill_users_listWidget()

    def fill_users_listWidget(self):
        """
        This method opens a new dialog. The dialog shows all maps and their own
        user lists.
        """
        self.users_listWidget.clear()
        # Add all valid results to model
        allowed_users = self.api.read_map(self.map_id)["map"]["users"]
        if allowed_users:
            for user in allowed_users:
                self.users_listWidget.addItem(user)

    def save_options(self):
        """
        This method saves all options that the user changed. It uses the
        REST API to make the PUT request.
        """
        QGuiApplication.setOverrideCursor(Qt.WaitCursor)
        data = {}
        map_settings = self.api.read_map(self.map_id)

        if self.viewer_active_chkb.isChecked():
            data["map[viewer_active]"] = 1
        else:
            data["map[viewer_active]"] = 0
        if self.wms_public_chkb.isChecked():
            data["map[wms_public]"] = 1
        else:
            data["map[wms_public]"] = 0
        if self.map_public_chkb.isChecked():
            data["map[map_public]"] = 1
        else:
            data["map[map_public]"] = 0

        viewer_name = self.viewer_combobox.currentText()
        if viewer_name:
            data["map[viewer_id]"] = self.get_viewer_id(viewer_name)
        data["map[lang]"] = self.language_combobox.currentText()
        data["map[scales]"] = ",".join(list(filter(
            str.isdigit, (self.scales_lineedit.text().split(",")))))
        data["map[search_db]"] = self.search_db_combobox.currentText()
        data["map[search_type"] = self.search_type_combobox.currentText()
        if self.search_sql_textedit.isEnabled():
            data["map[search_sql]"] = self.search_sql_textedit.text()

        self.api.update_map(self.map_id, data)

        # add userlist to settings
        QGuiApplication.restoreOverrideCursor()

    def toggle_disabled_fields(self):
        # general settings
        self.toggle_field('viewer_active', [self.viewer_active_lbl, self.viewer_active_chkb])
        self.toggle_field('wms_public', [self.wms_public_lbl, self.wms_public_chkb])
        self.toggle_field('map_public', [self.map_public_lbl, self.map_public_chkb])
        self.toggle_field('lang', [self.language_lbl, self.language_combobox])
        self.toggle_field('scales', [self.scales_lbl, self.scales_lineedit])
        self.toggle_field('viewer_id', [self.viewer_lbl, self.viewer_combobox])

        # search settings
        enabled_fields = self.map_options.get('enabled_fields', [])
        hide_disabled_fields = self.map_options.get('hide_disabled_fields', False)
        search_enabled = len(
            set(['search_type', 'search_db', 'search_sql']) & set(enabled_fields)
        ) > 0
        self.sql_editor_box.setEnabled(search_enabled)
        self.sql_editor_box.setVisible(search_enabled or not hide_disabled_fields)

        self.toggle_field('search_type', [self.search_type_lbl, self.search_type_combobox])
        self.toggle_field('search_db', [self.search_db_lbl, self.search_db_combobox])
        self.toggle_field('search_sql', [
            self.search_sql_lbl, self.search_sql_textedit, self.sql_preview_btn, self.label, self.label_2
        ])

        # allowed users
        self.toggle_field('users', [self.user_management])

        # resize dialog window
        self.adjustSize()
        if self.width() < 500:
            self.resize(500, self.height())

    def toggle_field(self, field, widgets):
        """Helper for toggling widgets of a form field."""
        enabled_fields = self.map_options.get('enabled_fields', [])
        hide_disabled_fields = self.map_options.get('hide_disabled_fields', False)
        enabled = field in enabled_fields
        for widget in widgets:
            widget.setEnabled(enabled)
            widget.setVisible(enabled or not hide_disabled_fields)


class TableModel(QAbstractTableModel):
    """
    TableModel for all dialogs that use a TableView.
    """
    def __init__(self, data, header):
        QAbstractTableModel.__init__(self)
        self.data = data
        self.header = header

    def rowCount(self, index):
        return len(self.data)

    def columnCount(self, index):
        return 2

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        return QVariant(self.data[index.row()][index.column()])

    def headerData(self, row, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[row]
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return row
        return None

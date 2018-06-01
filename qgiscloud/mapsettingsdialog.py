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

from .mapsettingsUI.ui_mapsettings import Ui_map_settings
from .mapsettingsUI.ui_generatescales import Ui_generate_scales
from .mapsettingsUI.ui_sqlpreview import Ui_sql_preview
from .mapsettingsUI.ui_showusers import Ui_show_users

import re


class MapSettingsDialog(QDialog):

    def __init__(self, api, map_id, db_connections, plan):
        """
        This is the contructor of the MapSettingsDialog. When calling this
        class, this method is executed automatically. This method creates all
        class variables and handles the diffrent account plans.
        """
        QDialog.__init__(self)
        QGuiApplication.setOverrideCursor(Qt.WaitCursor)
        self.ui = Ui_map_settings()
        self.ui.setupUi(self)
        self.api = api
        self.map_id = map_id
        self.db_connections = db_connections
        # get map settings
        self.map_settings = self.api.read_map(map_id)
        # get all map options
        self.all_map_options = self.api.read_map_options()
        # add userlist to settings
        QSettings().setValue("qgiscloud/%s/userlist" %
                             self.map_settings["map"]["name"],
                             ", ".join(self.map_settings["map"]["users"]))

        # set values of ui elements
        self.set_checkboxes()
        self.set_combobox_options()
        self.set_scales()
        self.set_search_type()

        # set connections
        self.ui.generate_scales_btn.clicked.connect(self.generate_scales)
        self.ui.search_type_list.itemSelectionChanged.connect(
            self.enable_DBsearch)
        self.ui.sql_preview_btn.clicked.connect(self.validate_sql_query)
        self.ui.add_users_btn.clicked.connect(self.add_user)
        self.ui.delete_user_btn.clicked.connect(self.delete_user)
        self.ui.show_userlist_btn.clicked.connect(self.show_user_list)
        self.ui.save_settings_btn.button(
            QDialogButtonBox.Apply).clicked.connect(self.save_options)

        self.check_plan(plan)

        QGuiApplication.restoreOverrideCursor()

    def set_checkboxes(self):
        """
        This method sets the checkboxes to their right state.
        """
        self.ui.viewer_active_chkb.setChecked(
            self.map_settings["map"]["viewer_active"])
        self.ui.wms_public_chkb.setChecked(
            self.map_settings["map"]["wms_public"])
        self.ui.map_public_chkb.setChecked(
            self.map_settings["map"]["map_public"])

    def set_combobox_options(self):
        """
        This method filles all comboboxes with the available options and
        selects the right option
        """
        # get all databases
        all_dbs = self.api.read_databases()
        # get viewer information
        all_viewers = self.api.read_viewers()
        # fill comboboxes and choose the right option
        viewer_id = self.map_settings["map"]["viewer_id"]
        for view in all_viewers:
            self.ui.viewer_combobox.addItem(view["viewer"]["name"])
            if viewer_id == view["viewer"]["id"]:
                self.ui.viewer_combobox.setCurrentText(view["viewer"]["name"])

        db_name = self.map_settings["map"]["search_db"]
        for db in all_dbs:
            self.ui.search_db_combobox.addItem(db["name"])
            if db["name"] == db_name:
                self.ui.search_db_combobox.setCurrentText(db["name"])

        language = self.map_settings["map"]["lang"]
        for lang in self.all_map_options["locales"]:
            self.ui.language_combobox.addItem(lang)
            self.ui.language_combobox.setCurrentText(language)

    def set_scales(self):
        """
        This method sets the scales.
        """
        # get scales
        scales = self.map_settings["map"]["scales"]
        self.ui.scales_lineedit.setText(",".join(scales))

    def generate_scales(self):
        """
        This method opens a new Dialog, where the user can generate scales. The
        scales will then be added to the scales lineedit.
        """
        scaleDialog = QDialog(self)
        scaleDialog.ui = Ui_generate_scales()
        scaleDialog.ui.setupUi(scaleDialog)
        generate = scaleDialog.exec_()
        all_scales = self.ui.scales_lineedit.text().split(",")

        minscale = scaleDialog.ui.min_lineedit.text()
        maxscale = scaleDialog.ui.max_lineedit.text()
        steps = scaleDialog.ui.steps_lineedit.text()
        # if the user presses ok
        if generate == 1:
            # generate the scales
            gen_scales = [minscale]
            try:
                # check scales
                if not minscale or not maxscale or not steps:
                    QMessageBox.warning(
                        self,
                        self.tr("Error"),
                        self.tr("Please fill everything out."))
                    return
                elif int(minscale) < 0 or int(maxscale) < 0 or int(steps) < 0:
                    QMessageBox.warning(
                        self,
                        self.tr("Error"),
                        self.tr("No negativ numbers allowed."))
                    return
                elif int(minscale) > int(maxscale):
                    QMessageBox.warning(
                        self,
                        self.tr("Error"),
                        self.tr("The minimum scale mustn't be bigger than the "
                                "maximum scale."))
                    return
                else:
                    while int(gen_scales[-1]) < int(maxscale):
                        if int(gen_scales[-1]) + int(steps) > int(maxscale):
                            break
                        else:
                            gen_scales.append(str(int(
                                gen_scales[-1]) + int(steps)))
            except ValueError:
                QMessageBox.warning(
                    self,
                    self.tr("Error"),
                    self.tr(
                        "A character was found!\nPlease use numbers only."))
                return
            if self.ui.scales_lineedit.text():
                self.ui.scales_lineedit.setText(",".join(sorted(set(
                    all_scales + gen_scales), key=int)))
            else:
                self.ui.scales_lineedit.setText(",".join(gen_scales))
        else:
            pass

    def get_viewer_id(self, viewer_name):
        """
        This method is needed to save the selected viewer. It returns the
        viewerid of the selected viewer.
        """
        all_viewers = self.api.read_viewers()
        for view in all_viewers:
            if viewer_name == view["viewer"]["name"]:
                return view["viewer"]["id"]
            else:
                continue

    def set_search_type(self):
        """
        This method selects the right search option in the listwidget.
        """
        for search_typ in self.all_map_options["search_types"]:
            self.ui.search_type_list.addItem(search_typ)
        listItem = self.ui.search_type_list.findItems(
            self.map_settings["map"]["search_type"], Qt.MatchFixedString)[0]
        self.ui.search_type_list.setCurrentItem(listItem)

    def enable_DBsearch(self):
        """
        This method disables UI elements, based on the search type selection.
        """
        self.set_sql_query()
        if self.ui.search_type_list.currentItem().text() == "DBSearch":
            self.ui.search_db_combobox.setVisible(True)
            self.ui.search_sql_textedit.setVisible(True)
            self.ui.sql_preview_btn.setVisible(True)
            # labels
            self.ui.search_db_lbl.setVisible(True)
            self.ui.search_sql_lbl.setVisible(True)
        else:
            self.ui.search_db_combobox.setVisible(False)
            self.ui.search_sql_textedit.setVisible(False)
            self.ui.sql_preview_btn.setVisible(False)
            # labels
            self.ui.search_db_lbl.setVisible(False)
            self.ui.search_sql_lbl.setVisible(False)

    def set_sql_query(self):
        """
        This metohd sets the rights sql query in the textedit
        """
        if self.map_settings["map"]["search_sql"]:
            self.ui.search_sql_textedit.setText(
                self.map_settings["map"]["search_sql"])

    def validate_sql_query(self):
        """
        This method validates the sql and enables the preview button for
        the user
        """
        # get db object
        db_name = self.ui.search_db_combobox.currentText()
        db = self.db_connections.db(unicode(db_name))
        # create db connection
        conn = db.psycopg_connection()
        cursor = conn.cursor()
        sql_results = False

        # split sql query and execute it
        sql_query = self.ui.search_sql_textedit.text()
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
        preview_dialog.ui = Ui_sql_preview()
        preview_dialog.ui.setupUi(preview_dialog)

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
        preview_dialog.ui.sql_preview_view.setModel(model)
        # set size of row
        preview_dialog.ui.sql_preview_view.resizeColumnsToContents()

        preview_dialog.exec_()

    def add_user(self):
        """
        This method trys to add a new user and if the user exists then it adds
        him to the user list, but if he doesn't exist, an error message is
        shown.
        The class variable self.map_settings can't be used here because this
        function relys on the newest version of the users in the map settings.
        Thats why we need to make a request to get the newest map settings
        everytime a user is added.
        """
        QGuiApplication.setOverrideCursor(Qt.WaitCursor)
        map_settings = self.api.read_map(self.map_id)
        # current user list
        old_user_list = []
        # list with the users that will be added
        users_to_add = re.sub(
            r"\s+", "", self.ui.users_lineedit.text()).split(",")
        # list for users that don't exist
        nonexistent_users = []
        # create list of all users
        for old_user in map_settings["map"]["users"]:
            old_user_list.append(old_user)

        new_user_list = ",".join(old_user_list + users_to_add)

        updated_user_list = self.api.update_map(
            self.map_id, {"map[users]": new_user_list})

        for user in users_to_add:
            if user not in updated_user_list["map"]["users"]:
                nonexistent_users.append(user)

        if self.ui.users_lineedit.text() and self.ui.users_lineedit.text().isspace() is False:
            if nonexistent_users:
                QGuiApplication.restoreOverrideCursor()
                QMessageBox.warning(
                    self,
                    self.tr("User error"),
                    self.tr("The users: %s don't exist.") %
                    (", ".join(nonexistent_users)))
                self.ui.users_lineedit.selectAll()
            else:
                QGuiApplication.restoreOverrideCursor()
                QMessageBox.information(
                    self,
                    self.tr("Success"),
                    self.tr("The users: %s have been added.") % (
                        ", ".join(users_to_add)))
                self.ui.users_lineedit.clear()
        else:
            QGuiApplication.restoreOverrideCursor()
            QMessageBox.warning(
                self,
                self.tr("Error"),
                self.tr("Can't add user, because there was no username given."))

    def delete_user(self):
        """
        This metohd removes a user. If the user isn't in the list of the users,
        then an error message is shown.
        """
        QGuiApplication.setOverrideCursor(Qt.WaitCursor)
        map_settings = self.api.read_map(self.map_id)
        users_to_delete = re.sub(
            r"\s+", "", self.ui.users_lineedit.text()).split(",")
        old_user_list = []
        new_user_list = []
        deleted_users = []
        # create list of all users
        for user in map_settings["map"]["users"]:
            old_user_list.append(user)
        # create list of all users without the user that's going to be deleted
        for user in old_user_list:
            if user in users_to_delete:
                continue
            else:
                new_user_list.append(user)

        QGuiApplication.restoreOverrideCursor()
        res = QMessageBox.information(
            self,
            self.tr(""),
            self.tr("Do you really want to delete the user %s?") %
            (", ".join(users_to_delete)), QMessageBox.Yes | QMessageBox.No)

        if res == QMessageBox.No:
            return
        QGuiApplication.setOverrideCursor(Qt.WaitCursor)
        updated_user_list = self.api.update_map(
            self.map_id, {"map[users]": ",".join(new_user_list)})

        for del_user in users_to_delete:
            if del_user not in updated_user_list:
                deleted_users.append(del_user)
        # check if the user was deleted
        if self.ui.users_lineedit.text() and self.ui.users_lineedit.text().isspace() is False:
            QGuiApplication.restoreOverrideCursor()
            QMessageBox.information(
                self,
                self.tr("Success"),
                self.tr("The users: %s has been deleted.") %
                (", ".join(deleted_users)))
            self.ui.users_lineedit.clear()
            self.ui.users_lineedit.selectAll()
        else:
            QGuiApplication.restoreOverrideCursor()
            QMessageBox.warning(
                self,
                self.tr("Error"),
                self.tr(
                    "Can't delete user, because there was no username given."))

    def show_user_list(self):
        """
        This method opens a new dialog. The dialog shows all maps and their own
        user lists.
        """
        show_user_dialog = QDialog(self)
        show_user_dialog.ui = Ui_show_users()
        show_user_dialog.ui.setupUi(show_user_dialog)

        # add all valid results to model
        data = []
        header = [self.tr("Map"), self.tr("allowed users")]

        all_maps = self.api.read_maps()
        for map in all_maps:
            data.append([map["map"]["name"], ",".join(map["map"]["users"])])

        model = TableModel(data, header)
        # set model tableview
        show_user_dialog.ui.users_listview.setModel(model)
        # set size of row
        show_user_dialog.ui.users_listview.resizeColumnsToContents()
        # add connection to exit button
        show_user_dialog.ui.copy_users.clicked.connect(
            lambda: self.copy_users(show_user_dialog.ui))

        show_user_dialog.exec_()

    def copy_users(self, view):
        if len(view.users_listview.selectedIndexes()) == 1:
            selected_index = view.users_listview.selectedIndexes()
            column = selected_index[0].column()
            row = selected_index[0].row()
            if column == 1:
                # copy user list when user selects user list
                user_list = selected_index[0].data(Qt.DisplayRole)
                QGuiApplication.clipboard().setText(user_list,
                                                    mode=QClipboard.Clipboard)
            else:
                # copy user list when user selects map name
                user_list = selected_index[0].sibling(row, 1).data(
                    Qt.DisplayRole)
                QGuiApplication.clipboard().setText(user_list,
                                                    mode=QClipboard.Clipboard)
            QMessageBox.information(
                self,
                self.tr("Success"),
                self.tr("The user list has been copied."))
        elif len(view.users_listview.selectedIndexes()) > 1:
            QMessageBox.warning(
                self,
                self.tr("Error"),
                self.tr("Please select only one user list."))
        elif len(view.users_listview.selectedIndexes()) == 0:
            QMessageBox.warning(
                self,
                self.tr("Error"),
                self.tr("No user list selected."))

    def save_options(self):
        """
        This method saves all options that the user changed. It uses the
        REST API to make the PUT request.
        """
        QGuiApplication.setOverrideCursor(Qt.WaitCursor)
        data = {}
        map_settings = self.api.read_map(self.map_id)

        if self.ui.viewer_active_chkb.isChecked():
            data["map[viewer_active]"] = 1
        else:
            data["map[viewer_active]"] = 0
        if self.ui.wms_public_chkb.isChecked():
            data["map[wms_public]"] = 1
        else:
            data["map[wms_public]"] = 0
        if self.ui.map_public_chkb.isChecked():
            data["map[map_public]"] = 1
        else:
            data["map[map_public]"] = 0

        viewer_name = self.ui.viewer_combobox.currentText()
        data["map[viewer_id]"] = self.get_viewer_id(viewer_name)
        data["map[lang]"] = self.ui.language_combobox.currentText()
        data["map[scales]"] = self.ui.scales_lineedit.text()
        data["map[search_db]"] = self.ui.search_db_combobox.currentText()
        data["map[search_type"] = self.ui.search_type_list.currentItem().text()
        data["map[search_sql]"] = self.ui.search_sql_textedit.text()

        self.api.update_map(self.map_id, data)

        # add userlist to settings
        QSettings().setValue("qgiscloud/%s/userlist" %
                             map_settings["map"]["name"],
                             ", ".join(map_settings["map"]["users"]))
        QGuiApplication.restoreOverrideCursor()

    def check_plan(self, plan):
        # Disable GUI elements
        if plan != "Free":
            if self.ui.search_type_list.currentItem().text() != "DBSearch":
                self.ui.search_db_combobox.setVisible(False)
                self.ui.search_sql_textedit.setVisible(False)
                self.ui.sql_preview_btn.setVisible(False)
                # labels
                self.ui.search_db_lbl.setVisible(False)
                self.ui.search_sql_lbl.setVisible(False)
            else:
                self.set_sql_query()
        else:
            for child in self.findChildren(QLineEdit):
                child.setEnabled(False)
            for child in self.findChildren(QComboBox):
                child.setEnabled(False)
            for child in self.findChildren(QCheckBox):
                child.setEnabled(False)
            for child in self.findChildren(QListWidget):
                child.setEnabled(False)
            for child in self.findChildren(QPushButton):
                if child.objectName():
                    child.setEnabled(False)
            for child in self.findChildren(QgsCodeEditorSQL):
                child.setEnabled(False)
            # enable gui elements for free User
            self.ui.generate_scales_btn.setEnabled(True)
            self.ui.scales_lineedit.setEnabled(True)
            self.ui.language_combobox.setEnabled(True)


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

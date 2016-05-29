# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QgisCloudPlugin
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
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
# Initialize Qt resources from file resources_rc.py
import resources_rc
# Import the code for the dialog
from qgiscloudplugindialog import QgisCloudPluginDialog
# API compatibilty module. Has to be imported only once.
import apicompat


class QgisCloudPlugin:

    def __init__(self, iface, version):
        # Save reference to the QGIS interface
        self.iface = iface
        self.version = version

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(QIcon(":/plugins/qgiscloud/icon.png"), \
            "Cloud Settings", self.iface.mainWindow())
        QObject.connect(self.action, SIGNAL("triggered()"), self.showHideDockWidget)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Cloud", self.action)

        self.plugin_dir = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/qgiscloud"
        # initialize locale
        localePath = ""
        locale = QSettings().value("locale/userLocale", type=str)[0:2]
        if QFileInfo(self.plugin_dir).exists():
            localePath = self.plugin_dir + "/i18n/qgiscloudplugin_" + locale + ".qm"

        if QFileInfo(localePath).exists():
            self.translator = QTranslator()
            self.translator.load(localePath)            

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
                
        # dock widget
        self.dockWidget = QgisCloudPluginDialog(self.iface, self.version)
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockWidget)                

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu("&Cloud",self.action)
        self.iface.removeToolBarIcon(self.action)
        self.dockWidget.unload()
        self.iface.removeDockWidget(self.dockWidget)

    def showHideDockWidget(self):
        if self.dockWidget.isVisible():
            self.dockWidget.hide()
        else:
            self.dockWidget.show()

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
from qgis.PyQt.QtCore import Qt, QCoreApplication, QSettings, QFileInfo, QTranslator, qVersion
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
# Initialize Qt resources from file resources_rc.py
from .resources_rc import *
# Import the code for the dialog
from .qgiscloudplugindialog import QgisCloudPluginDialog

import os


class QgisCloudPlugin(object):

    def __init__(self, iface, version):
        # Save reference to the QGIS interface
        self.iface = iface
        self.version = version
        

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(QIcon(":/plugins/qgiscloud/icon.png"), \
            "QGIS Cloud Settings", self.iface.mainWindow())
        self.action.triggered.connect(self.showHideDockWidget)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&QGIS Cloud", self.action)

        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale_short = QSettings().value("locale/userLocale", type=str)[0:2]
        locale_long = QSettings().value("locale/userLocale", type=str)
                
        if QFileInfo(self.plugin_dir).exists():            
            if QFileInfo(self.plugin_dir + "/i18n/qgiscloudplugin_" + locale_short + ".qm").exists():
                self.translator = QTranslator()
                self.translator.load( self.plugin_dir + "/i18n/qgiscloudplugin_" + locale_short + ".qm")            
                if qVersion() > '4.3.3':
                    QCoreApplication.installTranslator(self.translator)
            elif QFileInfo(self.plugin_dir + "/i18n/qgiscloudplugin_" + locale_long + ".qm").exists():
                self.translator = QTranslator()
                self.translator.load( self.plugin_dir + "/i18n/qgiscloudplugin_" + locale_long + ".qm")          
                if qVersion() > '4.3.3':
                    QCoreApplication.installTranslator(self.translator)                
                
#        # dock widget
        self.dockWidget = QgisCloudPluginDialog(self.iface, self.version)
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockWidget)                

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu("&QGIS Cloud",self.action)
        self.iface.removeToolBarIcon(self.action)
        self.dockWidget.unload()
        self.iface.removeDockWidget(self.dockWidget)

    def showHideDockWidget(self):
        if self.dockWidget.isVisible():
            self.dockWidget.hide()
        else:
            self.dockWidget.show()

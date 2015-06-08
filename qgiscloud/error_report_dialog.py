# -*- coding: utf-8 -*-
"""
/***************************************************************************
OpenLayers Plugin
A QGIS plugin

                             -------------------
begin                : 2015-06-08
copyright            : (C) 2015 by Sandro Mani, Sourcepole
email                : smani at sourcepole.ch
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
from . import version
import apicompat
import urllib
import sys
import platform


class ErrorReportDialog(QDialog):
    def __init__(self, title, message, errors, username, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle(title)

        self.verticalLayout = QVBoxLayout(self)

        self.label = QLabel(message, self)
        self.verticalLayout.addWidget(self.label)

        self.plainTextEdit = QPlainTextEdit(self)
        self.plainTextEdit.setPlainText(errors)
        self.plainTextEdit.setReadOnly(True)
        self.verticalLayout.addWidget(self.plainTextEdit)

        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)
        self.verticalLayout.addWidget(self.buttonBox)
        self.reportButton = self.buttonBox.addButton(self.tr("Report error"), QDialogButtonBox.ActionRole)

        self.reportButton.clicked.connect(self.__reportError)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.username = username

    def __reportError(self):
        body = ("Please describe your issue here:\n\n"
                "Technical information:\n%s\n\n"
                "Versions:\n"
                " QGIS: %s\n"
                " Python: %s\n"
                " OS: %s\n"
                " QGIS Cloud Plugin: %s\n\n"
                "Username: %s\n") % (
                    self.plainTextEdit.toPlainText(),
                    QGis.QGIS_VERSION,
                    sys.version.replace("\n", " "),
                    platform.platform(),
                    version(),
                    self.username)
        url = QUrl()
        url.setEncodedUrl("mailto:support@qgiscloud.com?subject=%s&body=%s" % (
                urllib.quote(pystring(self.tr("Data upload error"))),
                urllib.quote(body)))
        QDesktopServices.openUrl(url)

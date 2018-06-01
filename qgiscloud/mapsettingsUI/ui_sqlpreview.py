# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'sqlpreview.ui'
#
# Created by: PyQt5 UI code generator 5.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_sql_preview(object):
    def setupUi(self, sql_preview):
        sql_preview.setObjectName("sql_preview")
        sql_preview.resize(766, 584)
        self.gridLayout = QtWidgets.QGridLayout(sql_preview)
        self.gridLayout.setObjectName("gridLayout")
        self.sql_preview_view = QtWidgets.QTableView(sql_preview)
        self.sql_preview_view.setObjectName("sql_preview_view")
        self.gridLayout.addWidget(self.sql_preview_view, 0, 0, 1, 1)

        self.retranslateUi(sql_preview)
        QtCore.QMetaObject.connectSlotsByName(sql_preview)

    def retranslateUi(self, sql_preview):
        _translate = QtCore.QCoreApplication.translate
        sql_preview.setWindowTitle(_translate("sql_preview", "SQL preview"))


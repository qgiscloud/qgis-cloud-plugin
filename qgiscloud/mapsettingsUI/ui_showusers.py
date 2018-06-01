# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'showusers.ui'
#
# Created by: PyQt5 UI code generator 5.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_show_users(object):
    def setupUi(self, show_users):
        show_users.setObjectName("show_users")
        show_users.resize(603, 435)
        self.gridLayout = QtWidgets.QGridLayout(show_users)
        self.gridLayout.setObjectName("gridLayout")
        self.users_listview = QtWidgets.QTableView(show_users)
        self.users_listview.setObjectName("users_listview")
        self.gridLayout.addWidget(self.users_listview, 0, 0, 1, 5)
        self.copy_users = QtWidgets.QPushButton(show_users)
        self.copy_users.setObjectName("copy_users")
        self.gridLayout.addWidget(self.copy_users, 1, 4, 1, 1)

        self.retranslateUi(show_users)
        QtCore.QMetaObject.connectSlotsByName(show_users)

    def retranslateUi(self, show_users):
        _translate = QtCore.QCoreApplication.translate
        show_users.setWindowTitle(_translate("show_users", "All users"))
        self.copy_users.setText(_translate("show_users", "copy selected user list"))


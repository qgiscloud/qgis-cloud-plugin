# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'user_list_manager.ui'
#
# Created by: PyQt5 UI code generator 5.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_user_list_manager(object):
    def setupUi(self, user_list_manager):
        user_list_manager.setObjectName("user_list_manager")
        user_list_manager.resize(401, 406)
        self.gridLayout = QtWidgets.QGridLayout(user_list_manager)
        self.gridLayout.setObjectName("gridLayout")
        self.list_name_edit = QtWidgets.QLineEdit(user_list_manager)
        self.list_name_edit.setObjectName("list_name_edit")
        self.gridLayout.addWidget(self.list_name_edit, 0, 1, 1, 1)
        self.list_box = QtWidgets.QGroupBox(user_list_manager)
        self.list_box.setObjectName("list_box")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.list_box)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.add_user_btn = QtWidgets.QPushButton(self.list_box)
        self.add_user_btn.setObjectName("add_user_btn")
        self.gridLayout_2.addWidget(self.add_user_btn, 1, 2, 1, 1)
        self.user_listwidget = QtWidgets.QListWidget(self.list_box)
        self.user_listwidget.setObjectName("user_listwidget")
        self.gridLayout_2.addWidget(self.user_listwidget, 0, 0, 3, 1)
        self.remove_user_btn = QtWidgets.QPushButton(self.list_box)
        self.remove_user_btn.setObjectName("remove_user_btn")
        self.gridLayout_2.addWidget(self.remove_user_btn, 2, 2, 1, 1)
        self.gridLayout.addWidget(self.list_box, 1, 0, 1, 2)
        self.list_label = QtWidgets.QLabel(user_list_manager)
        self.list_label.setObjectName("list_label")
        self.gridLayout.addWidget(self.list_label, 0, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(user_list_manager)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Save)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 2, 1, 1, 1)
        self.delete_list_btn = QtWidgets.QPushButton(user_list_manager)
        self.delete_list_btn.setObjectName("delete_list_btn")
        self.gridLayout.addWidget(self.delete_list_btn, 2, 0, 1, 1)

        self.retranslateUi(user_list_manager)
        QtCore.QMetaObject.connectSlotsByName(user_list_manager)

    def retranslateUi(self, user_list_manager):
        _translate = QtCore.QCoreApplication.translate
        user_list_manager.setWindowTitle(_translate("user_list_manager", "user list management"))
        self.list_box.setTitle(_translate("user_list_manager", "User List"))
        self.add_user_btn.setText(_translate("user_list_manager", "+"))
        self.remove_user_btn.setText(_translate("user_list_manager", "-"))
        self.list_label.setText(_translate("user_list_manager", "List Name"))
        self.delete_list_btn.setText(_translate("user_list_manager", "delete list"))


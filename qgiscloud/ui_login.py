# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_login.ui'
#
# Created: Sat Jul 23 23:29:53 2011
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_LoginDialog(object):
    def setupUi(self, LoginDialog):
        LoginDialog.setObjectName(_fromUtf8("LoginDialog"))
        LoginDialog.resize(268, 95)
        self.gridLayout = QtGui.QGridLayout(LoginDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label_5 = QtGui.QLabel(LoginDialog)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout.addWidget(self.label_5, 0, 0, 1, 1)
        self.editUser = QtGui.QLineEdit(LoginDialog)
        self.editUser.setEnabled(True)
        self.editUser.setInputMask(_fromUtf8(""))
        self.editUser.setText(_fromUtf8(""))
        self.editUser.setObjectName(_fromUtf8("editUser"))
        self.gridLayout.addWidget(self.editUser, 0, 1, 1, 1)
        self.label_6 = QtGui.QLabel(LoginDialog)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.gridLayout.addWidget(self.label_6, 1, 0, 1, 1)
        self.editPassword = QtGui.QLineEdit(LoginDialog)
        self.editPassword.setEnabled(True)
        self.editPassword.setInputMask(_fromUtf8(""))
        self.editPassword.setText(_fromUtf8(""))
        self.editPassword.setEchoMode(QtGui.QLineEdit.Password)
        self.editPassword.setObjectName(_fromUtf8("editPassword"))
        self.gridLayout.addWidget(self.editPassword, 1, 1, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(LoginDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 2)
        self.label_5.setBuddy(self.editUser)
        self.label_6.setBuddy(self.editPassword)

        self.retranslateUi(LoginDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), LoginDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), LoginDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(LoginDialog)

    def retranslateUi(self, LoginDialog):
        LoginDialog.setWindowTitle(QtGui.QApplication.translate("LoginDialog", "Login", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("LoginDialog", "User:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("LoginDialog", "Password:", None, QtGui.QApplication.UnicodeUTF8))


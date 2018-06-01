# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'generatescales.ui'
#
# Created by: PyQt5 UI code generator 5.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_generate_scales(object):
    def setupUi(self, generate_scales):
        generate_scales.setObjectName("generate_scales")
        generate_scales.resize(338, 156)
        self.gridLayout = QtWidgets.QGridLayout(generate_scales)
        self.gridLayout.setObjectName("gridLayout")
        self.min_lbl = QtWidgets.QLabel(generate_scales)
        self.min_lbl.setObjectName("min_lbl")
        self.gridLayout.addWidget(self.min_lbl, 0, 0, 1, 1)
        self.min_lineedit = QtWidgets.QLineEdit(generate_scales)
        self.min_lineedit.setObjectName("min_lineedit")
        self.gridLayout.addWidget(self.min_lineedit, 0, 1, 1, 1)
        self.max_lbl = QtWidgets.QLabel(generate_scales)
        self.max_lbl.setObjectName("max_lbl")
        self.gridLayout.addWidget(self.max_lbl, 1, 0, 1, 1)
        self.max_lineedit = QtWidgets.QLineEdit(generate_scales)
        self.max_lineedit.setObjectName("max_lineedit")
        self.gridLayout.addWidget(self.max_lineedit, 1, 1, 1, 1)
        self.steps_lbl = QtWidgets.QLabel(generate_scales)
        self.steps_lbl.setObjectName("steps_lbl")
        self.gridLayout.addWidget(self.steps_lbl, 2, 0, 1, 1)
        self.steps_lineedit = QtWidgets.QLineEdit(generate_scales)
        self.steps_lineedit.setObjectName("steps_lineedit")
        self.gridLayout.addWidget(self.steps_lineedit, 2, 1, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(generate_scales)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 3, 0, 1, 2)

        self.retranslateUi(generate_scales)
        self.buttonBox.accepted.connect(generate_scales.accept)
        self.buttonBox.rejected.connect(generate_scales.reject)
        QtCore.QMetaObject.connectSlotsByName(generate_scales)

    def retranslateUi(self, generate_scales):
        _translate = QtCore.QCoreApplication.translate
        generate_scales.setWindowTitle(_translate("generate_scales", "Generate scales"))
        self.min_lbl.setText(_translate("generate_scales", "Minimum"))
        self.max_lbl.setText(_translate("generate_scales", "Maximum"))
        self.steps_lbl.setText(_translate("generate_scales", "Steps"))


# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/hdus/dev/qgis/qgis-cloud-plugin/qgiscloud/qgis3_warning_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Qgis3Warning(object):
    def setupUi(self, Qgis3Warning):
        Qgis3Warning.setObjectName("Qgis3Warning")
        Qgis3Warning.setWindowModality(QtCore.Qt.ApplicationModal)
        Qgis3Warning.resize(583, 318)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(Qgis3Warning)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.frame = QtWidgets.QFrame(Qgis3Warning)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.gridLayout = QtWidgets.QGridLayout(self.frame)
        self.gridLayout.setObjectName("gridLayout")
        self.textBrowser = QtWidgets.QTextBrowser(self.frame)
        self.textBrowser.setAcceptDrops(False)
        self.textBrowser.setReadOnly(True)
        self.textBrowser.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        self.textBrowser.setOpenExternalLinks(True)
        self.textBrowser.setObjectName("textBrowser")
        self.gridLayout.addWidget(self.textBrowser, 0, 0, 1, 1)
        self.cb_dont_show_again = QtWidgets.QCheckBox(self.frame)
        self.cb_dont_show_again.setObjectName("cb_dont_show_again")
        self.gridLayout.addWidget(self.cb_dont_show_again, 1, 0, 1, 1)
        self.verticalLayout_3.addWidget(self.frame)
        self.buttonBox = QtWidgets.QDialogButtonBox(Qgis3Warning)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_3.addWidget(self.buttonBox)

        self.retranslateUi(Qgis3Warning)
        self.buttonBox.accepted.connect(Qgis3Warning.accept)
        self.buttonBox.rejected.connect(Qgis3Warning.reject)
        QtCore.QMetaObject.connectSlotsByName(Qgis3Warning)

    def retranslateUi(self, Qgis3Warning):
        _translate = QtCore.QCoreApplication.translate
        Qgis3Warning.setWindowTitle(_translate("Qgis3Warning", "QGIS 3 Warning"))
        self.textBrowser.setHtml(_translate("Qgis3Warning", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">You have started the QGIS Cloud Plugin with QGIS 3. Please note that due to several bugs in QGIS Server 3, QGIS Cloud with QGIS 3 is not yet suitable for productive use. </p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">If you need a stable production environment, please use QGIS 2.18.</span> </p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">QGIS 2.18 is very mature and very suitable for professional and productive use of QGIS Cloud.</p></body></html>"))
        self.cb_dont_show_again.setText(_translate("Qgis3Warning", "Don\'t show again"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Qgis3Warning = QtWidgets.QDialog()
    ui = Ui_Qgis3Warning()
    ui.setupUi(Qgis3Warning)
    Qgis3Warning.show()
    sys.exit(app.exec_())


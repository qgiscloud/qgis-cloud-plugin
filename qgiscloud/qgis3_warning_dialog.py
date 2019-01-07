# -*- coding: utf-8 -*-

"""
Module implementing Qgis3Warning.
"""

from qgis.PyQt.QtCore import pyqtSlot,  QSettings
from qgis.PyQt.QtWidgets import QDialog
from .Ui_qgis3_warning_dialog import Ui_Qgis3Warning
from qgis.PyQt import uic
import os

class Qgis3Warning(QDialog, Ui_Qgis3Warning):
    """
    Class documentation goes here.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget
        @type QWidget
        """
        super(Qgis3Warning, self).__init__(parent)
        self.setupUi(self)
        
    @pyqtSlot()
    def on_buttonBox_accepted(self):
        """
        Slot documentation goes here.
        """
        print (self.cb_dont_show_again.isChecked())
        
        QSettings().setValue("Plugin-QgisCloud/qgis3_info_off", self.cb_dont_show_again.isChecked())
        self.close()        
    
    @pyqtSlot()
    def on_buttonBox_rejected(self):
        """
        Slot documentation goes here.
        """
        print (self.cb_dont_show_again.isChecked())
        
        QSettings().setValue("Plugin-QgisCloud/qgis3_info_off", self.cb_dont_show_again.isChecked())
        self.close()
        

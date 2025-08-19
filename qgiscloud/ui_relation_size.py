# -*- coding: utf-8 -*-

"""
Module implementing RelationSizeDialog.
"""
from PyQt5 import uic
from qgis.PyQt.QtCore import pyqtSlot,  Qt
from qgis.PyQt.QtWidgets import QApplication,  QDialog,  QTableWidgetItem,  QAbstractScrollArea,  QFileDialog
import sys
import os
from contextlib import contextmanager

try:
    filename = os.path.join(os.path.dirname(sys.executable), 'forms/relation_size.ui')
    FORM_CLASS, _ = uic.loadUiType(filename)
except:
    filename = os.path.join(os.path.dirname(__file__), 'ui_relation_size.ui')
    FORM_CLASS, _ = uic.loadUiType(filename)

class RelationSizeDialog(QDialog, FORM_CLASS):
    """
    Class documentation goes here.
    """
    
    @contextmanager
    def wait_cursor(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            yield
        finally:
            QApplication.restoreOverrideCursor()     
    

    def __init__(self, db,  dbname,  parent=None):
        """
        Constructor

        @param parent reference to the parent widget (defaults to None)
        @type QWidget (optional)
        """
        super().__init__(parent)
        self.setupUi(self)
        conn = db.psycopg_connection()
        cursor = conn.cursor()
        self.setWindowTitle(self.tr('Database {db} - Table overview'.format(db = dbname)))
        
        with self.wait_cursor():

            sql = """
      SELECT
        schemaname || '.' || tablename AS tablename,
        pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) AS pretty_size,
        pg_total_relation_size(schemaname || '.' || tablename) as size 
      FROM pg_tables
      WHERE schemaname not in ('pg_catalog', 'information_schema', 'topology')
        AND tablename not in ('spatial_ref_sys')
      ORDER BY size desc
    """
            cursor.execute(sql)
            rows=cursor.fetchall()
            
            sql = """
    SELECT pg_size_pretty(sum(pg_total_relation_size(schemaname || '.' || tablename))) AS size 
    FROM pg_tables
      WHERE schemaname NOT IN ('pg_catalog', 'information_schema', 'topology')
        AND tablename NOT IN ('spatial_ref_sys')        
    """
            cursor.execute(sql)
            total_size = cursor.fetchone()[0]
            
            self.result_table(rows,  self.tab_relation_size,  total_size)            
            
    @pyqtSlot()
    def on_buttonBox_rejected(self):
        """
        Slot documentation goes here.
        """
        self.close()

    @pyqtSlot()
    def on_btn_export_csv_clicked(self):
        """
        Slot documentation goes here.
        """
        self.save_as_csv()
        
    def result_table(self,  result,  tab_widget,  total_size):
        tab_widget.clear()

        if result != None:
            column_names = ['Table',  'Size']
            tab_widget.setColumnCount(len(column_names))
            tab_widget.setRowCount(len(result))
            tab_widget.setHorizontalHeaderLabels(column_names)
            tab_widget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
            
            row_count = 0
            for row in result:
                for col in range(len(column_names)):
                    self.tab_item = QTableWidgetItem(str(row[col]))
                    tab_widget.setItem(row_count,  col,  self.tab_item)
                row_count += 1
                    
            tab_widget.resizeColumnsToContents()        

    def save_as_csv(self):
        import csv
        path,  filter = QFileDialog.getSaveFileName(
                self, 'Save File', '', 'CSV(*.csv)')
        if len(path) > 0:
            with self.wait_cursor():
                with open(path, 'w',  newline='') as stream:
                    writer = csv.writer(stream)
                    writer.writerow(['Tablename',  'Size'])
                    for row in range( self.tab_relation_size.rowCount()):
                        rowdata = []
                        for column in range( self.tab_relation_size.columnCount()):
                            item =  self.tab_relation_size.item(row, column)
                            if item is not None:
                                rowdata.append(
                                    item.text())
                            else:
                                rowdata.append('')
                        writer.writerow(rowdata)

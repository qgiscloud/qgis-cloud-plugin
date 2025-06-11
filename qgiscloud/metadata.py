# -*- coding: utf-8 -*-
"""
/***************************************************************************
QMetaDB-Connector
                             -------------------
begin                : 2016-12-02
copyright            : (C) 2016 by Dr. Horst Duester / Sourcepole AG
email                : horst.duester@sourcepole.ch
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QFile, QTextStream, QIODevice
import os

class Metadata():
    
    def __init__(self):
        self._read_metadata()
    
    def _read_metadata(self):
        self.plugindir = self.plugin_dir = self.plugin_dir = os.path.dirname(__file__)
        mdFile = QFile(self.plugindir+"/metadata.txt")
        mdFile.open(QIODevice.ReadOnly | QIODevice.Text)
        inFile = QTextStream(mdFile)
        
        changeLog = ''
        self.result = {}

        self.result['version'] = ''
        self.result['description'] = ''
        self.result['name'] = ''                
        self.result['date'] = ''
        self.result['qgisMinimumVersion'] = ''               
        self.result['qgisMaximumVersion'] = ''               
        self.result['author'] = ''              
        self.result['email'] = ''                               
        self.result['homepage'] = ''               
        self.result['tracker'] = ''               
        self.result['repository'] = ''               
        self.result['changelog'] = ''
        
        while (not inFile.atEnd()):
            line = inFile.readLine()
            lineArr = line.split("=")
            
            if lineArr[0] == 'version':
               self.result['version'] = lineArr[1]
            elif lineArr[0] == 'description':
               self.result['description'] = lineArr[1]
            elif lineArr[0] == 'name':
               self.result['name'] = lineArr[1]                
            elif lineArr[0] == 'qgisMinimumVersion':
               self.result['qgisMinimumVersion'] = lineArr[1]               
            elif lineArr[0] == 'qgisMaximumVersion':
               self.result['qgisMaximumVersion'] = lineArr[1]               
            elif lineArr[0] == 'author':
               self.result['author'] = lineArr[1]               
            elif lineArr[0] == 'email':
               self.result['email'] = lineArr[1]                               
            elif lineArr[0] == 'homepage':
               self.result['homepage'] = lineArr[1]               
            elif lineArr[0] == 'tracker':
                self.result['tracker'] = lineArr[1]               
            elif lineArr[0] == 'repository':
                self.result['repository'] = lineArr[1]               
            elif lineArr[0] == 'date':   
                self.result['date'] = lineArr[1]                
                
            elif lineArr[0] == 'changelog':
                line = inFile.readLine()
                while len(line.split("=")) == 1:
                    if line[0:1] != '#':
                        changeLog += line+"\n"
                    line = inFile.readLine()
                    
                self.result['changelog'] = changeLog
                
    
    def version(self):
        return self.result['version']
        
    def description(self):
        return self.result['description']
        
        
    def name(self):
       return self.result['name']
       
    def date(self):
       return self.result['date']       
       
    def qgisMinimumVersion(self):
       return self.result['qgisMinimumVersion']
       
    def qgisMaximumVersion(self):
       return self.result['qgisMaximumVersion']
       
    def author(self):
       return self.result['author']
       
    def email(self):
       return self.result['email']
       
    def homepage(self):
       return self.result['homepage']
       
    def tracker(self):
        return self.result['tracker']
        
    def repository(self):
        return self.result['repository']               
        
    def changelog(self):
        return self.result['changelog']        
        
    

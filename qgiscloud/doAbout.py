# -*- coding: latin1 -*-
"""
/***************************************************************************
 QgisCloudPlugin
                                 A QGIS plugin
 Publish maps on qgiscloud.com
                              -------------------
        begin                : 2011-04-04
        copyright            : (C) 2011 by Sourcepole
        email                : horst.duester@sourcepole.ch
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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui_qgiscloudplugin import Ui_QgisCloudPlugin

class DlgAbout:
#    def __init__( self):    
#        # setup labels
#        
        
        # setup texts
    def aboutString(self):
        aboutString = QString('<p><center><b>Publish maps on qgiscloud.com<b></center></p>')
        return aboutString
    
    def contribString(self):
        contribString = QString("<p><center><b>The developement of QGISCloud-Plugin was supported by the following persons:</b></center></p>") 
        contribString.append( "<p>Pirmin Kalberer (project manager, developer and support)<br>" )
        contribString.append( "Mathias Walker (developer)<br>" )
        contribString.append( "Dr. Marco Hugentobler (developer)<br>" )
        contribString.append( "Dr. Horst Düster (developer and support)<br><br>" )
        return contribString
        
    def licenseString(self):
        licenseString = QString("Sourcepole AG - Linux & Open Source Solutions<br>")
        licenseString.append("Weberstrasse 5, 8004 Zürich, Switzerland<br>")
        
        licenseString.append("<br>")
        licenseString .append("Contact:<br>")
        licenseString.append( "support@qgiscloud.com<br>")
        licenseString.append( "http://qgiscloud.com<br>")
        
        return licenseString
    
    

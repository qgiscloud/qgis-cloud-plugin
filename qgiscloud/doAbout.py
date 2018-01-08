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
from builtins import object

class DlgAbout(object):
    def aboutString(self):
        return '<p><center><b>Publish maps on qgiscloud.com<b></center></p>'
    
    def contribString(self):
        return """
        <p><center><b>The QGIS Cloud-Plugin is developed by the following persons:</b></center></p> 
        <p>Dr. Horst Düster (product manager, developer and support)<br>
        Pirmin Kalberer (project manager, developer and support)<br>
        Sandro Mani (developer)<br>
        Mathias Walker (developer and support)<br>
        Dr. Marco Hugentobler (developer and support)
        </p>
        <p><b>Translations:</b</p><br>
        Hebrew - Harel Dan <br>
        Italian - Sandro Mani <br>
        Portuguese (Brazil) - Rodrigo Smarzaro<br>
        Portuguese (Europeu) - Nelson Silva<br>
        Spanish - Mario Alberto Luna Pavo<br><br>
        """
        
    def licenseString(self):
        return  """
        Sourcepole AG - Linux & Open Source Solutions<br>
        Weberstrasse 5, 8004 Zürich, Switzerland<br>
        <br>
        Contact:<br>
        support@qgiscloud.com<br>
        http://qgiscloud.com<br>
        <br>
        Source code and bug tracker:<br>
        https://github.com/qgiscloud/qgis-cloud-plugin
        """

#/***************************************************************************
# QgisCloudPlugin
# 
# Publish maps on qgiscloud.com
#                             -------------------
#        begin                : 2011-04-04
#        copyright            : (C) 2011 by Sourcepole
#        email                : pka@sourcepole.ch
# ***************************************************************************/
# 
#/***************************************************************************
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation; either version 2 of the License, or     *
# *   (at your option) any later version.                                   *
# *                                                                         *
# ***************************************************************************/

# Makefile for a PyQGIS plugin 

PLUGINNAME = qgiscloudplugin

PY_FILES = qgiscloudplugin.py qgiscloudplugindialog.py __init__.py

EXTRAS = icon.png logo.png

UI_FILES = ui_qgiscloudplugin.py ui_login.py

RESOURCE_FILES = resources_rc.py

default: compile

compile: $(UI_FILES) $(RESOURCE_FILES)

%_rc.py : %.qrc
	pyrcc4 -o $@  $<

%.py : %.ui
	pyuic4 -o $@ $<

# The deploy  target only works on unix like operating system where
# the Python plugin directory is located at:
# $HOME/.qgis/python/plugins
deploy: compile
	mkdir -p $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
	cp -vf $(PY_FILES) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
	cp -vf $(UI_FILES) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
	cp -vf $(RESOURCE_FILES) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
	cp -vf $(EXTRAS) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)

publish: compile
	echo "Deploy remote repo (don't forget to tag the release!)"
	git push && git push --tags
	ssh root@builder su builder /home/builder/qgis-plugins-update

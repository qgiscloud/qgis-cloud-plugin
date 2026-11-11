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

# CONFIGURATION
PLUGIN_UPLOAD = $(CURDIR)/plugin_upload.py

# Makefile for a PyQGIS plugin 

# translation
PYLUPDATE ?= pylupdate5
LRELEASE ?= lrelease

# Python modules used by the plugin at runtime
SOURCES = qgiscloudplugin.py \
          qgiscloudplugindialog.py \
          background_layers_menu.py \
          data_upload.py \
          db_connection_cfg.py \
          db_connections.py \
          error_report_dialog.py \
          local_data_sources.py \
          login_dialog.py \
          mapsettingsdialog.py \
          PGVectorLayerImport.py \
          ui_relation_size.py \
          qgiscloudapi/qgiscloudapi.py \
          raster/raster_upload.py

# Qt Designer forms loaded at runtime with uic.loadUiType()
FORMS = qgiscloudplugin.ui \
        ui_login.ui \
        mapsettings.ui \
        ui_relation_size.ui

TRANSLATIONS = i18n/qgiscloudplugin_ca.ts \
	i18n/qgiscloudplugin_cs.ts \
	i18n/qgiscloudplugin_da.ts \
	i18n/qgiscloudplugin_de.ts \
	i18n/qgiscloudplugin_es.ts \
	i18n/qgiscloudplugin_fi.ts \
	i18n/qgiscloudplugin_fr.ts \
	i18n/qgiscloudplugin_he.ts \
	i18n/qgiscloudplugin_hu.ts \
	i18n/qgiscloudplugin_it.ts \
	i18n/qgiscloudplugin_ja.ts \
	i18n/qgiscloudplugin_nb.ts \
	i18n/qgiscloudplugin_nl.ts \
	i18n/qgiscloudplugin_pl.ts \
	i18n/qgiscloudplugin_pt_BR.ts \
	i18n/qgiscloudplugin_pt_PT.ts \
	i18n/qgiscloudplugin_ro.ts \
	i18n/qgiscloudplugin_ru.ts \
	i18n/qgiscloudplugin_sv.ts \
	i18n/qgiscloudplugin_tr.ts \
	i18n/qgiscloudplugin_uk.ts \
	i18n/qgiscloudplugin_zh-Hans.ts

PLUGINNAME = qgiscloud

PY_FILES = qgiscloudplugin.py qgiscloudplugindialog.py __init__.py

EXTRAS = icon.png logo.png
ASSETS = assets

# resources_rc.py is committed as is (resources.qrc is empty), do not regenerate it
RESOURCE_FILES = resources_rc.py

default: transcompile

%.qm : %.ts
	$(LRELEASE) $<

# The deploy  target only works on unix like operating system where
# the Python plugin directory is located at:
# $HOME/.qgis/python/plugins
deploy: doc transcompile
	mkdir -p $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
	cp -vf $(PY_FILES) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
	cp -vf $(FORMS) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
	cp -vf $(RESOURCE_FILES) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
	cp -vf $(EXTRAS) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
	cp -vfr $(ASSETS) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
	cp -vfr i18n $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
	cp -vfr $(HELP) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)/help

# The dclean target removes compiled python files from plugin directory
# also delets any .svn entry
dclean:
	find $(HOME)/.qgis/python/plugins/$(PLUGINNAME) -iname "*.pyc" -delete
	find $(HOME)/.qgis/python/plugins/$(PLUGINNAME) -iname ".svn" -prune -exec rm -Rf {} \;

# The derase deletes deployed plugin
derase:
	rm -Rf $(HOME)/.qgis/python/plugins/$(PLUGINNAME)

# The zip target deploys the plugin and creates a zip file with the deployed
# content. You can then upload the zip file on http://plugins.qgis.org
zip: deploy dclean 
	rm -f $(PLUGINNAME).zip
	cd $(HOME)/.qgis/python/plugins; zip -9r $(CURDIR)/$(PLUGINNAME).zip $(PLUGINNAME)

# Create a zip package of the plugin named $(PLUGINNAME).zip. 
# This requires use of git (your plugin development directory must be a 
# git repository).
# To use, pass a valid commit or tag as follows:
#   make package VERSION=Version_0.3.2
package:
		rm -f $(PLUGINNAME).zip
		git archive --prefix=$(PLUGINNAME)/ -o $(PLUGINNAME).zip $(VERSION)
		echo "Created package: $(PLUGINNAME).zip"

upload: #zip
	$(PLUGIN_UPLOAD) $(PLUGINNAME).zip

# transup
# update .ts translation files from SOURCES and FORMS
# (strings no longer in the code are kept and marked as obsolete)
transup:
	$(PYLUPDATE) $(SOURCES) $(FORMS) -ts $(TRANSLATIONS)

# transcompile
# compile translation files into .qm binary format
transcompile: $(TRANSLATIONS:.ts=.qm)

# transclean
# deletes all .qm files
transclean:
	rm -f i18n/*.qm

# build documentation with sphinx
doc: 
	cd help; make html

#publish: compile doc transcompile
#	echo "Deploy remote repo (don't forget to tag the release!)"
#	git push && git push --tags
#	ssh root@builder su builder /home/builder/qgis-plugins-update
# To plugins.qgis.org:
# make package VERSION=master
# make upload
# Web application:
# cap production rake:invoke task=qgiscloud:fetch_plugin_xml

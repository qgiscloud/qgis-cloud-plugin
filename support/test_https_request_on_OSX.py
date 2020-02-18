# This script can be used to check whether https
# access to qgiscloud works from Python
#
# Please have a look at https://github.com/qgiscloud/qgis-cloud-plugin/wiki/Resolving-certificate-problems-on-OSX#testing
# on how to use it.

import urllib.request
req = urllib.request.Request('https://api.qgiscloud.com')
with urllib.request.urlopen(req) as response:
    the_page = response.read()

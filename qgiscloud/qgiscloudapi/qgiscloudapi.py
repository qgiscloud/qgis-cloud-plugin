# -*- coding: utf-8 -*-
"""
qgiscloudapi

library for accessing the qgiscloud API using Python

Copyright 2011 Sourcepole AG

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by maplicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

### basic usage example
# from qgiscloudapi.qgiscloudapi import *
#
# api = API()
# api.set_auth(user='myname', password='secretpassword')
#
# maps = api.read_maps()

"""
from builtins import str
from builtins import object
from qgis.core import *

# python versions below 2.6 do not have json included we need simplejson then
try:
    import json
except ImportError:
    from .. import simplejson as json

import time
from urllib.parse import urlencode
import urllib.request, urllib.error, urllib.parse
import base64, zlib
from .version import __version__

API_URL = 'https://api.qgiscloud.com'

__all__ = ['API', 'UnauthorizedError', 'ConnectionException', 'TokenRequiredError', 'BadRequestError', 'ForbiddenError',
           'ConflictDuplicateError', 'GoneError', 'InternalServerError',
           'NotImplementedError', 'ThrottledError']


class API(object):
    """
        The API class contains all methods to access the qgiscloud RESTful
        API.

        It wraps the HTTP requests to resources in convenient methods and also
        takes care of authenticating each request with a token, if needed.

        The create_token, check_token, get_token and set_token methods can be
        used to work with the token from outside the API class. This might be
        useful when it is not intended to ask users for their user and
        password for new instances of the API class.

        To instantiate API with a predefined token use something like:

        # token = json.loads('{"token": "A2wY7qgUNM5eTRM3Lz6D4RZHuGmYPP"}')
        # api = API(token=token)
    """

    user = None
    password = None
    _token = None
    cache = None
    url = None

    def __init__(self, token=None, cache=None, url=API_URL):
        self.set_token(token)
        self.cache = cache
        self.url = url

    def set_url(self, url):
        self.url = url

    def api_url(self):
        return API_URL

    def check_versions(self):
        request = Request(cache=self.cache, url=self.url)
        content = request.get('/.meta/version.json')
        return json.loads(content)

    def requires_auth(self):
        """
            requires_auth checks that methods that require
            a token can't be called without a token.

            If check_token doesn't return True a TokenRequiredError exception is
            raised telling the caller to use the create_token method to get a
            valid token.
        """
        if not (self.check_auth() or self.check_token()):
            raise TokenRequiredError

    def set_auth(self, user, password):
        """
            Set user/password for authentication.
        """
        self.user = bytearray()
        self.user.extend(map(ord, user))
        self.password = bytearray()

        if password != None:
            self.password.extend(map(ord,  password))
            return True
        else:
            return False

    def reset_auth(self):
        """
            Reset user/password for authentication.
        """
        self.user = self.password = None
        
    def accept_tos(self):
        """
        Accept GDPR complient privacy policy
        """
        self.requires_auth()
        resource = '/account/accept_tos.json'
        request = Request(user=self.user, password=self.password, token=self.get_token(), cache=self.cache, url=self.url)
        request.post(resource)
        return True     

    def check_auth(self):
        """
            Set user/password for authentication.
        """
        if self.user and self.password:
            return True
        return False

    def check_login(self, version_info):
        self.requires_auth()
        resource = '/notifications.json'
        data = {
            'type': 'Login',
            'info': version_info
        }

        request = Request(user=self.user,
                                       password=self.password,
                                       token=self.get_token(),
                                       cache=self.cache,
                                       url=self.url)
#        request = Request(user=self.user.encode('utf-8'),
#                                       password=self.password.encode('utf-8'),
#                                       token=self.get_token(),
#                                       cache=self.cache,
#                                       url=self.url)

        content = request.post(resource, data)
        login_info = json.loads(content)
        if 'clouddb' not in login_info:
            login_info['clouddb'] = True
        return login_info

    def create_token(self, user, password):
        """
            Queries the API for a new Token and saves it as self._token.
        """
        request = Request(user=user.encode('utf-8'), password=password.encode('utf-8'), cache=self.cache, url=self.url)
        content = request.post('/token.json')
        self.set_token(json.loads(content))
        return True

    def check_token(self):
        """
            This method checks if there's a token.
        """
        token = self.get_token()
        if token:
            return True
        return False

    def set_token(self, token):
        """
            We use set_token to set the token.
        """
        self._token = token

    def get_token(self):
        """
            We use get_token to get the token.
        """
        return self._token

    def create_database(self):
        """
            Create a database.
        """
        self.requires_auth()
        resource = '/databases.json'
        request = Request(user=self.user, password=self.password, token=self.get_token(), cache=self.cache, url=self.url)
        data = {}
        content = request.post(resource, data)
        return json.loads(content)

    def read_databases(self):
        """
            Returns a list of databases.
        """
        self.requires_auth()
        resource = '/databases.json'
        request = Request(user=self.user, password=self.password, token=self.get_token(), cache=self.cache, url=self.url)
        content = request.get(resource)
        return json.loads(content)

    def read_maps(self):
        """
            Returns a list of databases.
        """
        self.requires_auth()
        resource = '/maps.json'
        request = Request(user=self.user, password=self.password, token=self.get_token(), cache=self.cache, url=self.url)
        content = request.get(resource)
        return json.loads(content)

    def delete_database(self, db_name):
        """
            Delete a database.
        """
        self.requires_auth()
        resource = '/databases/%s.json' % (db_name)
        request = Request(user=self.user, password=self.password, token=self.get_token(), cache=self.cache, url=self.url)
        content = request.delete(resource)
        return json.loads(content)

    def create_table(self, db_name, table, overwrite_table, columns, srid, geometry_type, provider, pkey=None, geom_column=None, geom_column_index=None):
        """
            Create a new table

            overwrite_table = <bool>, drop table if it exists

            columns = [
              {
                'name': '<NAME>',
                'type': '<TYPE>',
                'length': <LENGTH>,
                'precision': <PRECISION>
              }, ...
            ]

            srid = 'EPSG:<SRID>'

            geometry_type = 'POINT' | 'MULTIPOINT' | 'LINESTRING' | 'MULTILINESTRING' | 'POLYGON' | 'MULTIPOLYGON'

            provider = '<QGIS PROVIDER NAME>'

            pkey, geom_column, geom_column_index = primary key and geometry column and index for PostGIS provider
        """
        self.requires_auth()
        resource = '/databases/%s/tables.json' % (db_name)
        data = {
            'table': json.dumps({
                'overwrite': overwrite_table,
                'name': table,
                'columns': [],
                'srid': srid,
                'geometry_type': geometry_type
            }),
            'provider': provider
        }
        data['table']['columns'] = columns
        if pkey is not None:
            data['table']['pkey'] = pkey
        if geom_column is not None:
            data['table']['geom_column'] = geom_column
        if geom_column_index is not None:
            data['table']['geom_column_index'] = geom_column_index
        request = Request(user=self.user, password=self.password, token=self.get_token(), cache=self.cache, url=self.url)
        content = request.post(resource, data)
        return json.loads(content)

    def create_map(self, name, mapfile, config):
        """
            Create a new map and return it.
        """
        name = name.decode('utf-8')

        self.requires_auth()
        resource = '/maps.json'
        file = open(mapfile, "rb")
        encoded_file = file.read()
        data = {
                'map': json.dumps({
                    'name' : name,
                    'config': config
                }),
                'file': encoded_file
        }
        request = Request(user=self.user, password=self.password, token=self.get_token(), cache=self.cache, url=self.url)
        content = request.post(resource, data)
        return json.loads(content)

    def read_maps(self):
        """
            Returns a list of maps.
        """
        self.requires_auth()
        resource = '/maps.json'
        request = Request(user=self.user, password=self.password, token=self.get_token(), cache=self.cache, url=self.url)
        content = request.get(resource)
        return json.loads(content)

    def read_map(self, map_id):
        """
            Returns all map details.
        """
        self.requires_auth()
        resource = '/maps/%s.json' % (map_id)
        request = Request(user=self.user, password=self.password, token=self.get_token(), cache=self.cache, url=self.url)
        content = request.get(resource)
        return json.loads(content)

    def load_map_project(self,  map_name,  map_id):
        """
            Download of QGIS project file.
        """
        self.requires_auth()
        headers = {}
        resource = '/maps/%s/qgs.json' % (map_id)
        headers['Content-Type'] = 'application/x-qgis-project'
        request = Request(user=self.user, password=self.password, token=self.get_token(), cache=self.cache, url=self.url)
        content = request.get(resource,  headers)

        return content

    def delete_map(self, map_id):
        """
            Delete a map.
        """
        self.requires_auth()
        resource = '/maps/%s.json' % (map_id)
        request = Request(user=self.user, password=self.password, token=self.get_token(), cache=self.cache, url=self.url)
        request.delete(resource)
        return True

    def update_map(self, map_id, data):
        """
            Returns a list of maps.
        """
        self.requires_auth()
        resource = '/maps/%s.json' % (map_id)
        request = Request(user=self.user, password=self.password, token=self.get_token(), cache=self.cache, url=self.url)
        content = request.put(resource, data)
        return json.loads(content)

    def create_graphic(self, name, symbol):
        """
            Upload a symbol.
        """
        self.requires_auth()
        resource = '/graphics.json'
        file = open(symbol, "rb")
        encoded_file = file.read()
        data = {
                'graphic': json.dumps({
                    'name' : name,
                }),
                'file': encoded_file
        }
        request = Request(user=self.user, password=self.password, token=self.get_token(), cache=self.cache, url=self.url)
        content = request.post(resource, data)
        return json.loads(content)

    def read_viewers(self):
        """
            Returns all viewers.
        """
        self.requires_auth()
        resource = '/viewers.json'
        request = Request(user=self.user, password=self.password, token=self.get_token(), cache=self.cache, url=self.url)
        content = request.get(resource)
        return json.loads(content)

    def read_map_options(self):
        """
            Returns all map select field options.
        """
        self.requires_auth()
        resource = '/maps/edit_options.json'
        request = Request(user=self.user, password=self.password, token=self.get_token(), cache=self.cache, url=self.url)
        content = request.get(resource)
        return json.loads(content)

    def create_exception(self, exception, version_info, project_fname):
        """
            Upload a plugin exception.
        """
        self.requires_auth()
        resource = '/notifications.json'
        encoded_file = ''
        try:
            file = open(project_fname, 'rb')
            encoded_file = file.read()
        except:
            pass
        try:
            exception_info = exception + str(version_info) + encoded_file
        except:
            exception_info = 'No exception info (message has encoding problems)' + str(version_info)
        data = {
            'type': 'ClientException',
            'info': exception_info
        }
        request = Request(user=self.user, password=self.password, token=self.get_token(), cache=self.cache, url=self.url)
        content = request.post(resource, data)
        return json.loads(content)

###
#
# EXCEPTIONS
#
###

class ConnectionException(Exception):
    """
        We raise this exception if the API was unreachable.
    """
    pass

class TokenRequiredError(Exception):
    """
        We raise this exception if a method requires a token but self._token
        is none.

        Use the create_token() method to get a new token.
    """
    def __unicode__(self):
        return 'No valid token. Use create_token(user, password) to get a new one'

class BadRequestError(Exception):
    """
        We raise this exception whenever the API answers with HTTP STATUS 400
        BAD REQUEST.
    """

    #msgs = {}
    msgs = []

    def __init__(self, value):
        try:
            self.msgs = json.loads(value) #json.loads(value[12:])
        except ValueError:
            self.msgs = [] #{}

    def __str__(self):
        #msg = ''
        #for key in self.msgs:
        #    msg = msg + key + ': ' + self.msgs[key] + '\n'
        msg = '\n'.join(self.msgs)
        return msg

class UnauthorizedError(Exception):
    """
        We raise this exception whenever the API answers with HTTP STATUS 401
        UNAUTHORIZED.
    """
    pass

class ForbiddenError(Exception):
    """
        We raise this exception whenever the API answers with HTTP STATUS 403
        FORBIDDEN.
    """
    pass

class NotFoundError(Exception):
    """
        We raise this exception whenever the API answers with HTTP STATUS 404
        NOT FOUND.
    """
    pass

class ConflictDuplicateError(Exception):
    """
        We raise this exception whenever the API answers with HTTP STATUS 409
        DUPLICATE ENTRY.
    """
    pass

class GoneError(Exception):
    """
        We raise this exception whenever the API answers with HTTP STATUS 410
        GONE.
    """
    pass

class InternalServerError(Exception):
    """
        We raise this exception whenever the API answers with HTTP STATUS 500
        INTERNAL SERVER ERROR.
    """
    pass

class NotImplementedError(Exception):
    """
        We raise this exception whenever the API answers with HTTP STATUS 501
        NOT IMPLEMENTED.
    """
    pass

class ThrottledError(Exception):
    """
        We raise this exception whenever the API answers with HTTP STATUS 503
        THROTTLED.
    """
    pass

###
#
# Custom HTTPBasicAuthHandler with fix for infinite retries when submitting wrong password
# http://bugs.python.org/issue8797
# http://bugs.python.org/file20471/simpler_fix.patch
#
###
#
#                    passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
#                    passman.add_password(None, url, username, password)
#                    urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPBasicAuthHandler(passman)))
#                    urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPCookieProcessor()))
#
#                    request = urllib.request.Request(url)
#                    base64string = base64.b64encode(b'%s:%s' % (username, password))
#                    request.add_header("Authorization", b"Basic %s" % base64string)

class HTTPBasicAuthHandlerLimitRetries(urllib.request.HTTPBasicAuthHandler):
    def __init__(self, *args, **kwargs):
        urllib.request.HTTPBasicAuthHandler.__init__(self, *args, **kwargs)

    def http_error_auth_reqed(self, authreq, host, req, headers):
        authreq = headers.get(authreq, None)
        if authreq:
            mo = urllib.request.AbstractBasicAuthHandler.rx.search(authreq)
            if mo:
                if len(mo.groups()) == 3:
                    scheme, quote, realm = mo.groups()
                else:
                    scheme, realm = mo.groups()
                if scheme.lower() == 'basic':
                    return self.retry_http_basic_auth(host, req, realm)

    def retry_http_basic_auth(self, host, req, realm):
        user, pw = self.passwd.find_user_password(realm, host)
        if pw is not None:
#                        base64string = base64.b64encode(b'%s:%s' % (username, password))
#                        request.add_header("Authorization", b"Basic %s" % base64string)
#            raw = ("%s:%s" % (user, pw)).encode('utf8')
#            auth = 'Basic %s' % base64.b64encode(raw).strip()
            raw = base64.b64encode(b"%s:%s" % (user, pw))
            auth = 'Basic %s' % raw
            if req.get_header(self.auth_header, None) == auth:
                return None
            req.add_unredirected_header(self.auth_header, auth)
            #return self.parent.open(req, timeout=req.timeout)
            return self.parent.open(req)

###
#
# Request Class using urllib2 to fire HTTP requests
#
###

class Request(object):
    """
        Request is used internally to actually fire API requests. It has some
        handy shortcut methods for POST, GET, PUT and DELETE, sets correct
        headers for each method, takes care of encoding data and handles all API
        errors by throwing exceptions.
    """
    user = None
    password = None
    token = None
    version = None
    url = None

    def __init__(self, user=None, password=None, token=None, cache=None, version=__version__, url=API_URL,  headers=None):
        self.user = user
        self.password = password
        self.token = token
        self.version = version
        self.cache = cache # FIXME: no caching in urllib2?
        self.url = url

    def post(self, resource, data={}):
        return self.request(resource, method='POST', data=data)

    def get(self, resource,  headers={}):
        return self.request(resource, method='GET',  data=None,  headers=headers)

    def put(self, resource, data={}):
        return self.request(resource, method='PUT', data=data)

    def delete(self, resource):
        return self.request(resource, method='DELETE')

    def request(self, resource, method='GET', data=None, headers={}):
        """
            use urllib
        """
        url = self.url + resource

        #
        # If the current API instance has a valid token we add the Authorization
        # header with the correct token.
        #
        # In case we do not have a valid token but user and password are
        # provided we automatically use them to add a HTTP Basic Authenticaion
        # header to the request to create a new token.
        #
        if self.token is not None:
            headers['Authorization'] = 'auth_token="%s"' % (self.token['token'])
        elif self.user is not None and self.password is not None:

#passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
#passman.add_password(None, url, username, password)
#urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPBasicAuthHandler(passman)))
#urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPCookieProcessor()))
#
            password_manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            password_manager.add_password(None, self.url, self.user, self.password)
            auth_handler = HTTPBasicAuthHandlerLimitRetries(password_manager)
            opener = urllib.request.build_opener(auth_handler)
            urllib.request.install_opener(opener)
        #
        # The API expects the body to be urlencoded. If data was passed to
        # the request method we therefore use urlencode from urllib.
        #
        if data == None:
            body = ''
        else:
            body = urlencode(data).encode('utf-8')

        #
        # We set the Host Header for MacOSX 10.5, to circumvent the NotFoundError
        #
        #headers['Host'] = 'api.qgiscloud.com'
        #
        # We set the User-Agent Header to qgiscloudapi and the local version.
        # This enables basic statistics about still used qgiscloudapi versions in
        # the wild.
        #
        headers['User-Agent'] = 'qgiscloudapi/%s' % (self.version)
        #
        # The API expects PUT or POST data to be x-www-form-urlencoded so we
        # also set the correct Content-Type header.
        #
        if method.upper() in ['PUT', 'POST']:
            headers['Content-Type']='application/x-www-form-urlencoded'
            #headers['Content-Type']='multipart/form-data'
        #
        # We also set the Content-Length and Accept-Encoding headers.
        #
        headers['Content-Length'] = str(len(body))
#        headers['Accept-Encoding'] = 'compress, gzip'
        #
        # Finally we fire the actual request.
        #
#        for i in range(1, 6):
#request = urllib.request.Request(url)
        base64string = base64.b64encode(b'%s:%s' % (self.user, self.password))
        headers['Authorization'] = b"Basic %s" % base64string
#request.add_header("Authorization", b"Basic %s" % base64string)
#u = urllib.request.urlopen(request)
        try:
            request_method = method.upper()
            if request_method in ['PUT', 'POST']:
                req = urllib.request.Request(url=url, data=body, headers=headers)
            else:
                req = urllib.request.Request(url=url, headers=headers)
            if request_method in ['PUT', 'DELETE']:
                # add PUT and DELETE methods
                req.get_method = lambda: request_method
            response = urllib.request.urlopen(req).read()

        except urllib.error.HTTPError as e:
            #
            # Handle the possible responses according to their HTTP STATUS
            # CODES.
            #
            # All non success STATUS CODES raise an exception containing
            # the API error message.
            #
            msg = e.read().decode('UTF8', errors='ignore')
            if e.code in [201, 202, 203, 204]: # Workaround for old Pythons
                return msg
            elif e.code == 400:
                raise BadRequestError(msg)
            elif e.code == 401:
                raise UnauthorizedError(msg)
            elif e.code == 403:
                raise ForbiddenError(msg)
            elif e.code == 404:
                raise NotFoundError()
            elif e.code == 409:
                raise ConflictDuplicateError(msg)
            elif e.code == 410:
                raise GoneError(msg)
            elif e.code == 422: # Unprocessable Entity
                raise BadRequestError(msg)
            #
            # 500 INTERNAL SERVER ERRORs normally shouldn't happen...
            #
            elif e.code == 500:
                raise InternalServerError(msg)
            elif e.code == 501:
                raise NotImplementedError(msg)
            elif e.code == 503:
                raise ThrottledError(msg)
#            except urllib2.URLError, e:
#                # if we could not reach the API we wait 1s and try again
#                time.sleep(1)
#                # if we tried for the fifth time we give up - and cry a little
#                if i == 5:
#                    raise ConnectionException('Connection to server failed: %s' % str(e))
        else:
            #
            # 200 OK, 201 CREATED and 204 DELETED result in returning the actual
            # response.
            #
            return response.decode('UTF8')

#  Copyright (c) 2013-2014, The University of Chicago
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
#  - Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
#  - Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#  - Neither the name of The University of Chicago nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.

from requests import exceptions, Session
from urlparse import urlparse
from pprint import pprint
import json
import sys
from requests.exceptions import HTTPError
from chisubmit.client.exceptions import UnknownObjectException,\
    ChisubmitRequestException, BadRequestException, UnauthorizedException
import base64



class Requester(object):
    
    def __init__(self, login_or_token, password, base_url):
        
        self.__base_url = base_url
        
        self.__headers = {}
        self.__headers['content-type'] = 'application/json'
        if login_or_token is not None and password is not None:
            self.__headers["Authorization"] = "Basic " + base64.b64encode('%s:%s' % (login_or_token, password))
        elif login_or_token is not None:
            self.__headers["Authorization"] = "Token %s" % login_or_token
        
        self.__session = Session()

    def request(self, method, resource, data=None, headers=None, params=None):
        if resource.startswith("/"):
            url = self.__base_url + resource
        else:
            # TODO: Validate the URL is valid given base_url
            url = resource

        all_headers = {}
        all_headers.update(self.__headers)
        if headers is not None:
            all_headers.update(headers)

        if data is not None:
            data = json.dumps(data)
            
        # TODO: try..except
        response = self.__session.request(url = url,
                                  method = method,
                                  params = params,
                                  data = data,
                                  headers = all_headers)
        
        if response.status_code == 400:
            raise BadRequestException(method, url, params, data, all_headers, response)        
        elif 400 < response.status_code < 500:
            if response.status_code == 401:
                raise UnauthorizedException(method, url, params, data, all_headers, response)
            if response.status_code == 404:
                raise UnknownObjectException(method, url, params, data, all_headers, response)
            else:
                raise ChisubmitRequestException(method, url, params, data, all_headers, response)
        elif 500 <= response.status_code < 600:
            raise ChisubmitRequestException(method, url, params, data, all_headers, response)

        try:
            response_data = response.json()
        except ValueError:
            response_data = {"data": response.text}

        return response.headers, response_data

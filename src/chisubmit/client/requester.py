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

class BadRequestError(HTTPError):
    
    def __init__(self, method, url, errors, *args, **kwargs):
        self.method = method
        self.url = url
        self.errors = errors        
        super(BadRequestError, self).__init__(*args, **kwargs)
        
    def print_errors(self):
        print "HTTP request %s %s returned error code 400 (Bad Request)" %(self.method, self.url)
        if len(self.errors) == 0:
            print "No additional error messages returned."
        else:
            for noun, message in self.errors:
                print "%s: %s" % (noun, message)
    

class Requester(object):
    
    def __init__(self, api_token, base_url, testing_app = None):
        
        self.__base_url = base_url
        self.__testing = testing_app is not None
        
        self.__headers = {}
        self.__headers['content-type'] = 'application/json'
        if api_token is not None:
            self.__headers["CHISUBMIT-API-KEY"] = api_token
            
        if self.__testing:
            self.__test_client = testing_app.test_client()
        else:
            self.__session = Session()
            
    def __werkzeug_request(self, method, url, data, headers, params):
        response = self.__test_client.open(path = url,
                                           method = method,
                                           query_string=params,
                                           data=data,
                                           headers=headers)
        
        return response.status_code, response.status, response.headers, response.get_data()

        

    def __requests_request(self, method, url, data, headers, params):
        response = self.__session.request(url = url,
                                          method = method,
                                          params = params,
                                          data = data,
                                          headers = headers)
        
        return response.status_code, response.reason, response.headers, response.text

    def request(self, method, resource, data=None, headers=None, params=None):
        url = self.__base_url + resource
        print url
        all_headers = {}
        all_headers.update(self.__headers)
        if headers is not None:
            all_headers.update(headers)
        
        if self.__testing:
            status_code, status, headers, data = self.__werkzeug_request(method, url, data, all_headers, params)
        else:
            status_code, status, headers, data = self.__requests_request(method, url, data, all_headers, params)
        
        try:
            print status_code
            print status
            print data
            data_json = json.loads(data)
        except ValueError, ve:
            if status_code == 400:
                raise BadRequestError(errors=[("unknown", "Unexpected error message: %s" % data)])
            else:
                raise ve        
        
        if status_code == 400:
            error_result = []
            for noun, problem in data_json.get('errors', {}).items():
                error_result.append((noun, problem))
            raise BadRequestError(method = method,
                                  url = url,
                                  errors = error_result)        
        elif 400 < status_code < 500:
            http_error_msg = '%s Client Error: %s' % (status_code, status)
            raise #TODO
        elif 500 <= status_code < 600:
            http_error_msg = '%s Server Error: %s' % (status_code, status)
            raise #TODO

        return headers, data_json

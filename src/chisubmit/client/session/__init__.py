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

# Disable the InsecurePlatformWarning warning
# This warning is thrown in versions of Python < 2.7.9, which includes pretty
# much all current Ubuntus.
# 
# Disabling this warning doesn't withhold information that the user could
# use to prevent a potentially insecure connection (as in the case of an
# untrusted certificate). The warning states that the version of Python and
# SSL used could lead to certain connections failing. So far, we haven't
# encountered this in any of our tests.
#
# More details here: https://urllib3.readthedocs.org/en/latest/security.html#insecureplatformwarning
try:
    from requests.packages.urllib3 import disable_warnings
    from requests.packages.urllib3.exceptions import InsecurePlatformWarning

    disable_warnings(category=InsecurePlatformWarning)
except ImportError, ie:
    pass

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
    

endpoint = None
session = None
test_client = None
testing = False
test_headers = None

def connect(url, access_token = None):
    global endpoint, session, testing
    testing = False
    endpoint = url
    session = Session()
    session.headers['content-type'] = 'application/json'
    if access_token is not None:
        session.headers["CHISUBMIT-API-KEY"] = access_token
    
def connect_test(app, access_token = None):
    global endpoint, test_client, testing, test_headers
    endpoint = "/api/v0/"
    test_client = app.test_client()
    testing = True
    test_headers = {'content-type': 'application/json'}
    if access_token is not None:
        test_headers["CHISUBMIT-API-KEY"] = access_token

    return test_client

def raise_for_status(response):
    if testing:
        http_error_msg = ''
    
        if 400 <= response.status_code < 500:
            http_error_msg = '%s Client Error: %s' % (response.status_code, response.status)
    
        elif 500 <= response.status_code < 600:
            http_error_msg = '%s Server Error: %s' % (response.status_code, response.status)
    
        if http_error_msg:
            raise HTTPError(http_error_msg, response=response)
    else:
        response.raise_for_status()


def __process_response(response, method, url):
    if testing:
        response_text = response.get_data()
        response_exc = None
    else:
        response_text = response.text
        response_exc = response
        
    if response.status_code != 400:
        raise_for_status(response)
    
    try:
        if testing:
            data_json = json.loads(response.get_data())
        else:
            data_json = response.json()
    except ValueError, ve:
        if response.status_code == 400:
            raise BadRequestError(errors=[("unknown", "Unexpected error message: %s" % response_text)])
        else:
            raise ve
            
    if response.status_code == 400:
        error_result = []
        for noun, problem in data_json.get('errors', {}).items():
            error_result.append((noun, problem))
        raise BadRequestError(method = method,
                              url = url,
                              errors = error_result,
                              response = response_exc)

    return data_json


def get(resource, headers=None, **kwargs):
    url = endpoint + resource
    
    if testing:
        if headers is None:
            headers = test_headers
        else:
            headers.update(test_headers)
        response = test_client.get(url, headers=headers, **kwargs)
    else:    
        response = session.get(url, headers=headers, **kwargs)
        
    return __process_response(response, method = "GET", url = url) 

def post(resource, data, headers=None, **kwargs):
    url = endpoint + resource

    if testing:
        if headers is None:
            headers = test_headers
        else:
            headers.update(test_headers)        
        response = test_client.post(url, data=data, headers=headers, **kwargs)
    else:
        response = session.post(url, data, headers=headers, **kwargs)
    
    return __process_response(response, method = "POST", url = url) 

def put(resource, data, headers = None, **kwargs):
    url = endpoint + resource
    
    if testing:
        if headers is None:
            headers = test_headers
        else:
            headers.update(test_headers)        
        response = test_client.put(url, data=data, headers=headers, **kwargs)
    else:
        response = session.put(url, data, headers=headers, **kwargs)
    
    return __process_response(response, method = "PUT", url = url) 


def exists(obj):
    if isinstance(obj, (str, unicode)):
        obj_endpoint = obj
    else:
        obj_endpoint = obj.url()
    if testing:
        response = test_client.get(endpoint + obj_endpoint, headers=test_headers)
    else:
        response = session.get(endpoint + obj_endpoint)
    if response.status_code == 404:
        return False
    return True

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
import json

endpoint = None
session = None
test_client = None
testing = False

def connect(url, access_token):
    global endpoint, session, testing
    testing = False
    endpoint = url
    session = Session()
    session.auth = (access_token, access_token)
    session.headers = {'content-type': 'application/json'}
    
def connect_test(app):
    global endpoint, test_client, testing
    endpoint = "/api/v0/"
    test_client = app.test_client()
    testing = True
    return test_client

def get(resource, **kwargs):
    if testing:
        response = test_client.get(endpoint + resource, **kwargs)
        return json.loads(response.get_data())
    else:    
        response = session.get(endpoint + resource, **kwargs)
        response.raise_for_status()
        return response.json()

def post(resource, data, **kwargs):
    if testing:
        response = test_client.post(endpoint + resource, data, **kwargs)
        return json.loads(response.get_data())
    else:
        response = session.post(endpoint + resource, data, **kwargs)
        if response.status_code == 400:
            error_result = []
            for noun, problem in response.json()['errors'].items():
                error_result.append((noun, problem))
            response.raise_for_status()
        else:
            response.raise_for_status()
        return response.json()

def put(resource, data, **kwargs):
    if testing:
        response = test_client.put(endpoint + resource, **kwargs)
        return json.loads(response.get_data())
    else:
        response = session.put(endpoint + resource, data, **kwargs)
        response.raise_for_status()
        return response.json()

def exists(obj):
    if isinstance(obj, (str, unicode)):
        obj_endpoint = obj
    else:
        obj_endpoint = obj.url()
    if testing:
        response = test_client.get(endpoint + obj_endpoint)
    else:
        response = session.get(endpoint + obj_endpoint)
    if response.status_code == 404:
        return False
    return True

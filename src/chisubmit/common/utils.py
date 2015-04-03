
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

import datetime
import pytz
import random
import hashlib
import base64
import string
from tzlocal import get_localzone
from chisubmit.repos.factory import RemoteRepositoryConnectionFactory
import math

localzone = get_localzone()

now_override = None

def get_datetime_now_utc():
    global now_override
    
    if now_override is None:
        return datetime.datetime.now(pytz.utc).replace(microsecond=0)
    else:
        return now_override 
    

def set_testing_now(dt):
    global now_override
    
    now_override = dt
    

def set_datetime_timezone_utc(dt):
    return pytz.utc.localize(dt)

def convert_datetime_to_utc(dt, default_tz = localzone):
    if dt.tzinfo is None:
        dt = localzone.localize(dt)
    return dt.astimezone(pytz.utc)

def convert_datetime_to_local(dt, default_tz = localzone):
    if dt.tzinfo is None:
        dt = localzone.localize(dt)
    return dt.astimezone(localzone)

def compute_extensions_needed(submission_time, deadline):
    delta = (submission_time - deadline).total_seconds()

    extensions_needed = math.ceil(delta / (3600.0 * 24))

    if extensions_needed <= 0:
        return 0
    else:
        return int(extensions_needed)

# Based on http://jetfar.com/simple-api-key-generation-in-python/
def gen_api_key():
    s = str(random.getrandbits(256))
    h = hashlib.sha256(s)
    altchars = random.choice(string.ascii_letters) + random.choice(string.ascii_letters)
    b = base64.b64encode(h.digest(), altchars).rstrip("==")
    return unicode(b)
    
    
def create_connection(course, config, staging = False):
    if not staging:
        connstr = course.options["git-server-connstr"]
    else:
        connstr = course.options["git-staging-connstr"]

    conn = RemoteRepositoryConnectionFactory.create_connection(connstr, staging)
    server_type = conn.get_server_type_name()
    
    git_credentials = None
    if config['git-credentials'] is not None:
        git_credentials = config['git-credentials'].get(server_type, None)

    if git_credentials is None:
        print "You do not have %s credentials." % server_type
        return None
    else:
        conn.connect(git_credentials)
        return conn
           

    
    

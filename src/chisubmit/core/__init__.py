
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

import os.path
from pkg_resources import Requirement, resource_filename
import ConfigParser
import shutil
import traceback
from chisubmit.common import CHISUBMIT_FAIL

DEFAULT_CHISUBMIT_DIR = os.path.expanduser("~/.chisubmit/")
DEFAULT_CONFIG_FILENAME = "chisubmit.conf"
DEFAULT_COURSE_FILENAME = "default_course"
GHTOKEN_FILENAME = "github_token"
GHDELETETOKEN_FILENAME = "github_delete_token"

chisubmit_dir = None
chisubmit_conf = None

class ChisubmitException(Exception):
    def __init__(self, message, original_exception = None):
        Exception.__init__(self, message)
        self.original_exception = original_exception
        if original_exception is not None:
            self.traceback = traceback.format_exc()
        else:
            self.traceback = None

    def print_exception(self):
        print self.traceback

def handle_unexpected_exception():
    print "ERROR: Unexpected exception"
    print traceback.format_exc()
    exit(CHISUBMIT_FAIL)

def init_chisubmit(base_dir = None, config_file = None):
    global chisubmit_dir, chisubmit_conf
    
    if base_dir is None:
        chisubmit_dir = DEFAULT_CHISUBMIT_DIR
    else:
        chisubmit_dir = os.path.expanduser(base_dir)
        
    if config_file is None:
        chisubmit_config_file = chisubmit_dir + DEFAULT_CONFIG_FILENAME
    else:
        chisubmit_config_file = os.path.expanduser(config_file)
    
    # Create chisubmit directory if it does not exist
    if not os.path.exists(chisubmit_dir):
        os.mkdir(chisubmit_dir)
        
    if not os.path.exists(chisubmit_dir + "/courses/"):        
        os.mkdir(chisubmit_dir + "/courses/")

    if not os.path.exists(chisubmit_dir + "/repositories/"):        
        os.mkdir(chisubmit_dir + "/repositories/")

    if not os.path.exists(chisubmit_config_file):
        example_conf = resource_filename(Requirement.parse("chisubmit"), "config/chisubmit.sample.conf")    
        shutil.copyfile(example_conf, chisubmit_config_file)   
    
    chisubmit_conf = ConfigParser.ConfigParser()
    chisubmit_conf.read(chisubmit_config_file)

def __get_file(filename):
    fname = chisubmit_dir + "/" + filename
    if not os.path.exists(fname):
        return None
    else:
        try:
            f = open(fname)
            contents = f.read().strip()
            return contents
        except IOError, ioe:
            raise ChisubmitException("Error when reading from file %s: %s" % (fname, ioe.meesage), ioe)        

def __set_file(filename, contents):
    fname = chisubmit_dir + "/" + filename
    try:
        f = open(fname, 'w')
        f.write(contents + "\n")
    except IOError, ioe:
        raise ChisubmitException("Error when writing to file %s: %s" % (fname, ioe.meesage), ioe)        
        
def get_default_course():
    return __get_file(DEFAULT_COURSE_FILENAME)

def set_default_course(course_id):
    __set_file(DEFAULT_COURSE_FILENAME, course_id)

def get_github_token():
    return __get_file(GHTOKEN_FILENAME)

def set_github_token(token):
    __set_file(GHTOKEN_FILENAME, token)

def get_github_delete_token():
    return __get_file(GHDELETETOKEN_FILENAME)

def set_github_delete_token(token):
    __set_file(GHDELETETOKEN_FILENAME, token)
    
def get_course_filename(course_id):
    return chisubmit_dir + "/courses/" + course_id + ".yaml"

    

    
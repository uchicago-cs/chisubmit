
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
import yaml

DEFAULT_CHISUBMIT_DIR = os.path.expanduser("~/.chisubmit/")
DEFAULT_CONFIG_FILENAME = "chisubmit.conf"

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
        
        
class ConfigFile(object):
    
    REQUIRED_FIELDS = []
    OPTIONAL_FIELDS = ["default-course", "git-credentials"]
        
    def __init__(self, config_file):
        self.config_file = config_file
        
        f = open(config_file)
        config = yaml.load(f)
        f.close()
        
        if type(config) != dict:
            raise ChisubmitException("Configuration file does not contain a YAML object")
        
        options = config.keys()
        
        for p in self.REQUIRED_FIELDS:
            if p not in options:
                raise ChisubmitException("Configuration file does not have required option '%s'" % p)
            options.remove(p)
            
        for p in options:
            if p not in self.OPTIONAL_FIELDS:
                raise ChisubmitException("Configuration file has invalid option '%s'" % p)

        self.options = config
                
    def save(self):
        try:
            f = open(self.config_file, 'w')
            yaml.dump(self.options, f, default_flow_style=False)
            f.close()
        except IOError, ioe:
            raise ChisubmitException("Error when saving configuration to file %s: %s" % (self.config_file, ioe.meesage), ioe)
        
    def get_default_course(self):
        return self.options.get("default-course")

    def set_default_course(self, default_course):
        self.options["default-course"] = default_course 
        self.save()
    
    def get_git_credentials(self, server_type):
        if self.options.has_key("git-credentials"):
            return self.options["git-credentials"].get(server_type)
        else:
            return None

    def set_git_credentials(self, server_type, git_credentials):
        self.options.set_default("git_credentials", {})[server_type] = git_credentials 
        self.save()


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
    
    chisubmit_conf = ConfigFile(chisubmit_config_file)


def chisubmit_config():
    global chisubmit_conf
    return chisubmit_conf
    
def get_course_filename(course_id):
    return chisubmit_dir + "/courses/" + course_id + ".yaml"

    

    
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
from chisubmit.common import ChisubmitException
import shutil
import yaml
import collections

DEFAULT_CHISUBMIT_DIR = os.path.expanduser("~/.chisubmit/")
DEFAULT_CONFIG_FILENAME = "chisubmit.conf"

# Based on http://stackoverflow.com/questions/3387691/python-how-to-perfectly-override-a-dict
class Config(collections.MutableMapping):

    IMPLICIT_FIELDS = ["directory"]
    REQUIRED_FIELDS = ["api-url"]
    OPTIONAL_FIELDS = ["default-course", "git-credentials", "server", "api-key"]
    ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS

    def __getitem__(self, key):
        if key in self.options:
            return self.options[key]
        elif key in self.OPTIONAL_FIELDS:
            return None
        else:
            raise KeyError

    def __setitem__(self, key, value):
        if key in self.ALL_FIELDS:
            self.options[key] = value
            self.save()
        else:
            raise KeyError

    def __delitem__(self, key):
        del self.options[key]
        self.save()

    def __iter__(self):
        return iter(self.options)

    def __len__(self):
        return len(self.options)

    def __init__(self, config_dir=None, config_file=None):

        if config_dir is None:
            config_dir = DEFAULT_CHISUBMIT_DIR
        else:
            config_dir = os.path.expanduser(config_dir)

        if config_file is None:
            config_file = config_dir + DEFAULT_CONFIG_FILENAME
        else:
            config_file = os.path.expanduser(config_file)
        
        self.create_directories(config_dir, config_file)
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        if type(config) != dict:
            raise ChisubmitException("Configuration is not valid YAML")

        options = config.keys()

        for p in self.REQUIRED_FIELDS:
            if p not in options:
                raise ChisubmitException("Configuration file does not have required option '%s'" % p)
            options.remove(p)

        for p in options:
            if p not in self.OPTIONAL_FIELDS:
                raise ChisubmitException("Configuration file has invalid option '%s'" % p)

        config['directory'] = config_dir
        self.config_file = config_file
        self.options = config

    def create_directories(self, config_dir, config_file):
        # Create directory if it does not exist
        if not os.path.exists(config_dir):
            os.mkdir(config_dir)

        if not os.path.exists(config_dir + "/courses/"):
            os.mkdir(config_dir + "/courses/")

        if not os.path.exists(config_dir + "/repositories/"):
            os.mkdir(config_dir + "/repositories/")

        if not os.path.exists(config_file):
            example_conf = resource_filename(Requirement.parse("chisubmit"), "chisubmit/config/chisubmit.sample.conf")
            shutil.copyfile(example_conf, config_file)

    def save(self):
        user_options = dict((k, v) for k,v in self.options.items() if k not in self.IMPLICIT_FIELDS)
        try:
            f = open(self.config_file, 'w')
            yaml.safe_dump(user_options, f, default_flow_style=False)
            f.close()
        except IOError, ioe:
            raise ChisubmitException("Error when saving configuration to file %s: %s" % (self.config_file, ioe.meesage), ioe)
        
    def get_server_profile(self, name=None):
        if not self.options.has_key("server"):
            return None
        
        if not self["server"].has_key("profiles"):
            return None
        
        if name is None:
            if not self["server"].has_key("default-profile"):
                return None
            else:
                name = self["server"]["default-profile"]

        if not self["server"]["profiles"].has_key(name):
            return None
        else:
            return self["server"]["profiles"][name]

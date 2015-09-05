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
from chisubmit.repos.factory import RemoteRepositoryConnectionFactory
from chisubmit.common.utils import read_string_file

SYSTEM_CONFIG_FILENAME = "/etc/chisubmit/chisubmit.conf"
GLOBAL_CONFIG_FILENAME = os.path.expanduser(".chisubmitconf")

CONFIG_DIRNAME = ".chisubmit"

class ConfigDirectoryNotFoundException(Exception):
    pass

class Config(object):

    @staticmethod
    def get_config_file_values(config_file):
        with open(config_file, 'r') as f:
            config_file_values = yaml.safe_load(f)
    
        if type(config_file_values) != dict:
            raise ChisubmitException("{} is not valid YAML".format(f))
        
        return config_file_values

    @staticmethod
    def get_global_config_values():
        config = {}
        
        for config_file in [SYSTEM_CONFIG_FILENAME, GLOBAL_CONFIG_FILENAME]:
            if os.path.exists(config_file):
                config_file_values = Config.get_config_file_values(config_file)
                
                config.update(config_file_values)     
                
        return config   

    @classmethod
    def get_global_config(cls):
        config = cls.get_global_config_values()
        
        # Right now, api-url is the only globally-settable value, but
        # this could change in the future
        api_url = config.get("api-url")
        
        return cls(config_dir = None, 
                   work_dir = None, 
                   api_url = api_url, 
                   api_key = None, 
                   default_course = None, 
                   git_credentials = {})


    @classmethod
    def get_config(cls, config_dir = None, work_dir = None, config_overrides = {}):      
        # If a configuration directory isn't specified, try to find it.
        if config_dir is None:
            dirl = os.getcwd().split(os.sep) + [CONFIG_DIRNAME]
            
            local_config_file = None
            while len(dirl) > 2:
                config_dir = os.sep.join(dirl)
                
                if os.path.exists(config_dir):
                    local_config_file = os.sep.join([config_dir, "chisubmit.conf"])
                    work_dir = os.sep.join(dirl[:-1]) 
                    break
                
                dirl.pop(-2)
            
            if local_config_file is None:
                raise ConfigDirectoryNotFoundException()
        else:
            local_config_file = os.sep.join([config_dir, "chisubmit.conf"])
            
        if not os.path.exists(local_config_file):
            raise ChisubmitException(".chisubmit directory ({}) does not contain a chisubmit.conf file".format(config_dir))
        
        config = cls.get_global_config_values()
        local_config_values = cls.get_config_file_values(local_config_file)
        config.update(local_config_values)
        config.update(config_overrides)
                
        # Check for configuration values
        if not "api-url" in config:
            raise ChisubmitException("Configuration value 'api-url' not found")
        else:
            api_url = config["api-url"]
            
        if not "api-key" in config:
            api_key = read_string_file("{}/api_key".format(config_dir))
        else:
            api_key = config["api-key"]

        if api_key is None:
            raise ChisubmitException("No chisubmit credentials were found!")
        
        if not "course" in config:
            course = read_string_file("{}/course".format(config_dir))
        else:
            course = config["course"]
            
        git_credentials = {}
        for server_type in RemoteRepositoryConnectionFactory.server_types:
            credentials = read_string_file("{}/{}.credentials".format(config_dir, server_type))
            if credentials is not None:
                git_credentials[server_type] = credentials
                    
        return cls(config_dir, work_dir, api_url, api_key, course, git_credentials)

    @classmethod
    def create_config_dir(cls, config_dir = None):
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
        pass

    def __init__(self, config_dir, work_dir, api_url, api_key, course, git_credentials):
        self.config_dir = config_dir
        self.work_dir = work_dir
        self.api_url = api_url
        self.api_key = api_key
        self.course = course
        self.git_credentials = git_credentials
        


        

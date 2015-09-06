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
import shutil
import yaml
import collections
from chisubmit.repos.factory import RemoteRepositoryConnectionFactory
from chisubmit.common import ChisubmitException


class ConfigDirectoryNotFoundException(Exception):
    pass

class Config(object):

    SYSTEM_CONFIG_FILENAME = "/etc/chisubmit/chisubmit.conf"
    GLOBAL_CONFIG_FILENAME = os.path.expanduser("~/.chisubmitconf")
    
    CONFIG_DIRNAME = ".chisubmit"
    
    SYSTEM = 0
    GLOBAL = 1
    LOCAL = 2    
    
    OPTION_API_URL = "api-url"
    OPTION_API_KEY = "api-key"
    OPTION_COURSE = "course"
    OPTION_GIT_CREDENTIALS = "git-credentials"
    
    VALID_OPTIONS = [OPTION_API_URL, OPTION_API_KEY, OPTION_COURSE, OPTION_GIT_CREDENTIALS]

    @staticmethod
    def get_config_file_values(config_file):
        if not os.path.exists(config_file):
            return {}
        
        with open(config_file, 'r') as f:
            config_file_values = yaml.safe_load(f)
    
        if type(config_file_values) != dict:
            raise ChisubmitException("{} is not valid YAML".format(f))
        
        return config_file_values
    
    @staticmethod
    def save_config_file_values(config_file, config_values):
        try:
            f = open(config_file, 'w')
            yaml.safe_dump(config_values, f, default_flow_style=False)
            f.close()
        except IOError, ioe:
            raise ChisubmitException("Error when saving configuration to file %s: %s" % (config_file, ioe.meesage), ioe)

    @staticmethod
    def set_config_value_in_file(config_file, option, value):
        config_file_values = Config.get_config_file_values(config_file)
        config_file_values[option] = value
        Config.save_config_file_values(config_file, config_file_values)

    @staticmethod
    def get_global_config_values():
        config = {}
        
        for config_file in [Config.SYSTEM_CONFIG_FILENAME, Config.GLOBAL_CONFIG_FILENAME]:
            if os.path.exists(config_file):
                config_file_values = Config.get_config_file_values(config_file)
                
                config.update(config_file_values)     
                
        return config   

    @classmethod
    def get_global_config(cls, config_overrides = {}):
        config = cls.get_global_config_values()
        config.update(config_overrides)

        return cls(config_dir = None, 
                   work_dir = None, 
                   config_values = config)


    @classmethod
    def get_config(cls, config_dir = None, work_dir = None, config_overrides = {}):
        assert( (config_dir is None and work_dir is None) or (config_dir is not None and work_dir is not None) )
        
        # If a configuration directory isn't specified, try to find it.
        if config_dir is None and work_dir is None:
            dirl = os.getcwd().split(os.sep) + [Config.CONFIG_DIRNAME]
            
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
                
        config = cls.get_global_config_values()
        local_config_values = cls.get_config_file_values(local_config_file)
        config.update(local_config_values)
        config.update(config_overrides)
                
        # Check for configuration values
        if not Config.OPTION_API_URL in config:
            raise ChisubmitException("Configuration value 'api-url' not found")
            
        if not Config.OPTION_API_KEY in config:
            raise ChisubmitException("No chisubmit credentials were found!")
        
        return cls(config_dir, work_dir, config)

    @classmethod
    def create_config_dir(cls, config_dir = None, work_dir = None): 
        if work_dir is None:
            work_dir = os.getcwd()
            
        if config_dir is None:
            config_dir = work_dir + "/.chisubmit"
        
        # Create directory if it does not exist
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        config_values = cls.get_global_config_values()            
        
        return cls(config_dir, work_dir, config_values)

    def __init__(self, config_dir, work_dir, config_values):
        self.config_dir = config_dir
        self.work_dir = work_dir
        
        self.config_values = {opt:config_values.get(opt) for opt in Config.VALID_OPTIONS}
        
    def __get_config_file(self, where):
        if where == Config.SYSTEM:
            return Config.SYSTEM_CONFIG_FILENAME
        elif where == Config.GLOBAL:
            return Config.GLOBAL_CONFIG_FILENAME
        elif where == Config.LOCAL:
            return "{}/chisubmit.conf".format(self.config_dir)


    def get_api_url(self):
        return self.config_values[Config.OPTION_API_URL]
    
    def set_api_url(self, api_url, where = None):
        if where is None: where = Config.LOCAL
                
        config_file = self.__get_config_file(where)
        Config.set_config_value_in_file(config_file, Config.OPTION_API_URL, api_url)
        
        
    def get_api_key(self):
        return self.config_values[Config.OPTION_API_KEY]
    
    def set_api_key(self, api_key, where = None):
        if where is None: where = Config.LOCAL
                
        config_file = self.__get_config_file(where)
        Config.set_config_value_in_file(config_file, Config.OPTION_API_KEY, api_key)
        
        
    def get_course(self):
        return self.config_values[Config.OPTION_COURSE]
    
    def set_course(self, course_id, where = None):
        if where is None: where = Config.LOCAL
                
        config_file = self.__get_config_file(where)
        Config.set_config_value_in_file(config_file, Config.OPTION_COURSE, course_id)


    def get_git_credentials(self, server_type):
        if server_type not in RemoteRepositoryConnectionFactory.server_types:
            raise ValueError("Unknown git server type: {}".format(server_type))

        if self.config_values.get(Config.OPTION_GIT_CREDENTIALS) is None:
            return None
        else:
            return self.config_values[Config.OPTION_GIT_CREDENTIALS].get(server_type)
    
    def set_git_credentials(self, server_type, credentials, where = None):
        if where is None: where = Config.LOCAL
        
        if server_type not in RemoteRepositoryConnectionFactory.server_types:
            raise ValueError("Unknown git server type: {}".format(server_type))
                
        config_file = self.__get_config_file(where)
        
        config_file_values = Config.get_config_file_values(config_file)
        if not Config.OPTION_GIT_CREDENTIALS in config_file_values:
            config_file_values[Config.OPTION_GIT_CREDENTIALS] = {}
        
        config_file_values[Config.OPTION_GIT_CREDENTIALS][server_type] = credentials
        
        Config.save_config_file_values(config_file, config_file_values)
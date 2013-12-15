import os.path
from pkg_resources import Requirement, resource_filename
import ConfigParser
import shutil
import traceback

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
        pass

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
    f = chisubmit_dir + "/" + filename
    if not os.path.exists(f):
        return None
    else:
        f = open(chisubmit_dir + "/" + filename)
        contents = f.read().strip()
        return contents

def __set_file(filename, contents):
    f = open(chisubmit_dir + "/" + filename, 'w')
    f.write(contents + "\n")

        
def get_default_course():
    return __get_file(DEFAULT_COURSE_FILENAME)

def set_default_course(course_id):
    __set_file(DEFAULT_COURSE_FILENAME, course_id)

def get_github_token():
    return __get_file(GHTOKEN_FILENAME)

def get_github_delete_token():
    return __get_file(GHDELETETOKEN_FILENAME)
    
def get_course_filename(course_id):
    return chisubmit_dir + "/courses/" + course_id + ".yaml"

    

    
import os.path
from pkg_resources import Requirement, resource_filename
import ConfigParser
import shutil
import traceback

DEFAULT_CHISUBMIT_DIR = os.path.expanduser("~/.chisubmit/")
DEFAULT_CONFIG_FILENAME = "chisubmit.conf"
DEFAULT_COURSE_FILENAME = "default_course"

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
        chisubmit_dir = base_dir
        
    if config_file is None:
        chisubmit_config_file = chisubmit_dir + DEFAULT_CONFIG_FILENAME
    else:
        chisubmit_config_file = config_file
    
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

        
def get_default_course():
    default_file = chisubmit_dir + "/" + DEFAULT_COURSE_FILENAME
    if not os.path.exists(default_file):
        return None
    else:
        default_file = open(chisubmit_dir + "/" + DEFAULT_COURSE_FILENAME)
        course = default_file.read().strip()
        return course

def set_default_course(course_id):
    default_file = open(chisubmit_dir + "/" + DEFAULT_COURSE_FILENAME, 'w')
    default_file.write(course_id + "\n")
    
def get_course_filename(course_id):
    return chisubmit_dir + "/courses/" + course_id + ".yaml"

    

    
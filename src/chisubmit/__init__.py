import os.path

VERSION="0.1"
RELEASE="0.1.0"

DEFAULT_CHISUBMIT_DIR = os.path.expanduser("~/.chisubmit/")
DEFAULT_CONFIG_FILE = DEFAULT_CHISUBMIT_DIR + "chisubmit.conf"
DEFAULT_COURSE_FILENAME = "default_course"

class ChisubmitException(Exception):
    pass

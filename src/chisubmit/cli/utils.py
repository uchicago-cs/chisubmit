import datetime
import os.path
from chisubmit import DEFAULT_COURSE_FILENAME

def create_subparser(subparsers, name, func):
    subparser = subparsers.add_parser(name)
    subparser.set_defaults(func=func)
    
    return subparser

def mkdatetime(datetimestr):
    return datetime.datetime.strptime(datetimestr, '%Y-%m-%dT%H:%M')

def get_default_course(config_dir):
    default_file = config_dir + "/" + DEFAULT_COURSE_FILENAME
    if not os.path.exists(default_file):
        return None
    else:
        default_file = open(config_dir + "/" + DEFAULT_COURSE_FILENAME)
        course = default_file.read().strip()
        return course

def set_default_course(config_dir, course):
    default_file = open(config_dir + "/" + DEFAULT_COURSE_FILENAME, 'w')
    default_file.write(course + "\n")


def get_course(config, args):
    if args.course:
        course = args.course
    else:
        course = get_default_course(args.dir)
    
    return course    


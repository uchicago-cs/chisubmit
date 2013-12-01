import sys
import traceback
import datetime

from argparse import ArgumentParser
import ConfigParser

from chisubmit import DEFAULT_CONFIG_FILE, DEFAULT_CHISUBMIT_DIR
from chisubmit.model import Course, Project, Student
from chisubmit.cli.course import *
from chisubmit.cli.student import *
from chisubmit.cli.team import create_team_subparsers
from chisubmit.cli.project import create_project_subparsers
from chisubmit.cli.utils import get_course

NON_COURSE_SUBCOMMANDS = ['course-create']

def chisubmit_cmd(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    
    # Setup argument parser
    parser = ArgumentParser(description="chisubmit")
    parser.add_argument('--config', type=str, default=DEFAULT_CONFIG_FILE)
    parser.add_argument('--dir', type=str, default=DEFAULT_CHISUBMIT_DIR)
    parser.add_argument('--noop', action="store_true")
    parser.add_argument('--course', type=str)

    subparsers = parser.add_subparsers(dest="subcommand")
    
    create_course_subparsers(subparsers)
    create_project_subparsers(subparsers)
    create_student_subparsers(subparsers)
    create_team_subparsers(subparsers)
    
    args = parser.parse_args(args = argv)
    
    config = ConfigParser.ConfigParser()
    config.read(args.config)

    if args.subcommand not in NON_COURSE_SUBCOMMANDS:
        course = get_course(config, args)
        if course is None:
            print "ERROR: No course specified with --course and no default course in configuration file"
            exit(1)
        else:
            course_file = open(args.dir + "/courses/" + course + ".yaml")
            course_obj = Course.from_file(course_file)
            course_file.close()
    else:
        course, course_obj = None, None

    if not args.noop:
        try:
            args.func(course_obj, config, args)
        except Exception, e:
            print "ERROR: Exception raised while executing %s command" % args.subcommand
            print traceback.format_exc()
            exit(3)

    if args.subcommand not in NON_COURSE_SUBCOMMANDS:
        course_file = open(args.dir + "/courses/" + course + ".yaml", 'w')
        course_obj.to_file(course_file)
        course_file.close()

    return 0
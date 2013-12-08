import sys
import traceback
import datetime
import os.path

from argparse import ArgumentParser

import chisubmit.core
import chisubmit.common.log as log
from chisubmit.core.model import Course, Project, Student
from chisubmit.cli.course import *
from chisubmit.cli.student import *
from chisubmit.cli.team import create_team_subparsers
from chisubmit.cli.project import create_project_subparsers
from chisubmit.cli.submit import create_submit_subparsers
from chisubmit.core import ChisubmitException
from chisubmit.common import CHISUBMIT_FAIL
from chisubmit.cli.shell import create_shell_subparsers

SUBCOMMANDS_NO_COURSE = ['course-create']
SUBCOMMANDS_DONT_SAVE = ['course-create', 'shell']

def chisubmit_cmd(argv=None):
    if argv is None:
        argv = sys.argv[1:]
        
    # Setup argument parser
    parser = ArgumentParser(description="chisubmit")
    parser.add_argument('--config', type=str, default=None)
    parser.add_argument('--dir', type=str, default=None)
    parser.add_argument('--noop', action="store_true")
    parser.add_argument('--course', type=str)
    parser.add_argument('--verbose', action="store_true")
    parser.add_argument('--debug', action="store_true")

    subparsers = parser.add_subparsers(dest="subcommand")
    
    create_course_subparsers(subparsers)
    create_project_subparsers(subparsers)
    create_student_subparsers(subparsers)
    create_team_subparsers(subparsers)
    create_submit_subparsers(subparsers)
    create_shell_subparsers(subparsers)
    
    args = parser.parse_args(args = argv)
    
    chisubmit.core.init_chisubmit(args.dir, args.config)
    log.init_logging(args.verbose, args.debug)

    if args.subcommand not in SUBCOMMANDS_NO_COURSE:
        if args.course:
            course_id = args.course
        else:
            course_id = chisubmit.core.get_default_course()
        
        if course_id is None:
            print "ERROR: No course specified with --course and no default course in configuration file"
            exit(CHISUBMIT_FAIL)
        else:
            course_obj = Course.from_course_id(course_id)
            if course_obj is None:
                print "ERROR: Course '%s' does not exist" % course_id
                exit(CHISUBMIT_FAIL)
    else:
        course_id, course_obj = None, None

    if not args.noop:
        try:
            rc = args.func(course_obj, args)
        except ChisubmitException, ce:
            print "ERROR: %s" % ce.message
            ce.print_exception()
            exit(CHISUBMIT_FAIL)
        except Exception, e:
            print "ERROR: Unexpected exception"
            print traceback.format_exc()
            exit(CHISUBMIT_FAIL)

    if args.subcommand not in SUBCOMMANDS_DONT_SAVE:
        course_file = chisubmit.core.open_course_file(course_id, 'w')
        course_obj.to_file(course_file)
        course_file.close()

    return rc

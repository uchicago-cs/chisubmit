
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

import sys
import traceback
import datetime
import os.path

from argparse import ArgumentParser

import chisubmit.core
import chisubmit.common.log as log
from chisubmit import RELEASE
from chisubmit.core.model import Course, Project, Student,\
    ChisubmitModelException
from chisubmit.cli.course import *
from chisubmit.cli.student import *
from chisubmit.cli.team import create_team_subparsers
from chisubmit.cli.project import create_project_subparsers
from chisubmit.cli.submit import create_submit_subparsers
from chisubmit.core import ChisubmitException
from chisubmit.common import CHISUBMIT_FAIL
from chisubmit.cli.shell import create_shell_subparsers
from chisubmit.cli.grader import create_grader_subparsers
from chisubmit.cli.gh import create_gh_subparsers

SUBCOMMANDS_NO_COURSE = ['course-create', 'course-install', 'gh-token-create']
SUBCOMMANDS_DONT_SAVE = ['course-create', 'course-install', 'course-generate-distributable', 'gh-token-create', 'shell']

            
def chisubmit_cmd(argv=None):
    if argv is None:
        argv = sys.argv[1:]
        
    # Setup argument parser
    parser = ArgumentParser(description="chisubmit")
    parser.add_argument('--config', type=str, default=None)
    parser.add_argument('--dir', type=str, default=None)
    parser.add_argument('--noop', action="store_true")
    parser.add_argument('--course', type=str, default=None)
    parser.add_argument('--verbose', action="store_true")
    parser.add_argument('--version', action='version', version="chisubmit %s" % RELEASE)
    parser.add_argument('--debug', action="store_true")

    subparsers = parser.add_subparsers(dest="subcommand")
    
    create_course_subparsers(subparsers)
    create_project_subparsers(subparsers)
    create_student_subparsers(subparsers)
    create_team_subparsers(subparsers)
    create_submit_subparsers(subparsers)
    create_grader_subparsers(subparsers)
    create_shell_subparsers(subparsers)
    create_gh_subparsers(subparsers)
    
    args = parser.parse_args(args = argv)
    
    chisubmit.core.init_chisubmit(args.dir, args.config)
    log.init_logging(args.verbose, args.debug)

    if args.subcommand not in SUBCOMMANDS_NO_COURSE:
        if args.course is not None:
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
            if args.debug:
                ce.print_exception()
            exit(CHISUBMIT_FAIL)
        except ChisubmitModelException, cme:
            print "ERROR: %s" % cme.message
            exit(CHISUBMIT_FAIL)
        except Exception, e:
            handle_unexpected_exception()

    if args.subcommand not in SUBCOMMANDS_DONT_SAVE:
        course_obj.save()

    return rc


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

import click

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
from chisubmit.cli.shell import create_shell_subparsers
from chisubmit.cli.grader import create_grader_subparsers
from chisubmit.cli.gh import create_gh_subparsers
from chisubmit.cli.admin import create_admin_subparsers
from chisubmit.cli.gradingrepo import create_gradingrepo_subparsers

SUBCOMMANDS_NO_COURSE = ['course-create', 'course-install', 'gh-token-create']
SUBCOMMANDS_DONT_SAVE = ['course-create', 'course-install', 'course-generate-distributable', 'gh-token-create', 'shell']


@click.group()      
@click.option('--config', type=str, default=None)
@click.option('--dir', type=str, default=None)
@click.option('--noop', is_flag=True)
@click.option('--course', type=str, default=None)
@click.option('--verbose', '-v', is_flag=True)
@click.option('--debug', is_flag=True)
@click.version_option(version=RELEASE)              
@click.pass_context    
def chisubmit_cmd(ctx, config, dir, noop, course, verbose, debug):
    ctx.obj = {}
    
    chisubmit.core.init_chisubmit(dir, config)
    log.init_logging(verbose, debug)

    if course is not None:
        course_specified = True
        course_id = course
        course_obj = Course.from_course_id(course)
        if course_obj is None:
            raise click.BadParameter("Course '%s' does not exist" % course)
    else:
        course_specified = False
        course_id = chisubmit.core.get_default_course()
        if course_id is None:
            course_obj = None
        else:
            course_obj = Course.from_course_id(course_id)

    ctx.obj["course_specified"] = course_specified
    ctx.obj["course_id"] = course_id
    ctx.obj["course_obj"] = course_obj

    return 0

chisubmit_cmd.add_command(course)

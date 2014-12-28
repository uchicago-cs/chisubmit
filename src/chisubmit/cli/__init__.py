
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

import click
config = None

import chisubmit.common.log as log
from chisubmit.config import Config
from chisubmit import RELEASE
from chisubmit.cli.course import course
from chisubmit.cli.student import student
from chisubmit.cli.instructor import instructor
from chisubmit.cli.team import team
from chisubmit.cli.project import project
from chisubmit.cli.submit import submit
from chisubmit.cli.shell import shell
from chisubmit.cli.grader import grader
from chisubmit.cli.gh import gh
from chisubmit.cli.admin import admin
from chisubmit.cli.user import user
from chisubmit.client import session

SUBCOMMANDS_NO_COURSE = [('course','create')]
SUBCOMMANDS_DONT_SAVE = ['course-create', 'course-install', 'course-generate-distributable', 'gh-token-create', 'shell']


@click.group()
@click.option('--conf', type=str, default=None)
@click.option('--dir', type=str, default=None)
@click.option('--noop', is_flag=True)
@click.option('--course', type=str, default=None)
@click.option('--verbose', '-v', is_flag=True)
@click.option('--debug', is_flag=True)
@click.version_option(version=RELEASE)
@click.pass_context
def chisubmit_cmd(ctx, conf, dir, noop, course, verbose, debug):
    ctx.obj = {}

    config = Config(dir, conf)
    log.init_logging(verbose, debug)

    if not config['api-key']:
        raise click.BadParameter("Sorry, can't find your chisubmit api token")

    session.connect(config['api-url'], config['api-key'])

    if course:
        course_specified = True
        course_id = course
    else:
        course_specified = False
        course_id = config['default-course']

    ctx.obj["course_specified"] = course_specified
    ctx.obj["course_id"] = course_id
    ctx.obj["config"] = config

    return 0


chisubmit_cmd.add_command(admin)


from chisubmit.cli.server import server_start, server_initdb

@click.group()
@click.option('--conf', type=str, default=None)
@click.option('--dir', type=str, default=None)
@click.option('--verbose', '-v', is_flag=True)
@click.option('--debug', is_flag=True)
@click.version_option(version=RELEASE)
@click.pass_context
def chisubmit_server_cmd(ctx, conf, dir, verbose, debug):
    ctx.obj = {}

    config = Config(dir, conf)
    log.init_logging(verbose, debug)
    
    ctx.obj["config"] = config
    
    return 0


chisubmit_server_cmd.add_command(server_start)
chisubmit_server_cmd.add_command(server_initdb)


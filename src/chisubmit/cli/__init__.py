
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
from chisubmit.common import ChisubmitException, CHISUBMIT_FAIL,\
    handle_unexpected_exception, CHISUBMIT_SUCCESS
import sys
from pprint import pprint
from requests.exceptions import HTTPError, ConnectionError
from chisubmit.cli.admin import admin
from chisubmit.cli.instructor import instructor
from chisubmit.cli.student import student
from chisubmit.cli.grader import grader
import getpass
from docutils.utils.math.math2html import URL
from chisubmit.client.requester import BadRequestException
from chisubmit.client.exceptions import UnknownObjectException,\
    ChisubmitRequestException, UnauthorizedException
from functools import update_wrapper
from chisubmit.cli.common import catch_chisubmit_exceptions
import os
from chisubmit.repos.factory import RemoteRepositoryConnectionFactory
config = None

import chisubmit.common.log as log
from chisubmit.config import Config, ConfigDirectoryNotFoundException
from chisubmit import RELEASE
from chisubmit.client import Chisubmit


VERBOSE = False
DEBUG = False 

@click.group(name="chisubmit")
@click.option('--config', '-c', type=str, multiple=True)
@click.option('--config-dir', type=str, default=None)
@click.option('--work-dir', type=str, default=None)
@click.option('--verbose', '-v', is_flag=True)
@click.option('--debug', is_flag=True)
@click.version_option(version=RELEASE)
@catch_chisubmit_exceptions
@click.pass_context
def chisubmit_cmd(ctx, config, config_dir, work_dir, verbose, debug):
    global VERBOSE, DEBUG
    
    VERBOSE = verbose
    DEBUG = debug
    
    if config_dir is None and work_dir is not None:
        print "You cannot specify --work-dir without --config-dir"
        ctx.exit(CHISUBMIT_FAIL)

    if config_dir is not None and work_dir is None:
        print "You cannot specify --config-dir without --work-dir"
        ctx.exit(CHISUBMIT_FAIL)
    
    log.init_logging(verbose, debug)

    config_overrides = {}
    for c in config:
        if c.count("=") != 1 or c[0] == "=" or c[-1] == "=":
            raise click.BadParameter("Invalid configuration parameter: {}".format(c))
        else:
            k, v = c.split("=")
            config_overrides[k] = v

    ctx.obj = {}

    ctx.obj["config_overrides"] = config_overrides
    ctx.obj["config_dir"] = config_dir
    ctx.obj["work_dir"] = work_dir
    ctx.obj["verbose"] = verbose
    ctx.obj["debug"] = debug

    return CHISUBMIT_SUCCESS

chisubmit_cmd.add_command(admin)
chisubmit_cmd.add_command(instructor)
chisubmit_cmd.add_command(student)
chisubmit_cmd.add_command(grader)


@click.command(name="init")
@click.argument('course_id', required=False)
@click.option('--username', type=str)
@click.option('--password', type=str)
@click.option('--git-username', type=str)
@click.option('--git-password', type=str)
@click.option('--force', '-f', is_flag=True)
@catch_chisubmit_exceptions
@click.pass_context
def chisubmit_init(ctx, course_id, username, password, git_username, git_password, force):
                
    if ctx.obj["config_dir"] is None and ctx.obj["work_dir"] is None:
        try:
            config = Config.get_config()
            if not force:
                in_root = os.path.normpath(config.work_dir) == os.path.normpath(os.getcwd())
                
                if in_root:
                    print "The current directory is already configured to use chisubmit."
                else:
                    print "You are already inside a directory configured to use chisubmit."
                    print "Root directory: {}".format(config.work_dir)
                print
                if in_root:
                    print "If you're sure you want to reset the configuration of this directory,"
                    print "use the --force option"
                else:
                    print "If you're sure you want to create another chisubmit directory"
                    print "in the current directory, use the --force option"
                ctx.exit(CHISUBMIT_FAIL)
        except ConfigDirectoryNotFoundException:
            pass
    else:
        if not os.path.exists(ctx.obj["work_dir"]):
            print "The specified work directory does not exist: {}".format(ctx.obj["work_dir"])
            ctx.exit(CHISUBMIT_FAIL)      

        if os.path.exists(ctx.obj["config_dir"]) and not force:
            print "The specified configuration directory already exists: {}".format(ctx.obj["config_dir"])
            print "If you're sure you want to create a configuration directory there,"
            print "use the --force option."
            ctx.exit(CHISUBMIT_FAIL)      

    
    global_config = Config.get_global_config(config_overrides = ctx.obj["config_overrides"])
    
    api_url = global_config.get_api_url()
    api_key = global_config.get_api_key()
    
    if api_url is None:
        print "The 'api-url' configuration option is not set. I need this to connect to"
        print "the chisubmit server. If your instructor did not set this option"
        print "globally, you need to specify it like this:"
        print
        print "    chisubmit -c api-url=CHISUBMIT_API_URL init"
        print
        print "Where CHISUBMIT_API_URL should be replaced with the URL of the chisubmit server."
        print "Your instructor can provide you with the correct URL."
        ctx.exit(CHISUBMIT_FAIL)
        
    if api_key is None:
        guess_user = getpass.getuser()
        
        user_prompt = "Enter your chisubmit username [{}]: ".format(guess_user)
        password_prompt = "Enter your chisubmit password: "
        
        if username is None:
            username = raw_input(user_prompt)
            if len(username.strip()) == 0:
                username = guess_user
            
        if password is None:
            password = getpass.getpass(password_prompt)
        
        client = Chisubmit(username, password=password, base_url=api_url)
        
        try:
            api_key, _ = client.get_user_token()
        except UnauthorizedException:
            print "ERROR: Incorrect username/password"
            ctx.exit(CHISUBMIT_FAIL)
    
    client = Chisubmit(api_key, base_url=api_url)
    
    if course_id is not None:
        try:
            course = client.get_course(course_id = course_id)
        except UnknownObjectException:
            print "Cannot access course '{}'".format(course_id)
            print "This could mean the course does not exist, or you have not been added to this course."            
            ctx.exit(CHISUBMIT_FAIL)
    else:
        courses = client.get_courses()
        if len(courses) == 0:
            print "You do not have access to any courses on chisubmit."
            print "This could you have not been added to any course, or no courses have been created."
            ctx.exit(CHISUBMIT_FAIL)
            
        print
        print "You are a member of the following course(s)."
        print "Please select the one you want to use:"
        print
        n = 1
        for course in courses:
            print "[{}] {}: {}".format(n, course.course_id, course.name)
            n+=1
        print
        print "[X] Exit"
        print
        valid_options = [`x` for x in range(1, len(courses)+1)] + ['X', 'x']
        option = None
        while option not in valid_options:
            option = raw_input("Choose one: ")
            if option not in valid_options:
                print "'{}' is not a valid option!".format(option)
                print
        
        if option in ['X', 'x']:
            ctx.exit(CHISUBMIT_FAIL)
        else:
            course = courses[int(option)-1]
    
    connstr = course.git_server_connstr
    
    if connstr is None or connstr == "":
        print "Error: Course '{}' doesn't seem to be configured to use a Git server." % course.id
        ctx.exit(CHISUBMIT_FAIL)
        
    conn = RemoteRepositoryConnectionFactory.create_connection(connstr, staging = False)
    server_type = conn.get_server_type_name()

    # If there are global credentials defined, see if they work
    git_credentials = global_config.get_git_credentials(server_type)
    if git_credentials is not None:
        try:
            conn.connect(git_credentials)
        except ChisubmitException:
            git_credentials = None

    # If the existing credentials didn't work, get new ones
    if git_credentials is None:
        # Try the chisubmit username/password
        git_credentials, _ = conn.get_credentials(username, password)
        
        if git_credentials is None:
            user_prompt = "Enter your {} username: ".format(server_type)
            password_prompt = "Enter your {} password: ".format(server_type)
            
            if git_username is None:
                git_username = raw_input(user_prompt)
                
            if git_password is None:
                git_password = getpass.getpass(password_prompt)
            
            git_credentials, _ = conn.get_credentials(git_username, git_password)
    
            if git_credentials is None:
                print
                print "Unable to obtain {} credentials. Incorrect username/password.".format(server_type)

    config = Config.create_config_dir(ctx.obj["config_dir"], ctx.obj["work_dir"])
    
    # Always save the API URL locally
    config.set_api_url(api_url, where = Config.LOCAL)
    
    # Save the API key only if one was not found globally
    if config.get_api_key() is None:
        config.set_api_key(api_key, where = Config.LOCAL)
        
    # Always save the course locally
    config.set_course(course.course_id, where = Config.LOCAL)
    
    # Save the git credentials only if they're not the same as the global ones
    if config.get_git_credentials(server_type) != git_credentials:
        config.set_git_credentials(server_type, git_credentials, where = Config.LOCAL)
    
    print
    print "The following directory has been set up to use chisubmit"
    print "for course '{}' ({})".format(course.course_id, course.name)
    print
    print "   " + config.work_dir
    print
    print "Remember to run chisubmit only inside this directory"
    print "(or any of its subdirectories)"
    print
    
chisubmit_cmd.add_command(chisubmit_init)        



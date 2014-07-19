
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

import chisubmit.core

from chisubmit.common.utils import create_subparser
from chisubmit.core import handle_unexpected_exception
from chisubmit.core.model import Course
from chisubmit.core.repos import GithubConnection
from chisubmit.common import CHISUBMIT_SUCCESS
from chisubmit.core import ChisubmitException
from chisubmit.cli.common import requires_course
   
    
@click.group()    
@click.pass_context
def course(ctx):
    pass
    
@click.command(name="create")
@click.option('--make-default', is_flag=True)
@click.argument('id', type=str)
@click.argument('name', type=str)
@click.argument('extensions', type=int)  
@click.pass_context  
def course_create(ctx, make_default, id, name, extensions):
    course = Course(course_id = id,
                    name = name,
                    extensions = extensions)
    
    try:
        course.course_file = chisubmit.core.get_course_filename(course.id)
        course.save()
        
        if make_default:
            chisubmit.core.set_default_course(id)
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()
        
    return CHISUBMIT_SUCCESS

@click.command(name="install")
@click.option('--make-default', is_flag=True)
@click.argument('filename', type=str)
@click.pass_context  
def course_install(ctx, make_default, filename):
    if filename.startswith("http"):
        new_course = Course.from_url(filename)
    else:
        f = open(filename)
        new_course = Course.from_file(f)
        f.close()
        
    try:
        new_course.course_file = chisubmit.core.get_course_filename(new_course.id)
        new_course.save()
        
        if make_default:
            chisubmit.core.set_default_course(new_course.id)
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()
        
    return CHISUBMIT_SUCCESS

@click.command(name="github-settings")
@click.argument('organization', type=str)
@click.pass_context  
@requires_course
def course_github_settings(ctx, organization):
    course.github_organization = organization
    
    try:
        # Try connecting to GitHub
        github_access_token = chisubmit.core.get_github_token()
        gh = GithubConnection(github_access_token, course.github_organization)
        
        # Create GitHub team to contain admins for this course
        course.github_admins_team = "%s-admins" % course.id
        gh.create_team(course.github_admins_team, [], "admin", fail_if_exists = False)    
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()
    
    return CHISUBMIT_SUCCESS

@click.command(name="git-staging-settings")
@click.argument('git_username', type=str)
@click.argument('git_hostname', type=str)
@click.pass_context
@requires_course  
def course_git_staging_settings(ctx, git_username, git_hostname):
    course.git_staging_username = git_username
    course.git_staging_hostname = git_hostname
    
    return CHISUBMIT_SUCCESS

@click.command(name="generate-distributable")
@click.argument('filename', type=str)
@click.pass_context  
@requires_course
def course_generate_distributable(ctx, filename):
    course.github_admins_team = None
    course.git_staging_username = None
    course.git_staging_hostname = None
    course.students = {}
    course.teams = {}
    
    try:
        course.save(filename)
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()
        
    return CHISUBMIT_SUCCESS

course.add_command(course_create)
course.add_command(course_install)
course.add_command(course_github_settings)
course.add_command(course_git_staging_settings)
course.add_command(course_generate_distributable)


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

from chisubmit.core import handle_unexpected_exception
from chisubmit.core.model import Course
from chisubmit.common import CHISUBMIT_SUCCESS
from chisubmit.core import ChisubmitException
from chisubmit.cli.common import pass_course
   
    
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
        new_course.save()
        
        if make_default:
            chisubmit.core.set_default_course(new_course.id)
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()
        
    return CHISUBMIT_SUCCESS

@click.command(name="git-server")
@click.argument('connection_string', type=str)
@pass_course
@click.pass_context  
def course_git_server(ctx, course, connection_string):
        
    course.git_server_connection_string = connection_string
    
    conn = course.get_git_server_connection()
    
    try:
        github_access_token = chisubmit.core.get_github_token()
        conn.connect(github_access_token)

        conn.init_course(course)
        
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()
    
    return CHISUBMIT_SUCCESS

@click.command(name="git-staging-server")
@click.argument('connection_string', type=str)
@pass_course
@click.pass_context  
def course_git_staging_server(ctx, course, connection_string):
    course.git_staging_server_connection_string = connection_string
    
    conn = course.get_git_staging_server_connection()
    
    try:
        github_access_token = chisubmit.core.get_github_token()
        conn.connect(github_access_token)

        conn.init_course(course)
        
    except ChisubmitException, ce:
        raise click.ClickException(ce.message)
    except Exception, e:
        handle_unexpected_exception()
    
    return CHISUBMIT_SUCCESS

@click.command(name="generate-distributable")
@click.argument('filename', type=str)
@pass_course
@click.pass_context  
def course_generate_distributable(ctx, course, filename):
    return CHISUBMIT_SUCCESS

course.add_command(course_create)
course.add_command(course_install)
course.add_command(course_git_server)
course.add_command(course_git_staging_server)
course.add_command(course_generate_distributable)

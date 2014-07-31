
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

from chisubmit.core.model import Student, Instructor
from chisubmit.common import CHISUBMIT_FAIL, CHISUBMIT_SUCCESS
from chisubmit.cli.common import pass_course, save_changes
from chisubmit.core import ChisubmitException, handle_unexpected_exception,\
    chisubmit_config

@click.group()    
@click.pass_context
def instructor(ctx):
    pass

@click.command(name="create")
@click.argument('id', type=str)
@click.argument('first_name', type=str)
@click.argument('last_name', type=str)
@click.argument('email', type=str)
@click.argument('git_server_id', type=str)
@click.argument('git_staging_server_id', type=str)
@pass_course
@save_changes
@click.pass_context  
def instructor_create(ctx, course, id, first_name, last_name, email, git_server_id, git_staging_server_id):
    instructor = Instructor(instructor_id = id,
                            first_name = first_name,
                            last_name = last_name,
                            email = email,
                            git_server_id = git_server_id,
                            git_staging_server_id = git_staging_server_id)
    course.add_instructor(instructor)
    
    try:    
        if course.git_server_connection_string is not None:
            conn = course.get_git_server_connection()
            server_type = conn.get_server_type_name()
            git_credentials = chisubmit_config().get_git_credentials(server_type)

            if git_credentials is None:
                print "You do not have %s credentials." % server_type
                return CHISUBMIT_FAIL    

            conn.connect(git_credentials)
            conn.update_instructors(course)
        
        if course.git_staging_server_connection_string is not None:
            conn = course.get_git_staging_server_connection()
            server_type = conn.get_server_type_name()
            git_credentials = chisubmit_config().get_git_credentials(server_type)

            if git_credentials is None:
                print "You do not have %s credentials." % server_type
                return CHISUBMIT_FAIL    

            conn.connect(git_credentials)
            conn.update_instructors(course)
            
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()
    
    
    return CHISUBMIT_SUCCESS
    

instructor.add_command(instructor_create)

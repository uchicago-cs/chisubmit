
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

from chisubmit.core.model import Student
from chisubmit.common import CHISUBMIT_FAIL, CHISUBMIT_SUCCESS
from chisubmit.cli.common import pass_course

@click.group()
@click.pass_context
def student(ctx):
    pass

@click.command(name="create")
@click.argument('id', type=str)
@click.argument('first_name', type=str)
@click.argument('last_name', type=str)
@click.argument('email', type=str)
@click.argument('git_server_id', type=str)
@pass_course
@click.pass_context
def student_create(ctx, course, id, first_name, last_name, email, git_server_id):
    student = Student(id = id,
                      first_name = first_name,
                      last_name = last_name,
                      email = email,
                      git_server_id = git_server_id)
    course.add_student(student)

    return CHISUBMIT_SUCCESS


@click.command(name="set-dropped")
@click.argument('id', type=str)
@pass_course
@click.pass_context
def student_set_dropped(ctx, course, id):
    student = course.get_student(id)
    if student is None:
        print "Student %s does not exist" % id
        return CHISUBMIT_FAIL

    student.dropped = True

    return CHISUBMIT_SUCCESS


student.add_command(student_create)
student.add_command(student_set_dropped)

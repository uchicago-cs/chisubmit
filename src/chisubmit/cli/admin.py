
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

from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
import operator
import random
from chisubmit.client.user import User
from chisubmit.client.course import Course


@click.group()
@click.pass_context
def admin(ctx):
    pass



@click.group(name="user")
@click.pass_context
def admin_user(ctx):
    pass


@click.group(name="course")
@click.pass_context
def admin_course(ctx):
    pass

@click.command(name="add")
@click.argument('user_id', type=str)
@click.argument('first_name', type=str)
@click.argument('last_name', type=str)
@click.argument('email', type=str)
@click.pass_context
def admin_user_add(ctx, user_id, first_name, last_name, email):
    user = User(id = user_id,
                first_name = first_name,
                last_name = last_name,
                email = email)

    return CHISUBMIT_SUCCESS

@click.command(name="remove")
@click.argument('user_id', type=str)
@click.pass_context
def admin_user_remove(ctx, user_id):
    # TODO
    print "NOT IMPLEMENTED"
    
    return CHISUBMIT_SUCCESS


admin.add_command(admin_user)
admin_user.add_command(admin_user_add)
admin_user.add_command(admin_user_remove)


@click.command(name="add")
@click.argument('course_id', type=str)
@click.argument('name', type=str)
@click.pass_context
def admin_course_add(ctx, course_id, name):
    course = Course(course_id = course_id,
                    name = name)
    
    course.save()

    return CHISUBMIT_SUCCESS


@click.command(name="remove")
@click.argument('course_id', type=str)
@click.pass_context
def admin_course_remove(ctx, course_id):
    print "NOT IMPLEMENTED"

    return CHISUBMIT_SUCCESS


@click.command(name="show")
@click.argument('course_id', type=str)
@click.option("--include-users", is_flag=True)
@click.option("--include-assignments", is_flag=True)
@click.pass_context
def admin_course_show(ctx, course_id, include_users, include_assignments):
    course = Course.from_course_id(course_id)
    
    print course.id, course.name
    print "Options:", course.options
    print

    if include_users:
        print "INSTRUCTORS"
        print "-----------"
        for i in course.instructors:
            print "%s: %s, %s <%s>" % (i.id, i.last_name, i.first_name, i.email)
        print
            
        print "GRADERS"
        print "-------"
        for g in course.graders:
            print "%s: %s, %s <%s>" % (g.id, g.last_name, g.first_name, g.email)
        print
        
        print "STUDENTS"
        print "--------"
        for s in course.students:
            print "%s: %s, %s <%s>" % (s.id, s.last_name, s.first_name, s.email)
        print
    
    return CHISUBMIT_SUCCESS


@click.command(name="list")
@click.pass_context
def admin_course_list(ctx):
    courses = Course.all()
    
    for course in courses:
        print course.id, course.name

    return CHISUBMIT_SUCCESS

@click.command(name="add-instructor")
@click.argument('course_id', type=str)
@click.argument('user_id', type=str)
@click.pass_context
def admin_course_add_instructor(ctx, course_id, user_id):
    course = Course.from_course_id(course_id)
    user = User.from_id(user_id)
    
    course.add_instructor(user)
    
@click.command(name="add-grader")
@click.argument('course_id', type=str)
@click.argument('user_id', type=str)
@click.pass_context
def admin_course_add_grader(ctx, course_id, user_id):
    course = Course.from_course_id(course_id)
    user = User.from_id(user_id)
    
    course.add_grader(user)
    
@click.command(name="add-student")
@click.argument('course_id', type=str)
@click.argument('user_id', type=str)
@click.pass_context
def admin_course_add_student(ctx, course_id, user_id):
    course = Course.from_course_id(course_id)
    user = User.from_id(user_id)
    
    course.add_student(user)        

admin.add_command(admin_course)
admin_course.add_command(admin_course_add)
admin_course.add_command(admin_course_remove)
admin_course.add_command(admin_course_show)
admin_course.add_command(admin_course_list)
admin_course.add_command(admin_course_add_instructor)
admin_course.add_command(admin_course_add_grader)
admin_course.add_command(admin_course_add_student)



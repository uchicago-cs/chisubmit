
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
from chisubmit.common.utils import create_connection
from chisubmit.cli.shared.course import shared_course_list,\
    shared_course_set_user_attribute
import operator
from chisubmit.client.exceptions import UnknownObjectException
from chisubmit.cli.common import get_course_or_exit, get_user_or_exit,\
    api_obj_set_attribute, get_team_or_exit


@click.group(name="course")
@click.pass_context
def admin_course(ctx):
    pass


@click.command(name="add")
@click.argument('course_id', type=str)
@click.argument('name', type=str)
@click.pass_context
def admin_course_add(ctx, course_id, name):
    try:
        course = ctx.obj["client"].get_course(course_id = course_id)
        print "ERROR: Cannot create course."
        print "       Course with course_id = %s already exists." % course_id
        ctx.exit(CHISUBMIT_FAIL)
    except UnknownObjectException, uoe:
        course = ctx.obj["client"].create_course(course_id = course_id,
                                                 name = name)
    
    return CHISUBMIT_SUCCESS


@click.command(name="remove")
@click.argument('course_id', type=str)
@click.pass_context
def admin_course_remove(ctx, course_id):
    course = get_course_or_exit(ctx, course_id)
    
    course.delete()

    return CHISUBMIT_SUCCESS


@click.command(name="show")
@click.argument('course_id', type=str)
@click.option("--include-users", is_flag=True)
@click.option("--include-assignments", is_flag=True)
@click.pass_context
def admin_course_show(ctx, course_id, include_users, include_assignments):
    course = get_course_or_exit(ctx, course_id) 
    
    print course.course_id, course.name

    if include_users:
        print
        print "INSTRUCTORS"
        print "-----------"
        for i in course.get_instructors():
            print "%s: %s, %s <%s>" % (i.user.username, i.user.last_name, i.user.first_name, i.user.email)
        print
            
        print "GRADERS"
        print "-------"
        for g in course.get_graders():
            print "%s: %s, %s <%s>" % (g.user.username, g.user.last_name, g.user.first_name, g.user.email)
        print
        
        print "STUDENTS"
        print "--------"
        for s in course.get_students():
            print "%s: %s, %s <%s>" % (s.user.username, s.user.last_name, s.user.first_name, s.user.email)
        print

    if include_assignments:
        print "ASSIGNMENTS"
        print "-----------"
        for a in course.get_assignments():
            print "%s: %s (Due: %s)" % (a.assignment_id, a.name, a.deadline)
        print

    
    return CHISUBMIT_SUCCESS




@click.command(name="add-instructor")
@click.argument('course_id', type=str)
@click.argument('user_id', type=str)
@click.pass_context
def admin_course_add_instructor(ctx, course_id, user_id):
    course = get_course_or_exit(ctx, course_id)    
    user = get_user_or_exit(ctx, user_id)    
    course.add_instructor(user)
    
@click.command(name="add-grader")
@click.argument('course_id', type=str)
@click.argument('user_id', type=str)
@click.pass_context
def admin_course_add_grader(ctx, course_id, user_id):
    course = get_course_or_exit(ctx, course_id)    
    user = get_user_or_exit(ctx, user_id)    
    course.add_grader(user)
    
@click.command(name="add-student")
@click.argument('course_id', type=str)
@click.argument('user_id', type=str)
@click.pass_context
def admin_course_add_student(ctx, course_id, user_id):
    course = get_course_or_exit(ctx, course_id)    
    user = get_user_or_exit(ctx, user_id)    
    course.add_student(user)    
    
    
@click.command(name="set-attribute")
@click.argument('course_id', type=str)
@click.argument('attr_name', type=str)
@click.argument('attr_value', type=str)
@click.pass_context
def admin_course_set_attribute(ctx, course_id, attr_name, attr_value):
    course = get_course_or_exit(ctx, course_id)
    
    api_obj_set_attribute(ctx, course, attr_name, attr_value)
    



@click.command(name="setup-repo")
@click.argument('course_id', type=str)
@click.option('--staging', is_flag=True)
@click.pass_context
def admin_course_setup_repo(ctx, course_id, staging):
    course = get_course_or_exit(ctx, course_id)   

    conn = create_connection(course, ctx.obj['config'], staging)
    
    if conn is None:
        print "Could not connect to git server."
        ctx.exit(CHISUBMIT_FAIL)

    conn.init_course(course)

    return CHISUBMIT_SUCCESS

@click.command(name="unsetup-repo")
@click.argument('course_id', type=str)
@click.option('--staging', is_flag=True)
@click.pass_context
def admin_course_unsetup_repo(ctx, course_id, staging):
    course = get_course_or_exit(ctx, course_id)

    conn = create_connection(course, ctx.obj['config'], staging)
    
    if conn is None:
        print "Could not connect to git server."
        ctx.exit(CHISUBMIT_FAIL)

    conn.deinit_course(course)

    return CHISUBMIT_SUCCESS

@click.command(name="update-repo-access")
@click.argument('course_id', type=str)
@click.option('--staging', is_flag=True)
@click.pass_context
def admin_course_update_repo_access(ctx, course_id, staging):
    course = get_course_or_exit(ctx, course_id)
    
    conn = create_connection(course, ctx.obj['config'], staging)
    
    if conn is None:
        print "Could not connect to git server."
        ctx.exit(CHISUBMIT_FAIL)
    
    conn.update_instructors(course)
    conn.update_graders(course)


@click.command(name="create-repos")
@click.argument('course_id', type=str)
@click.option('--staging', is_flag=True)
@click.pass_context
def admin_course_create_repos(ctx, course_id, staging):
    course = get_course_or_exit(ctx, course_id)

    teams = course.get_teams()

    max_len = max([len(t.id) for t in teams])

    conn = create_connection(course, ctx.obj['config'], staging)
    
    if conn is None:
        print "Could not connect to git server."
        ctx.exit(CHISUBMIT_FAIL)
    
    v = ctx.obj["verbose"]
    already_has_repository = 0
    warning = 0
    created = 0
    for team in sorted(teams, key=operator.attrgetter("id")):
        if not team.is_complete():
            warning += 1
            print "%-*s  WARNING. Team registration is incomplete." % (max_len, team.id)
            continue
        
        if conn.exists_team_repository(course, team):
            already_has_repository += 1
            if v: print "%-*s  SKIPPING. Already has a repository." % (max_len, team.id)
            continue

        if not staging:        
            students = [s for s in course.students if s.user.id in [ts.user.id for ts in team.students]]
                
            missing = []
            for s in students:
                if not hasattr(s, "repo_info") or s.repo_info is None or not s.repo_info.has_key("git-username"):
                    missing.append(s.user.id)
                    
            if len(missing) > 0:
                warning += 1
                print "%-20s WARNING. These students haven't set their git usernames: %s" % (team.id, ",".join(missing))
                continue
        
        try:
            conn.create_team_repository(course, team)
            created += 1
            print "%-20s CREATED" % team.id
        except Exception, e:
            print "%-20s Unexpected exception %s: %s" % (team.id, e.__class__.__name__, e.message)

    print
    print "Existing: %i" % already_has_repository
    print "Created : %i" % created
    print "Warnings: %i" % warning

    return CHISUBMIT_SUCCESS


@click.command(name="team-repo-create")
@click.argument('course_id', type=str)
@click.argument('team_id', type=str)
@click.option('--ignore-existing', is_flag=True)
@click.option('--public', is_flag=True)
@click.option('--staging', is_flag=True)
@click.pass_context
def admin_course_team_repo_create(ctx, course_id, team_id, ignore_existing, public, staging):
    course = get_course_or_exit(ctx, course_id) 
    team = get_team_or_exit(ctx, course, team_id) 

    conn = create_connection(course, ctx.obj['config'], staging)
    
    if conn is None:
        print "Could not connect to git server."
        ctx.exit(CHISUBMIT_FAIL)
    
    if conn.exists_team_repository(course, team) and not ignore_existing:
        print "Team %s already has a repository" % team_id
        ctx.exit(CHISUBMIT_FAIL)
    else:
        conn.create_team_repository(course, team, fail_if_exists = not ignore_existing, private = not public)

    return CHISUBMIT_SUCCESS


@click.command(name="team-repo-update")
@click.argument('course_id', type=str)
@click.argument('team_id', type=str)
@click.pass_context
def admin_course_team_repo_update(ctx, course_id, team_id):
    course = get_course_or_exit(ctx, course_id) 
    team = get_team_or_exit(ctx, course, team_id) 

    #if team.github_repo is None:
    #    print "Team %s does not have a repository." % team.id
    #    return CHISUBMIT_FAIL

    conn = create_connection(course, ctx.obj['config'], staging = False)
    
    if conn is None:
        print "Could not connect to git server."
        ctx.exit(CHISUBMIT_FAIL)

    conn.update_team_repository(course, team)
    return CHISUBMIT_SUCCESS


@click.command(name="team-repo-remove")
@click.argument('course_id', type=str)
@click.argument('team_id', type=str)
@click.option('--ignore-non-existing', is_flag=True)
@click.option('--staging', is_flag=True)
@click.pass_context
def admin_course_team_repo_remove(ctx, course_id, team_id, ignore_non_existing, staging):
    course = get_course_or_exit(ctx, course_id) 
    team = get_team_or_exit(ctx, course, team_id) 

    conn = create_connection(course, ctx.obj['config'], staging)
    
    if conn is None:
        print "Could not connect to git server."
        ctx.exit(CHISUBMIT_FAIL)

    if not conn.exists_team_repository(course, team) and not ignore_non_existing:
        print "WARNING: Cannot delete repository because it doesn't exist"
        ctx.exit(CHISUBMIT_FAIL)
    else:
        conn.delete_team_repository(course, team, fail_if_not_exists = not ignore_non_existing)

    return CHISUBMIT_SUCCESS


admin_course.add_command(shared_course_list)
admin_course.add_command(shared_course_set_user_attribute)

admin_course.add_command(admin_course_add)
admin_course.add_command(admin_course_remove)
admin_course.add_command(admin_course_show)
admin_course.add_command(admin_course_add_instructor)
admin_course.add_command(admin_course_add_grader)
admin_course.add_command(admin_course_add_student)
admin_course.add_command(admin_course_set_attribute)
admin_course.add_command(admin_course_setup_repo)
admin_course.add_command(admin_course_unsetup_repo)
admin_course.add_command(admin_course_update_repo_access)
admin_course.add_command(admin_course_create_repos)
admin_course.add_command(admin_course_team_repo_create)
admin_course.add_command(admin_course_team_repo_update)
admin_course.add_command(admin_course_team_repo_remove)



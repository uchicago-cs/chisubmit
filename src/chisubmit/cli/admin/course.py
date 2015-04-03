
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
from chisubmit.client.user import User
from chisubmit.client.course import Course
from chisubmit.common.utils import create_connection
from chisubmit.cli.shared.course import shared_course_list
import operator
import csv

@click.group(name="course")
@click.pass_context
def admin_course(ctx):
    pass


@click.command(name="add")
@click.argument('course_id', type=str)
@click.argument('name', type=str)
@click.pass_context
def admin_course_add(ctx, course_id, name):
    course = Course(id = course_id,
                    name = name)
    
    return CHISUBMIT_SUCCESS


@click.command(name="remove")
@click.argument('course_id', type=str)
@click.pass_context
def admin_course_remove(ctx, course_id):
    course = Course.from_id(course_id)
    if course is None:
        print "Course %s does not exist" % course_id
        ctx.exit(CHISUBMIT_FAIL)    
    
    print "NOT IMPLEMENTED"

    return CHISUBMIT_SUCCESS


@click.command(name="show")
@click.argument('course_id', type=str)
@click.option("--include-users", is_flag=True)
@click.option("--include-assignments", is_flag=True)
@click.pass_context
def admin_course_show(ctx, course_id, include_users, include_assignments):
    course = Course.from_id(course_id)
    if course is None:
        print "Course %s does not exist" % course_id
        ctx.exit(CHISUBMIT_FAIL)    
    
    print course.id, course.name
    if len(course.options) == 0:
        print "No options"
    else:
        print "Options"
        for name, value in course.options.items():
            print "  %s: %s" % (name, value)
    print

    if include_users:
        print "INSTRUCTORS"
        print "-----------"
        for i in course.instructors:
            print "%s: %s, %s <%s>" % (i.user.id, i.user.last_name, i.user.first_name, i.user.email)
        print
            
        print "GRADERS"
        print "-------"
        for g in course.graders:
            print "%s: %s, %s <%s>" % (g.user.id, g.user.last_name, g.user.first_name, g.user.email)
        print
        
        print "STUDENTS"
        print "--------"
        for s in course.students:
            print "%s: %s, %s <%s>" % (s.user.id, s.user.last_name, s.user.first_name, s.user.email)
        print

    if include_assignments:
        print "ASSIGNMENTS"
        print "-----------"
        for a in course.assignments:
            print "%s: %s (Due: %s)" % (a.id, a.name, a.deadline)
        print

    
    return CHISUBMIT_SUCCESS




@click.command(name="add-instructor")
@click.argument('course_id', type=str)
@click.argument('user_id', type=str)
@click.pass_context
def admin_course_add_instructor(ctx, course_id, user_id):
    course = Course.from_id(course_id)
    if course is None:
        print "Course %s does not exist" % course_id
        ctx.exit(CHISUBMIT_FAIL)    
    
    user = User.from_id(user_id)
    if course is None:
        print "User %s does not exist" % user_id
        ctx.exit(CHISUBMIT_FAIL)    
    
    course.add_instructor(user)
    
@click.command(name="add-grader")
@click.argument('course_id', type=str)
@click.argument('user_id', type=str)
@click.pass_context
def admin_course_add_grader(ctx, course_id, user_id):
    course = Course.from_id(course_id)
    if course is None:
        print "Course %s does not exist" % course_id
        ctx.exit(CHISUBMIT_FAIL)    

    user = User.from_id(user_id)
    if course is None:
        print "User %s does not exist" % user_id
        ctx.exit(CHISUBMIT_FAIL)    
    
    course.add_grader(user)
    
@click.command(name="add-student")
@click.argument('course_id', type=str)
@click.argument('user_id', type=str)
@click.pass_context
def admin_course_add_student(ctx, course_id, user_id):
    course = Course.from_id(course_id)
    if course is None:
        print "Course %s does not exist" % course_id
        ctx.exit(CHISUBMIT_FAIL)    

    user = User.from_id(user_id)
    if course is None:
        print "User %s does not exist" % user_id
        ctx.exit(CHISUBMIT_FAIL)    
    
    course.add_student(user)  
    
    
@click.command(name="load-students")
@click.argument('course_id', type=str)
@click.argument('csv_file', type=click.File('rb'))
@click.argument('csv_userid_column', type=str)
@click.argument('csv_fname_column', type=str)
@click.argument('csv_lname_column', type=str)
@click.argument('csv_email_column', type=str)
@click.option('--dry-run', is_flag=True)
@click.option('--id-from-email', is_flag=True)
@click.pass_context
def admin_course_load_students(ctx, course_id, csv_file, csv_userid_column, csv_fname_column, csv_lname_column, csv_email_column, dry_run, id_from_email):   
    course = Course.from_id(course_id)
    if course is None:
        print "Course %s does not exist" % course_id
        ctx.exit(CHISUBMIT_FAIL)   
                
    csvf = csv.DictReader(csv_file)
            
    for col in (csv_userid_column, csv_fname_column, csv_lname_column, csv_email_column):
        if col not in csvf.fieldnames:
            print "CSV file %s does not have a '%s' column" % (csv_file, col)
            ctx.exit(CHISUBMIT_FAIL)
        
    for entry in csvf:
        user_id = entry[csv_userid_column]
        if id_from_email:
            user_id = user_id.split("@")[0].strip()
        
        first_name = entry[csv_fname_column]
        last_name = entry[csv_lname_column]
        email = entry[csv_email_column]

        print "Processing %s (%s, %s)" % (user_id, last_name, first_name)

        user = User.from_id(user_id)
    
        if user is not None:
            print "- User %s already exists." % user_id
        else:
            print "- Creating user %s" % user_id
            if not dry_run:
                user = User(id = user_id,
                            first_name = first_name,
                            last_name = last_name,
                            email = email)
        
        student = course.get_student(user_id)
        if student is not None:
            print "- User %s is already a student in %s" % (user_id, course_id)
        else:
            print "- Adding %s to %s" % (user_id, course_id)
            if not dry_run:
                course.add_student(user)
        
        print 
    
@click.command(name="set-option")
@click.argument('course_id', type=str)
@click.argument('option_name', type=str)
@click.argument('option_value', type=str)
@click.pass_context
def admin_course_set_option(ctx, course_id, option_name, option_value):
    course = Course.from_id(course_id)
    if course is None:
        print "Course %s does not exist" % course_id
        ctx.exit(CHISUBMIT_FAIL)    

    course.set_option(option_name, option_value)


@click.command(name="setup-repo")
@click.argument('course_id', type=str)
@click.option('--staging', is_flag=True)
@click.pass_context
def admin_course_setup_repo(ctx, course_id, staging):
    course = Course.from_id(course_id)
    if course is None:
        print "Course %s does not exist" % course_id
        ctx.exit(CHISUBMIT_FAIL)    

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
    course = Course.from_id(course_id)
    if course is None:
        print "Course %s does not exist" % course_id
        ctx.exit(CHISUBMIT_FAIL)    

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
    course = Course.from_id(course_id)
    if course is None:
        print "Course %s does not exist" % course_id
        ctx.exit(CHISUBMIT_FAIL)    
    
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
    course = Course.from_id(course_id)
    if course is None:
        print "Course %s does not exist" % course_id
        ctx.exit(CHISUBMIT_FAIL)    

    teams = course.get_teams()

    if len(teams) == 0:
        print "Course %s has no teams. No repositories to create." % course_id
        ctx.exit(CHISUBMIT_FAIL)  

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
    course = Course.from_id(course_id)
    if course is None:
        print "Course %s does not exist" % course_id
        ctx.exit(CHISUBMIT_FAIL)    

    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        ctx.exit(CHISUBMIT_FAIL)

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
    course = Course.from_id(course_id)
    if course is None:
        print "Course %s does not exist" % course_id
        ctx.exit(CHISUBMIT_FAIL)    

    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        ctx.exit(CHISUBMIT_FAIL)

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
    course = Course.from_id(course_id)
    if course is None:
        print "Course %s does not exist" % course_id
        ctx.exit(CHISUBMIT_FAIL)    

    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        ctx.exit(CHISUBMIT_FAIL)

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


admin_course.add_command(admin_course_add)
admin_course.add_command(admin_course_remove)
admin_course.add_command(admin_course_show)
admin_course.add_command(admin_course_add_instructor)
admin_course.add_command(admin_course_add_grader)
admin_course.add_command(admin_course_add_student)
admin_course.add_command(admin_course_load_students)
admin_course.add_command(admin_course_set_option)
admin_course.add_command(admin_course_setup_repo)
admin_course.add_command(admin_course_unsetup_repo)
admin_course.add_command(admin_course_update_repo_access)
admin_course.add_command(admin_course_create_repos)
admin_course.add_command(admin_course_team_repo_create)
admin_course.add_command(admin_course_team_repo_update)
admin_course.add_command(admin_course_team_repo_remove)



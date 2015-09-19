
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

from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL,\
    ChisubmitException
from chisubmit.common.utils import create_connection
from chisubmit.cli.shared.course import shared_course_list,\
    shared_course_set_user_attribute
import operator
from chisubmit.client.exceptions import UnknownObjectException
from chisubmit.cli.common import get_course_or_exit, get_user_or_exit,\
    api_obj_set_attribute, get_team_or_exit, catch_chisubmit_exceptions,\
    require_config, get_student_or_exit
import csv


@click.group(name="course")
@click.pass_context
def admin_course(ctx):
    pass


@click.command(name="add")
@click.argument('course_id', type=str)
@click.argument('name', type=str)
@catch_chisubmit_exceptions
@require_config
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
@catch_chisubmit_exceptions
@require_config
@click.pass_context
def admin_course_remove(ctx, course_id):
    course = get_course_or_exit(ctx, course_id)
    
    course.delete()

    return CHISUBMIT_SUCCESS


@click.command(name="show")
@click.argument('course_id', type=str)
@click.option("--include-users", is_flag=True)
@click.option("--include-assignments", is_flag=True)
@catch_chisubmit_exceptions
@require_config
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
@catch_chisubmit_exceptions
@require_config
@click.pass_context
def admin_course_add_instructor(ctx, course_id, user_id):
    course = get_course_or_exit(ctx, course_id)    
    user = get_user_or_exit(ctx, user_id)    
    course.add_instructor(user)
    
@click.command(name="add-grader")
@click.argument('course_id', type=str)
@click.argument('user_id', type=str)
@catch_chisubmit_exceptions
@require_config
@click.pass_context
def admin_course_add_grader(ctx, course_id, user_id):
    course = get_course_or_exit(ctx, course_id)    
    user = get_user_or_exit(ctx, user_id)    
    course.add_grader(user)
    
@click.command(name="add-student")
@click.argument('course_id', type=str)
@click.argument('user_id', type=str)
@catch_chisubmit_exceptions
@require_config
@click.pass_context
def admin_course_add_student(ctx, course_id, user_id):
    course = get_course_or_exit(ctx, course_id)    
    user = get_user_or_exit(ctx, user_id)    
    course.add_student(user)    
    
    
VALID_USER_TYPES = ['student', 'grader', 'instructor']    
    
@click.command(name="load-users")
@click.argument('course_id', type=str)
@click.argument('csv_file', type=click.File('rb'))
@click.argument('csv_username_column', type=str)
@click.argument('csv_fname_column', type=str)
@click.argument('csv_lname_column', type=str)
@click.argument('csv_email_column', type=str)
@click.option('--dry-run', is_flag=True)
@click.option('--sync', is_flag=True)
@click.option('--user-type', type=click.Choice(VALID_USER_TYPES + ['column']))
@click.option('--user-type-column', type=str)
@click.option('--id-from-email', is_flag=True)
@require_config
@click.pass_context
def admin_course_load_users(ctx, course_id, csv_file, csv_username_column, csv_fname_column, csv_lname_column, csv_email_column,
                                 dry_run, sync, user_type, user_type_column, id_from_email):   
    course = get_course_or_exit(ctx, course_id)    
                
    if user_type == "column" and user_type_column is None:
        print "You must specify a column with --user-type-column when using '--user-type column'"
        ctx.exit(CHISUBMIT_FAIL)
                
    csvf = csv.DictReader(csv_file)
            
    columns = [csv_username_column, csv_fname_column, csv_lname_column, csv_email_column]
    
    if user_type == "column":
        columns.append(user_type_column)
            
    for col in columns:
        if col not in csvf.fieldnames:
            print "CSV file %s does not have a '%s' column" % (csv_file, col)
            ctx.exit(CHISUBMIT_FAIL)
        
    student_usernames = set()
        
    for entry in csvf:
        username = entry[csv_username_column]
        
        if id_from_email:
            username = username.split("@")[0].strip()
        
        first_name = entry[csv_fname_column]
        last_name = entry[csv_lname_column]
        email = entry[csv_email_column]
        
        print "Processing %s (%s, %s)" % (username, last_name, first_name)        
        
        if user_type == "column":
            cur_user_type = entry[user_type_column]
            if cur_user_type not in VALID_USER_TYPES:
                print "- User %s has invalid user type '%s'." % (username, cur_user_type)
                continue
        else:
            cur_user_type = user_type

        if cur_user_type == "student":
            student_usernames.add(username)

        try:
            user = ctx.obj["client"].get_user(username = username)
            print "- User %s already exists." % username
        except UnknownObjectException, uoe:
            print "- Creating user %s" % username
            if not dry_run:
                user = ctx.obj["client"].create_user(username = username,
                                                     first_name = first_name,
                                                     last_name = last_name,
                                                     email = email)
        
        if cur_user_type == "student":
            try:
                student = course.get_student(username)
                if not student.dropped:
                    print "- User %s is already a student in %s" % (username, course_id)
                else:
                    if not dry_run:
                        student.dropped = False
                    print "- Student had previously been marked as dropped, has been un-dropped"
            except UnknownObjectException, uoe:
                print "- Adding student %s to %s" % (username, course_id)
                if not dry_run:
                    course.add_student(user)
        elif cur_user_type == "instructor":
            try:
                instructor = course.get_instructor(username)
                print "- User %s is already an instructor in %s" % (username, course_id)
            except UnknownObjectException, uoe:
                print "- Adding instructor %s to %s" % (username, course_id)
                if not dry_run:
                    course.add_instructor(user)
        elif cur_user_type == "grader":
            try:
                grader = course.get_grader(username)
                print "- User %s is already a grader in %s" % (username, course_id)
            except UnknownObjectException, uoe:
                print "- Adding grader %s to %s" % (username, course_id)
                if not dry_run:
                    course.add_grader(user)
            
        print 
    
    if sync:
        existing_students = course.get_students()
        for existing_student in existing_students:
            if existing_student.username not in student_usernames:
                if not dry_run:
                    existing_student.dropped = True
                print "Dropped %s" % existing_student.username
        

@click.command(name="create-git-users")
@click.argument('course_id', type=str)
@click.option('--staging', is_flag=True)
@click.option('--dry-run', is_flag=True)
@click.option('--all-types', is_flag=True)
@click.option('--only-type', type=click.Choice(VALID_USER_TYPES), required = False)
@require_config
@click.pass_context
def admin_course_create_git_users(ctx, course_id, staging, dry_run, all_types, only_type):   
    course = get_course_or_exit(ctx, course_id)    
                
    if all_types and only_type is not None:
        print "You cannot specify both --all-types and --only-type"
        ctx.exit(CHISUBMIT_FAIL)
        
    if staging and only_type == "student":
        print "You cannot create student accounts on the staging server."
        ctx.exit(CHISUBMIT_FAIL)
          
    conn = create_connection(course, ctx.obj['config'], staging)          
          
    users = []
    
    if not staging and (all_types or only_type == "student"):
        users += course.get_students()

    if all_types or only_type == "grader":
        users += course.get_graders()

    if all_types or only_type == "instructor":
        users += course.get_instructors()

    for user in users:
        if conn.exists_user(course, user):
            print "[SKIP] User '%s' already exists" % user.username
        else:
            if dry_run:
                print "[OK] Created user %s" % user.username
            else:
                try:
                    conn.create_user(course, user)
                    print "[OK] Created user %s" % user.username
                except ChisubmitException, ce:
                    print "[ERROR] Couldn't create user '%s': %s" % (user.username, ce.message)
    
@click.command(name="create-individual-teams")
@click.argument('course_id', type=str)
@click.option('--dry-run', is_flag=True)
@click.option('--only', type=str)
@require_config
@click.pass_context
def admin_course_create_individual_teams(ctx, course_id, dry_run, only):      
    course = get_course_or_exit(ctx, course_id)    

    if only is not None:
        students = [get_student_or_exit(ctx, course, only)]
    else:
        students = course.get_students()
        
    
    for student in students:
        print "Processing %s (%s, %s)" % (student.username, student.user.last_name, student.user.first_name)        

        try:
            team = course.get_team(student.username)

            tms = team.get_team_members()
            if len(tms) == 0:
                # Incomplete team creation
                if not dry_run:
                    team.add_team_member(student.username, confirmed = True)
                print "- Added user %s to team %s." % (student.username, team.team_id)
            elif len(tms) == 1 and tms[0].username == student.username:
                print "- User %s already has an individual team." % student.username
            else:
                print "- ERROR: Team '%s' exists but it has these team members: %s" % (team.team_id, [tm.username for tm in tms])
            
        except UnknownObjectException, uoe:
            if not dry_run:
                team = course.create_team(student.username)
                team.add_team_member(student.username, confirmed = True)
            print "- Created individual team for user %s." % student.username
            
        print
        
        
            
    
@click.command(name="set-attribute")
@click.argument('course_id', type=str)
@click.argument('attr_name', type=str)
@click.argument('attr_value', type=str)
@catch_chisubmit_exceptions
@require_config
@click.pass_context
def admin_course_set_attribute(ctx, course_id, attr_name, attr_value):
    course = get_course_or_exit(ctx, course_id)
    
    api_obj_set_attribute(ctx, course, attr_name, attr_value)
    



@click.command(name="setup-repo")
@click.argument('course_id', type=str)
@click.option('--staging', is_flag=True)
@catch_chisubmit_exceptions
@require_config
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
@catch_chisubmit_exceptions
@require_config
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
@catch_chisubmit_exceptions
@require_config
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
@catch_chisubmit_exceptions
@require_config
@click.pass_context
def admin_course_create_repos(ctx, course_id, staging):
    course = get_course_or_exit(ctx, course_id)

    teams = course.get_teams()

    if len(teams) == 0:
        print "Course %s has no teams. No repositories to create." % course_id
        ctx.exit(CHISUBMIT_FAIL)  

    max_len = max([len(t.team_id) for t in teams])

    conn = create_connection(course, ctx.obj['config'], staging)
    
    if conn is None:
        print "Could not connect to git server."
        ctx.exit(CHISUBMIT_FAIL)
    
    v = ctx.obj["verbose"]
    already_has_repository = 0
    warning = 0
    created = 0
    for team in sorted(teams, key=operator.attrgetter("team_id")):
        if conn.exists_team_repository(course, team):
            already_has_repository += 1
            if v: print "%-*s  SKIPPING. Already has a repository." % (max_len, team.team_id)
            continue

        team_members = team.get_team_members()
        unconfirmed_students = [tm for tm in team_members if not tm.confirmed]
        
        if len(unconfirmed_students) > 0:
            usernames = [tm.student.username for tm in unconfirmed_students]
            warning += 1
            print "%-*s  WARNING. Team has unconfirmed students: %s" % (max_len, team.team_id, ",".join(usernames))
            continue


        if not staging:        
            missing = []
            for tm in team_members:
                if course.git_usernames == "custom":
                    if tm.student.git_username is None:
                        missing.append(tm.student.username)
                    
            if len(missing) > 0:
                warning += 1
                print "%-20s WARNING. These students haven't set their git usernames: %s" % (team.id, ",".join(missing))
                continue
        
        try:
            conn.create_team_repository(course, team)
            created += 1
            print "%-20s CREATED" % team.team_id
        except Exception, e:
            print "%-20s Unexpected exception %s: %s" % (team.team_id, e.__class__.__name__, e.message)

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
@catch_chisubmit_exceptions
@require_config
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
@catch_chisubmit_exceptions
@require_config
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
@catch_chisubmit_exceptions
@require_config
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
admin_course.add_command(admin_course_load_users)
admin_course.add_command(admin_course_create_git_users)
admin_course.add_command(admin_course_create_individual_teams)
admin_course.add_command(admin_course_set_attribute)
admin_course.add_command(admin_course_setup_repo)
admin_course.add_command(admin_course_unsetup_repo)
admin_course.add_command(admin_course_update_repo_access)
admin_course.add_command(admin_course_create_repos)
admin_course.add_command(admin_course_team_repo_create)
admin_course.add_command(admin_course_team_repo_update)
admin_course.add_command(admin_course_team_repo_remove)



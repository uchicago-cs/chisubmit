
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

from chisubmit.core import chisubmit_config

from chisubmit.core.model import Team
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.core import ChisubmitException, handle_unexpected_exception
from chisubmit.cli.common import pass_course, save_changes
import os.path
import smtplib
from string import Template
import random
import pprint


@click.group()    
@click.pass_context
def team(ctx):
    pass


@click.command(name="create")
@click.argument('team_id', type=str)
@pass_course
@save_changes
@click.pass_context  
def team_create(ctx, course, team_id):
    team = Team(team_id = team_id)
    course.add_team(team)
        
    return CHISUBMIT_SUCCESS


@click.command(name="list")
@click.option('--ids', is_flag=True)
@pass_course
@save_changes
@click.pass_context  
def team_list(ctx, course, ids):
    team_ids = course.teams.keys()
    team_ids.sort()
    
    for team_id in team_ids:
        if ids:
            print team_id
        else:
            team = course.teams[team_id]
            
            fields = [team.id, `team.active`]
                        
            print "\t".join(fields)

    return CHISUBMIT_SUCCESS


@click.command(name="show")
@click.option('--search', is_flag=True)
@click.option('--verbose', is_flag=True)
@click.argument('team_id', type=str)
@pass_course
@save_changes
@click.pass_context  
def team_show(ctx, course, search, verbose, team_id):
    if not search:
        team = course.get_team(team_id)
        if team is None:
            print "Team %s does not exist" % team_id
            return CHISUBMIT_FAIL       
        
        teams = [team]
    else:
        teams = course.search_team(team_id)

    pp = pprint.PrettyPrinter(indent=4, depth=6)
    
    for t in teams:
        tdict = dict(vars(t))
        if verbose:
            tdict["projects"] = dict(tdict["projects"])
            for p in tdict["projects"]:
                tdict["projects"][p] = vars(tdict["projects"][p])
               
            tdict["students"] = [vars(s) for s in tdict["students"]]
            
        pp.pprint(tdict)
    
    return CHISUBMIT_SUCCESS


@click.command(name="student-add")
@click.argument('team_id', type=str)
@click.argument('student_id', type=str)
@pass_course
@save_changes
@click.pass_context  
def team_student_add(ctx, course, team_id, student_id):
    student = course.get_student(student_id)
    if student is None:
        print "Student %s does not exist" % student_id
        return CHISUBMIT_FAIL
    
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        return CHISUBMIT_FAIL       
    
    team.add_student(student)   

    return CHISUBMIT_SUCCESS

    
@click.command(name="project-add")    
@click.argument('team_id', type=str)
@click.argument('project_id', type=str)    
@pass_course
@save_changes
@click.pass_context  
def team_project_add(ctx, course, team_id, project_id):
    project = course.get_project(project_id)
    if project is None:
        print "Project %s does not exist" % project_id
        return CHISUBMIT_FAIL    
    
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        return CHISUBMIT_FAIL
    
    if team.projects.has_key(project.id):
        print "Team %s has already been assigned project %s"  % (team.id, project.id)
        return CHISUBMIT_FAIL
    
    team.add_project(project)                

    return CHISUBMIT_SUCCESS


@click.command(name="project-set-grade")
@click.argument('team_id', type=str)
@click.argument('project_id', type=str)
@click.argument('grade_component', type=str)
@click.argument('grade', type=float)
@pass_course
@save_changes
@click.pass_context  
def team_project_set_grade(ctx, course, team_id, project_id, grade_component, grade):
    project = course.get_project(project_id)
    if project is None:
        print "Project %s does not exist" % project_id
        return CHISUBMIT_FAIL    
    
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        return CHISUBMIT_FAIL
    
    grade_component = project.get_grade_component(grade_component)
    if grade_component is None:
        print "Project %s does not have a grade component '%s'" % (project.id, grade_component)
        return CHISUBMIT_FAIL
    
    team.set_project_grade(project.id, grade_component, grade)


@click.command(name="set-private-name")
@click.argument('team_id', type=str)
@click.argument('private_name', type=str)
@pass_course
@save_changes
@click.pass_context  
def team_set_private_name(ctx, course, team_id, private_name):
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        return CHISUBMIT_FAIL

    team.private_name = private_name
    
    
@click.command(name="repo-create")
@click.argument('team_id', type=str)
@click.option('--ignore-existing', is_flag=True)
@click.option('--public', is_flag=True)
@click.option('--staging', is_flag=True)
@pass_course
@save_changes
@click.pass_context  
def team_repo_create(ctx, course, team_id, ignore_existing, public, staging):
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        return CHISUBMIT_FAIL

    if team.git_repo_created and not ignore_existing:
        print "Repository for team %s has already been created." % team.id
        print "Maybe you meant to run team-repo-update?"
        return CHISUBMIT_FAIL     
    
    try:
        if staging:
            conn = course.get_git_staging_server_connection()
            team_access = False
        else:
            conn = course.get_git_server_connection()
            team_access = True

        server_type = conn.get_server_type_name()
        git_credentials = chisubmit_config().get_git_credentials(server_type)
    
        if git_credentials is None:
            print "You do not have %s credentials." % server_type
            return CHISUBMIT_FAIL    
            
        conn.connect(git_credentials)
            
        conn.create_team_repository(course, team, team_access, fail_if_exists = not ignore_existing, private = not public)
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()
        
    if staging:
        team.git_repo_created = True
    else:
        team.git_staging_repo_created = True
        
    return CHISUBMIT_SUCCESS


@click.command(name="repo-update")
@click.argument('team_id', type=str)    
@pass_course
@save_changes
@click.pass_context  
def team_repo_update(ctx, course, team_id):
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        return CHISUBMIT_FAIL
    
    if team.github_repo is None:
        print "Team %s does not have a repository." % team.id
        return CHISUBMIT_FAIL

    conn = course.get_git_server_connection()
    server_type = conn.get_server_type_name()
    git_credentials = chisubmit_config().get_git_credentials(server_type)

    if git_credentials is None:
        print "You do not have %s credentials." % server_type
        return CHISUBMIT_FAIL    
        
    try:
        conn.connect(git_credentials)
        conn.update_team_repository(team)    
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()

    return CHISUBMIT_SUCCESS

    
@click.command(name="repo-remove")    
@click.argument('team_id', type=str)    
@click.option('--staging', is_flag=True)    
@pass_course
@save_changes
@click.pass_context  
def team_repo_remove(ctx, course, team_id, staging):
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        return CHISUBMIT_FAIL
    
    if team.github_repo is None:
        print "Team %s does not have a repository." % team.id
        return CHISUBMIT_FAIL
        
    try:
        if staging:
            conn = course.get_git_staging_server_connection()
        else:
            conn = course.get_git_server_connection()
        
        server_type = conn.get_server_type_name()
        git_credentials = chisubmit_config().get_git_credentials(server_type)
    
        if git_credentials is None:
            print "You do not have %s credentials." % server_type
            return CHISUBMIT_FAIL    
            
        conn.connect(git_credentials)

        conn.delete_team_repository(team)
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()

    return CHISUBMIT_SUCCESS


@click.command(name="repo-check")
@click.argument('team_id', type=str)    
@pass_course
@save_changes
@click.pass_context  
def team_repo_check(ctx, course, team_id):
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        return CHISUBMIT_FAIL
    
    if not team.git_repo_created:
        print "Team %s does not have a repository." % team.id
        return CHISUBMIT_FAIL

    conn = course.get_git_server_connection()
    server_type = conn.get_server_type_name()
    git_credentials = chisubmit_config().get_git_credentials(server_type)

    if git_credentials is None:
        print "You do not have %s credentials." % server_type
        return CHISUBMIT_FAIL    
        
    try:
        conn.connect(git_credentials)
    except ChisubmitException, ce:
        print "Unable to connect to GitHub: %s" % ce.message
        return CHISUBMIT_FAIL
        
    if not conn.exists_team_repository(course, team):
        print "The repository '%s' does not exist or you do not have permission to access it." % team.github_repo
        return CHISUBMIT_FAIL

    # TODO: Check that the user actually has push access
    print "Your repository exists and you have access to it."
    print "Repository website: %s" % conn.get_repository_http_url(course, team)
    print "Repository URL: %s" % conn.get_repository_git_url(course, team)

    return CHISUBMIT_SUCCESS


@click.command(name="repo-email")
@click.argument('team_id', type=str)
@click.argument('email_from', type=str)
@click.argument('template', type=str)
@click.option('--force', is_flag=True)
@click.option('--dry-run', is_flag=True)
@pass_course
@save_changes
@click.pass_context  
def team_repo_email(ctx, course, team_id, email_from, template, force, dry_run):
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        return CHISUBMIT_FAIL
    
    if team.github_email_sent and not force:
        print "E-mail to team %s has already been sent. Use --force to send anyways." % team.id
        return CHISUBMIT_FAIL
    
    if team.github_repo is None:
        print "Team %s does not have a repository." % team.id
        return CHISUBMIT_FAIL

    if not os.path.exists(template):
        print "File %s does not exists"
        return CHISUBMIT_FAIL
       
    # Commenting this out for now, since the e-mail functionality is eventually
    # going to be implemented from scratch
    smtp_server = None #smtplib.SMTP(chisubmit.core.chisubmit_conf.get("smtp", "server"))
    email_template = Template(open(template).read()) 
    email_to = ["%s %s <%s>" % (s.first_name, s.last_name, s.email) for s in team.students]
    email_rcpt = [s.email for s in team.students] + [email_from]
    github_repo = "https://github.com/%s/%s" % (course.github_organization, team.github_repo)
    email_message = email_template.substitute(sender = email_from, 
                                              recipients = ", ".join(email_to), 
                                              subject = "New GitHub repository: %s" % team.github_repo, 
                                              github_repo = github_repo)
    
    if not dry_run:
        smtp_server.sendmail(email_from, email_rcpt, email_message)
        team.github_email_sent = True
        print "E-mail sent to team %s" % team.id
    else:
        print "Dry run requested. This is the message that would have been sent:"
        print
        print email_message
        
        
team.add_command(team_create)
team.add_command(team_list)
team.add_command(team_show)
team.add_command(team_student_add)
team.add_command(team_project_add)
team.add_command(team_project_set_grade)
team.add_command(team_set_private_name)
team.add_command(team_repo_create)
team.add_command(team_repo_update)
team.add_command(team_repo_remove)
team.add_command(team_repo_check)
team.add_command(team_repo_email)        

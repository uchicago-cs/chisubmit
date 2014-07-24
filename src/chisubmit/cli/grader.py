
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
from chisubmit.core.model import Grader
from chisubmit.cli.common import create_grading_repos,\
    gradingrepo_push_grading_branch, gradingrepo_pull_grading_branch, get_teams
from chisubmit.repos.grading import GradingGitRepo
from chisubmit.core.rubric import RubricFile, ChisubmitRubricException
from chisubmit.cli.common import pass_course, save_changes
import os.path
from chisubmit.core import ChisubmitException, handle_unexpected_exception,\
    chisubmit_config

@click.group()    
@click.pass_context
def grader(ctx):
    pass

@click.command(name="create")
@click.argument('grader_id', type=str)
@click.argument('first_name', type=str)
@click.argument('last_name', type=str)
@click.argument('email', type=str)
@click.argument('git_server_id', type=str)
@click.argument('git_staging_server_id', type=str)
@pass_course
@save_changes
@click.pass_context  
def grader_create(ctx, course, grader_id, first_name, last_name, email, git_server_id, git_staging_server_id):
    grader = Grader(grader_id = grader_id,
                    first_name = first_name,
                    last_name = last_name,
                    email = email,
                    git_server_id = git_server_id,
                    git_staging_server_id = git_staging_server_id)
    course.add_grader(grader)
    
    try:    
        if course.git_server_connection_string is not None:
            conn = course.get_git_server_connection()
            server_type = conn.get_server_type_name()
            git_credentials = chisubmit_config().get_git_credentials(server_type)

            if git_credentials is None:
                print "You do not have %s credentials." % server_type
                return CHISUBMIT_FAIL    

            conn.connect(git_credentials)
            conn.update_graders(course)
        
        if course.git_staging_server_connection_string is not None:
            conn = course.get_git_staging_server_connection()
            server_type = conn.get_server_type_name()
            git_credentials = chisubmit_config().get_git_credentials(server_type)

            if git_credentials is None:
                print "You do not have %s credentials." % server_type
                return CHISUBMIT_FAIL    

            conn.connect(git_credentials)
            conn.update_graders(course)
            
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()
    
    
    return CHISUBMIT_SUCCESS


@click.command(name="add-conflict")
@click.argument('grader_id', type=str)
@click.argument('student_id', type=str)
@pass_course
@save_changes
@click.pass_context  
def grader_add_conflict(ctx, course, grader_id, student_id):
    grader = course.get_grader(grader_id)
    if grader is None:
        print "Grader %s does not exist" % grader_id
        return CHISUBMIT_FAIL
    
    student = course.get_student(student_id)
    if student is None:
        print "Student %s does not exist" % student_id
        return CHISUBMIT_FAIL
    
    if student in grader.conflicts:
        print "Student %s is already listed as a conflict for grader %s" % (student.id, grader.id)

    grader.conflicts.append(student)
    
    return CHISUBMIT_SUCCESS


@click.command(name="create-grading-repos")
@click.argument('grader_id', type=str)
@click.argument('project_id', type=str)
@pass_course
@save_changes
@click.pass_context  
def grader_create_grading_repos(ctx, course, grader_id, project_id):
    grader = course.get_grader(grader_id)
    if grader is None:
        print "Grader %s does not exist" % grader_id
        return CHISUBMIT_FAIL
        
    project = course.get_project(project_id)
    if project is None:
        print "Project %s does not exist"
        return CHISUBMIT_FAIL

    teams = get_teams(course, project, grader = grader)
    
    if teams is None:
        print "No teams found"
        return CHISUBMIT_FAIL
    
    repos = create_grading_repos(course, project, teams, grader = grader)
    
    if repos is None:
        return CHISUBMIT_FAIL
    
    for repo in repos:
        repo.set_grader_author()
        
    for team in teams:
        print "Pulling grading branch for team %s... " % team.id
        gradingrepo_pull_grading_branch(course, team, project, staging = True)

    return CHISUBMIT_SUCCESS


@click.command(name="validate-rubric")
@click.argument('team_id', type=str)
@click.argument('project_id', type=str)
@pass_course
@save_changes
@click.pass_context  
def grader_validate_rubric(ctx, course, team_id, project_id):
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist"
        return CHISUBMIT_FAIL
        
    project = course.get_project(project_id)
    if project is None:
        print "Project %s does not exist"
        return CHISUBMIT_FAIL

    repo = GradingGitRepo.get_grading_repo(course, team, project)
    if repo is None:    
        print "Repository for %s does not exist" % (team.id)
        return CHISUBMIT_FAIL
        
    rubricfile = repo.repo_path + "/%s.rubric.txt" % project.id
    
    if not os.path.exists(rubricfile):
        print "Repository for %s does not exist have a rubric for project %s" % (team.id, project.id)
        return CHISUBMIT_FAIL
    
    try:
        RubricFile.from_file(open(rubricfile), project)
    except ChisubmitRubricException, cre:
        print "Error in rubric: %s" % cre.message
        return CHISUBMIT_FAIL
        
    print "Rubric OK."
    
    return CHISUBMIT_SUCCESS
                
                
@click.command(name="push-grading-branch")                
@click.argument('grader_id', type=str)
@click.argument('project_id', type=str)    
@click.option('--only', type=str)    
@pass_course
@save_changes
@click.pass_context  
def grader_push_grading_branch(ctx, course, grader_id, project_id, only):
    grader = course.get_grader(grader_id)
    if grader is None:
        print "Grader %s does not exist" % grader_id
        return CHISUBMIT_FAIL
    
    project = course.get_project(project_id)
    if project is None:
        print "Project %s does not exist"
        return CHISUBMIT_FAIL
    
    teams = get_teams(course, project, grader = grader, only = only)
    
    if teams is None:
        return CHISUBMIT_FAIL
        
    for team in teams:
        print "Pushing grading branch for team %s... " % team.id
        gradingrepo_push_grading_branch(course, team, project, staging = True)
    
    return CHISUBMIT_SUCCESS

@click.command(name="pull-grading-branch")
@click.argument('grader_id', type=str)
@click.argument('project_id', type=str)    
@click.option('--only', type=str)    
@pass_course
@save_changes
@click.pass_context  
def grader_pull_grading_branch(ctx, course, grader_id, project_id, only):
    grader = course.get_grader(grader_id)
    if grader is None:
        print "Grader %s does not exist" % grader_id
        return CHISUBMIT_FAIL
    
    project = course.get_project(project_id)
    if project is None:
        print "Project %s does not exist"
        return CHISUBMIT_FAIL
    
    teams = get_teams(course, project, grader = grader, only = only)
    
    if teams is None:
        return CHISUBMIT_FAIL
        
    for team in teams:
        print "Pulling grading branch for team %s... " % team.id
        gradingrepo_pull_grading_branch(course, team, project, staging = True)

    return CHISUBMIT_SUCCESS


grader.add_command(grader_create)
grader.add_command(grader_add_conflict)
grader.add_command(grader_create_grading_repos)
grader.add_command(grader_validate_rubric)
grader.add_command(grader_push_grading_branch)
grader.add_command(grader_pull_grading_branch)
                

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

from chisubmit.common.utils import create_subparser
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.core.model import Grader
from chisubmit.cli.common import create_grading_repos,\
    gradingrepo_push_grading_branch, gradingrepo_pull_grading_branch, get_teams
from chisubmit.core.repos import GradingGitRepo
from chisubmit.core.rubric import RubricFile, ChisubmitRubricException
import os.path

def create_grader_subparsers(subparsers):
    subparser = create_subparser(subparsers, "grader-create", cli_do__grader_create)
    subparser.add_argument('id', type=str)
    subparser.add_argument('first_name', type=str)
    subparser.add_argument('last_name', type=str)
    subparser.add_argument('email', type=str)
    subparser.add_argument('github_id', type=str)

    subparser = create_subparser(subparsers, "grader-add-conflict", cli_do__grader_add_conflict)
    subparser.add_argument('grader_id', type=str)
    subparser.add_argument('student_id', type=str)
    
    subparser = create_subparser(subparsers, "grader-create-grading-repos", cli_do__grader_create_grading_repos)
    subparser.add_argument('grader_id', type=str)
    subparser.add_argument('project_id', type=str)
    
    subparser = create_subparser(subparsers, "grader-validate-rubric", cli_do__grader_validate_rubric)
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('project_id', type=str)
    
    subparser = create_subparser(subparsers, "grader-pull-grading-branches", cli_do__grader_pull_grading_branch)
    subparser.add_argument('grader_id', type=str)
    subparser.add_argument('project_id', type=str)    
    subparser.add_argument('--only', type=str)    

    subparser = create_subparser(subparsers, "grader-push-grading-branches", cli_do__grader_push_grading_branch)
    subparser.add_argument('grader_id', type=str)
    subparser.add_argument('project_id', type=str)    
    subparser.add_argument('--only', type=str)    


def cli_do__grader_create(course, args):
    grader = Grader(grader_id = args.id,
                    first_name = args.first_name,
                    last_name = args.last_name,
                    email = args.email,
                    github_id = args.github_id)
    course.add_grader(grader)
    
    return CHISUBMIT_SUCCESS

def cli_do__grader_add_conflict(course, args):
    grader = course.get_grader(args.grader_id)
    if grader is None:
        print "Grader %s does not exist" % args.grader_id
        return CHISUBMIT_FAIL
    
    student = course.get_student(args.student_id)
    if student is None:
        print "Student %s does not exist" % args.student_id
        return CHISUBMIT_FAIL
    
    if student in grader.conflicts:
        print "Student %s is already listed as a conflict for grader %s" % (student.id, grader.id)

    grader.conflicts.append(student)
    
    return CHISUBMIT_SUCCESS

def cli_do__grader_create_grading_repos(course, args):
    grader = course.get_grader(args.grader_id)
    if grader is None:
        print "Grader %s does not exist" % args.grader_id
        return CHISUBMIT_FAIL
        
    project = course.get_project(args.project_id)
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



def cli_do__grader_validate_rubric(course, args):
    team = course.get_team(args.team_id)
    if team is None:
        print "Team %s does not exist"
        return CHISUBMIT_FAIL
        
    project = course.get_project(args.project_id)
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
                
                

def cli_do__grader_push_grading_branch(course, args):
    grader = course.get_grader(args.grader_id)
    if grader is None:
        print "Grader %s does not exist" % args.grader_id
        return CHISUBMIT_FAIL
    
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist"
        return CHISUBMIT_FAIL
    
    teams = get_teams(course, project, grader = grader, only = args.only)
    
    if teams is None:
        return CHISUBMIT_FAIL
        
    for team in teams:
        print "Pushing grading branch for team %s... " % team.id
        gradingrepo_push_grading_branch(course, team, project, staging = True)
    
    return CHISUBMIT_SUCCESS


def cli_do__grader_pull_grading_branch(course, args):
    grader = course.get_grader(args.grader_id)
    if grader is None:
        print "Grader %s does not exist" % args.grader_id
        return CHISUBMIT_FAIL
    
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist"
        return CHISUBMIT_FAIL
    
    teams = get_teams(course, project, grader = grader, only = args.only)
    
    if teams is None:
        return CHISUBMIT_FAIL
        
    for team in teams:
        print "Pulling grading branch for team %s... " % team.id
        gradingrepo_pull_grading_branch(course, team, project, staging = True)

    return CHISUBMIT_SUCCESS

                
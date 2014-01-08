
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
from chisubmit.core.repos import GradingGitRepo
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.core import ChisubmitException, handle_unexpected_exception

def create_grader_subparsers(subparsers):
    subparser = create_subparser(subparsers, "grader-sync-grading-repo", cli_do__grader_sync_grading_repo)
    subparser.add_argument('team_id', type=str)

    subparser = create_subparser(subparsers, "grader-create-grading-branch", cli_do__grader_create_grading_branch)
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('project_id', type=str)

    subparser = create_subparser(subparsers, "grader-push-grading-branch", cli_do__grader_push_grading_branch)
    subparser.add_argument('--staging', action="store_true")
    subparser.add_argument('--github', action="store_true")
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('project_id', type=str)

    subparser = create_subparser(subparsers, "grader-pull-grading-branch", cli_do__grader_pull_grading_branch)
    subparser.add_argument('--staging', action="store_true")
    subparser.add_argument('--github', action="store_true")
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('project_id', type=str)


def cli_do__grader_sync_grading_repo(course, args):
    team = course.get_team(args.team_id)
    if team is None:
        print "Team %s does not exist" % args.team_id
        return CHISUBMIT_FAIL
    
    try:
        repo = GradingGitRepo.get_grading_repo(course, team)
        
        if repo is None:
            repo = GradingGitRepo.create_grading_repo(course, team)
        else:
            repo.sync()
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()

    return CHISUBMIT_SUCCESS

        
def cli_do__grader_create_grading_branch(course, args):
    team = course.get_team(args.team_id)
    if team is None:
        print "Team %s does not exist"
        return CHISUBMIT_FAIL
    
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist"
        return CHISUBMIT_FAIL
    
    try:
        repo = GradingGitRepo.get_grading_repo(course, team)
        
        if repo is None:
            print "%s does not have a grading repository" % team.id
            return CHISUBMIT_FAIL
        
        repo.create_grading_branch(project)
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()

    return CHISUBMIT_SUCCESS


def cli_do__grader_push_grading_branch(course, args):
    team = course.get_team(args.team_id)
    if team is None:
        print "Team %s does not exist"
        return CHISUBMIT_FAIL
    
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist"
        return CHISUBMIT_FAIL
    
    try:    
        repo = GradingGitRepo.get_grading_repo(course, team)
        
        if repo is None:
            print "%s does not have a grading repository" % team.id
            return CHISUBMIT_FAIL
            
        if args.github:
            repo.push_grading_branch_to_github(project)
            
        if args.staging:
            repo.push_grading_branch_to_staging(project)
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()

    return CHISUBMIT_SUCCESS

def cli_do__grader_pull_grading_branch(course, args):
    team = course.get_team(args.team_id)
    if team is None:
        print "Team %s does not exist"
        return CHISUBMIT_FAIL
    
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist"
        return CHISUBMIT_FAIL
    
    try:
        repo = GradingGitRepo.get_grading_repo(course, team)
        
        if repo is None:
            print "%s does not have a grading repository" % team.id
            return CHISUBMIT_FAIL
        
        if args.github:
            repo.pull_grading_branch_from_github(project)
        
        if args.staging:
            repo.pull_grading_branch_from_staging(project)
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()
        
    return CHISUBMIT_SUCCESS
                
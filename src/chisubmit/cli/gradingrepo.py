
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
from chisubmit.core.rubric import RubricFile, ChisubmitRubricException
import os.path
from chisubmit.cli.common import gradingrepo_push_grading_branch,\
    gradingrepo_pull_grading_branch

def create_gradingrepo_subparsers(subparsers):
    subparser = create_subparser(subparsers, "gradingrepo-push-grading-branch", cli_do__gradingrepo_push_grading_branch)
    subparser.add_argument('--staging', action="store_true")
    subparser.add_argument('--github', action="store_true")
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('project_id', type=str)

    subparser = create_subparser(subparsers, "gradingrepo-pull-grading-branch", cli_do__gradingrepo_pull_grading_branch)
    subparser.add_argument('--staging', action="store_true")
    subparser.add_argument('--github', action="store_true")
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('project_id', type=str)


def cli_do__gradingrepo_push_grading_branch(course, args):
    team = course.get_team(args.team_id)
    if team is None:
        print "Team %s does not exist"
        return CHISUBMIT_FAIL
    
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist"
        return CHISUBMIT_FAIL
    
    return gradingrepo_push_grading_branch(course, team, project, args.github, args.staging)

def cli_do__gradingrepo_pull_grading_branch(course, args):
    team = course.get_team(args.team_id)
    if team is None:
        print "Team %s does not exist"
        return CHISUBMIT_FAIL
    
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist"
        return CHISUBMIT_FAIL
    
    return gradingrepo_pull_grading_branch(course, team, project, args.github, args.staging)
                
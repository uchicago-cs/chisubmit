
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

import chisubmit.core

from chisubmit.common.utils import create_subparser
from chisubmit.core.model import Team
from chisubmit.core.repos import GithubConnection
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.core import ChisubmitException, handle_unexpected_exception
import os.path
import smtplib
from string import Template

def create_team_subparsers(subparsers):
    subparser = create_subparser(subparsers, "team-create", cli_do__team_create)
    subparser.add_argument('team_id', type=str)

    subparser = create_subparser(subparsers, "team-list", cli_do__team_list)
    subparser.add_argument('--ids', action="store_true")
    
    subparser = create_subparser(subparsers, "team-student-add", cli_do__team_student_add)
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('student_id', type=str)

    subparser = create_subparser(subparsers, "team-project-add", cli_do__team_project_add)
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('project_id', type=str)
    
    subparser = create_subparser(subparsers, "team-gh-repo-create", cli_do__team_gh_repo_create)
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('--ignore-existing', action="store_true", dest="ignore_existing")
    
    subparser = create_subparser(subparsers, "team-gh-repo-update", cli_do__team_gh_repo_update)
    subparser.add_argument('team_id', type=str)    

    subparser = create_subparser(subparsers, "team-gh-repo-remove", cli_do__team_gh_repo_remove)
    subparser.add_argument('team_id', type=str)

    subparser = create_subparser(subparsers, "team-gh-repo-check", cli_do__team_gh_repo_check)
    subparser.add_argument('team_id', type=str)

    subparser = create_subparser(subparsers, "team-gh-repo-set", cli_do__team_gh_repo_set)
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('github_repo', type=str)

    subparser = create_subparser(subparsers, "team-gh-repo-email", cli_do__team_gh_repo_email)
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('email_from', type=str)
    subparser.add_argument('template', type=str)
    subparser.add_argument('--force', action="store_true")
    subparser.add_argument('--dry-run', action="store_true")


def cli_do__team_create(course, args):
    team = Team(team_id = args.team_id)
    course.add_team(team)
        
    return CHISUBMIT_SUCCESS

def cli_do__team_list(course, args):
    team_ids = course.teams.keys()
    team_ids.sort()
    
    for team_id in team_ids:
        if args.ids:
            print team_id
        else:
            team = course.teams[team_id]
            
            fields = [team.id, `team.active`, team.github_repo, team.github_team, `team.github_email_sent`]
                        
            print "\t".join(fields)

    return CHISUBMIT_SUCCESS

    
def cli_do__team_student_add(course, args):
    student = course.get_student(args.student_id)
    if student is None:
        print "Student %s does not exist" % args.student_id
        return CHISUBMIT_FAIL
    
    team = course.get_team(args.team_id)
    if team is None:
        print "Team %s does not exist" % args.team_id
        return CHISUBMIT_FAIL       
    
    team.add_student(student)   

    return CHISUBMIT_SUCCESS

    
def cli_do__team_project_add(course, args):
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist" % args.project_id
        return CHISUBMIT_FAIL    
    
    team = course.get_team(args.team_id)
    if team is None:
        print "Team %s does not exist"
        return CHISUBMIT_FAIL
    
    team.add_project(project)                

    return CHISUBMIT_SUCCESS

    
def cli_do__team_gh_repo_create(course, args):
    team = course.get_team(args.team_id)
    if team is None:
        print "Team %s does not exist" % args.team_id
        return CHISUBMIT_FAIL

    if team.github_repo is not None and not args.ignore_existing:
        print "Repository for team %s has already been created." % team.id
        print "Maybe you meant to run team-repo-update?"
        return CHISUBMIT_FAIL

    github_access_token = chisubmit.core.get_github_token()

    if github_access_token is None:
        print "You have not created a GitHub access token."
        print "You can create one using 'chisubmit gh-token-create'"
        return CHISUBMIT_FAIL    
    
    try:
        gh = GithubConnection(github_access_token, course.github_organization)
            
        gh.create_team_repository(course, team, fail_if_exists = not args.ignore_existing)
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()
        
    return CHISUBMIT_SUCCESS

    
def cli_do__team_gh_repo_update(course, args):
    team = course.get_team(args.team_id)
    if team is None:
        print "Team %s does not exist" % args.team_id
        return CHISUBMIT_FAIL
    
    if team.github_repo is None:
        print "Team %s does not have a repository." % team.id
        return CHISUBMIT_FAIL

    github_access_token = chisubmit.core.get_github_token()

    if github_access_token is None:
        print "You have not created a GitHub access token."
        print "You can create one using 'chisubmit gh-token-create'"
        return CHISUBMIT_FAIL    
    
    try:    
        gh = GithubConnection(github_access_token, course.github_organization)
        gh.update_team_repository(team)    
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()

    return CHISUBMIT_SUCCESS

    
def cli_do__team_gh_repo_remove(course, args):
    team = course.get_team(args.team_id)
    if team is None:
        print "Team %s does not exist" % args.team_id
        return CHISUBMIT_FAIL
    
    if team.github_repo is None:
        print "Team %s does not have a repository." % team.id
        return CHISUBMIT_FAIL

    github_access_token = chisubmit.core.get_github_delete_token()
    
    if github_access_token is None:
        print "No GitHub access token with delete permissions found."
        print "You can create one with 'chisubmit gh-token-create --delete"
        return CHISUBMIT_FAIL
        
    try:
        gh = GithubConnection(github_access_token, course.github_organization)
        gh.delete_team_repository(team)
    except ChisubmitException, ce:
        raise ce # Propagate upwards, it will be handled by chisubmit_cmd
    except Exception, e:
        handle_unexpected_exception()

    return CHISUBMIT_SUCCESS

def cli_do__team_gh_repo_check(course, args):
    team = course.get_team(args.team_id)
    if team is None:
        print "Team %s does not exist" % args.team_id
        return CHISUBMIT_FAIL
    
    if team.github_repo is None:
        print "Team %s does not have a repository." % team.id
        return CHISUBMIT_FAIL

    github_access_token = chisubmit.core.get_github_token()

    if github_access_token is None:
        print "You have not created a GitHub access token."
        print "You can create one using 'chisubmit gh-token-create'"
        return CHISUBMIT_FAIL    
        
    try:
        gh = GithubConnection(github_access_token, course.github_organization)
    except ChisubmitException, ce:
        print "Unable to connect to GitHub: %s" % ce.message
        return CHISUBMIT_FAIL
        
    if not gh.repository_exists(team.github_repo):
        print "The repository '%s' does not exist or you do not have permission to access it." % team.github_repo
        return CHISUBMIT_FAIL

    # TODO: Check that the user actually has push access
    print "Repository '%s' exists and you have access to it." % team.github_repo
    print "GitHub URL: https://github.com/%s/%s" % (course.github_organization, team.github_repo)

    return CHISUBMIT_SUCCESS

def cli_do__team_gh_repo_set(course, args):
    team = course.get_team(args.team_id)
    if team is None:
        print "Team %s does not exist" % args.team_id
        return CHISUBMIT_FAIL
    
    team.github_repo = args.github_repo
    
    return CHISUBMIT_SUCCESS


def cli_do__team_gh_repo_email(course, args):
    team = course.get_team(args.team_id)
    if team is None:
        print "Team %s does not exist" % args.team_id
        return CHISUBMIT_FAIL
    
    if team.github_email_sent and not args.force:
        print "E-mail to team %s has already been sent. Use --force to send anyways." % team.id
        return CHISUBMIT_FAIL
    
    if team.github_repo is None:
        print "Team %s does not have a repository." % team.id
        return CHISUBMIT_FAIL

    if not os.path.exists(args.template):
        print "File %s does not exists"
        return CHISUBMIT_FAIL
       
    smtp_server = smtplib.SMTP(chisubmit.core.chisubmit_conf.get("smtp", "server"))
    email_template = Template(open(args.template).read()) 
    email_to = ["%s %s <%s>" % (s.first_name, s.last_name, s.email) for s in team.students]
    email_rcpt = [s.email for s in team.students] + [args.email_from]
    github_repo = "https://github.com/%s/%s" % (course.github_organization, team.github_repo)
    email_message = email_template.substitute(sender = args.email_from, 
                                              recipients = ", ".join(email_to), 
                                              subject = "New GitHub repository: %s" % team.github_repo, 
                                              github_repo = github_repo)
    
    if not args.dry_run:
        smtp_server.sendmail(args.email_from, email_rcpt, email_message)
        team.github_email_sent = True
        print "E-mail sent to team %s" % team.id
    else:
        print "Dry run requested. This is the message that would have been sent:"
        print
        print email_message
        

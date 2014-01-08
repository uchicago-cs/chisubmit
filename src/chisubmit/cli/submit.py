
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

from chisubmit.common.utils import create_subparser, set_datetime_timezone_utc, convert_timezone_to_local
from chisubmit.core.repos import GithubConnection
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.core import ChisubmitException

def create_submit_subparsers(subparsers):
    subparser = create_subparser(subparsers, "team-project-submit", cli_do__team_project_submit)
    subparser.add_argument('team_id', type=str)    
    subparser.add_argument('project_id', type=str)
    subparser.add_argument('commit', type=str)
    subparser.add_argument('extensions', type=int, default=0)
    subparser.add_argument('--force', action="store_true")
    subparser.add_argument('--yes', action="store_true")
    subparser.add_argument('--ignore-extensions', action="store_true", dest="ignore_extensions")
    
    
def cli_do__team_project_submit(course, args):
    project = course.get_project(args.project_id)
    if project is None:
        print "Project %s does not exist" % args.project_id
        return CHISUBMIT_FAIL
    
    team = course.get_team(args.team_id)
    if team is None:
        print "Team %s does not exist" % args.team_id
        return CHISUBMIT_FAIL
    
    extensions_requested = args.extensions
    
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

    commit = gh.get_commit(team, args.commit)
    
    if commit is None:
        print "Commit %s does not exist in repository" % commit
        return CHISUBMIT_FAIL
        
    commit_time_utc = set_datetime_timezone_utc(commit.commit.author.date)
    commit_time_local = convert_timezone_to_local(commit_time_utc)
    
    deadline_utc = project.get_deadline()
    deadline_local = convert_timezone_to_local(deadline_utc)
        
    extensions_needed = project.extensions_needed(commit_time_utc)
    
    extensions_bad = False
    if extensions_requested < extensions_needed:
        print
        print "The number of extensions you have requested is insufficient."
        print
        print "     Deadline (UTC): %s" % deadline_utc.isoformat()
        print "       Commit (UTC): %s" % commit_time_utc.isoformat()
        print 
        print "   Deadline (Local): %s" % deadline_local.isoformat()
        print "     Commit (Local): %s" % commit_time_local.isoformat()
        print 
        print "You need to request %s extensions." % extensions_needed
        extensions_bad = True
    elif extensions_requested > extensions_needed:
        print        
        print "The number of extensions you have requested is excessive."
        print
        print "     Deadline (UTC): %s" % deadline_utc.isoformat()
        print "       Commit (UTC): %s" % commit_time_utc.isoformat()
        print 
        print "   Deadline (Local): %s" % deadline_local.isoformat()
        print "     Commit (Local): %s" % commit_time_local.isoformat()
        print 
        print "You only need to request %s extensions." % extensions_needed
        extensions_bad = True

    if not args.ignore_extensions and extensions_bad:
        print
        print "You can use the --ignore-extensions option to submit regardless, but"
        print "you should get permission from the instructor before you do so."
        print
        return CHISUBMIT_FAIL
    elif args.ignore_extensions and extensions_bad:
        print
        print "WARNING: You are forcing a submission with an incorrect number"
        print "of extensions. Make sure you have approval from the instructor"
        print "to do this."
        
    tag_name = project.id
    submission_tag = gh.get_submission_tag(team, tag_name)
    
    if submission_tag is not None and not args.force:
        submission_commit = gh.get_commit(team, submission_tag.object.sha)
        print        
        print "Submission tag '%s' already exists" % tag_name
        print "It points to commit %s (%s)" % (submission_commit.commit.sha, submission_commit.commit.message)
        print "If you want to override this submission, please use the --force option"
        return CHISUBMIT_FAIL
    elif submission_tag is not None and args.force:
        submission_commit = gh.get_commit(team, submission_tag.object.sha)
        print
        print "WARNING: Submission tag '%s' already exists" % tag_name
        print "It currently points to commit %s...: %s" % (submission_commit.commit.sha[:8], submission_commit.commit.message)
        print "Make sure you want to overwrite the previous submission tag."
        
    print
    print "You are going to tag your code for %s as ready to grade." % project.name
    print "The commit you are submitting is the following:"
    print
    print "      Commit: %s" % commit.commit.sha
    print "        Date: %s" % commit.commit.author.date.isoformat()
    print "     Message: %s" % commit.commit.message
    print "      Author: %s <%s>" % (commit.commit.author.name, commit.commit.author.email)
    if not extensions_bad:
        print
        print "The number of extensions you are requesting (%i) is acceptable." % args.extensions
        print "Please note that this program does not check how many extensions"
        print "you have left. It only checks whether the number of extensions is"
        print "correct given the deadline for the project."
    
    print
    print "Are you sure you want to continue? (y/n): ", 
    
    if not args.yes:
        yesno = raw_input()
    else:
        yesno = 'y'
        print 'y'
    
    if yesno in ('y', 'Y', 'yes', 'Yes', 'YES'):
        message = "Extensions requested: %i\n" % args.extensions
        message += "Extensions needed: %i\n" % extensions_needed
        if extensions_bad:
            message += "Extensions bad: yes\n"
            
        if submission_tag is None:
            gh.create_submission_tag(team, tag_name, message, commit.commit.sha)
        else:
            gh.update_submission_tag(team, tag_name, message, commit.commit.sha)
            
        print
        print "Your submission has been completed."
        #print "You can use 'chisubmit team-project-submission-verify' to double-check"
        #print "that your code was correctly tagged as ready to grade."
        
    return CHISUBMIT_SUCCESS

        
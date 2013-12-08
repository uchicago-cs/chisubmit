import chisubmit.core

from chisubmit.common.utils import create_subparser, set_datetime_timezone_utc, convert_timezone_to_local
from chisubmit.core.repos import GithubConnection
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL

def create_submit_subparsers(subparsers):
    subparser = create_subparser(subparsers, "team-project-submit", cli_do__team_project_submit)
    subparser.add_argument('team_id', type=str)    
    subparser.add_argument('project_id', type=str)
    subparser.add_argument('commit', type=str)
    subparser.add_argument('extensions', type=int, default=0)
    subparser.add_argument('--force', action="store_true")
    subparser.add_argument('--ignore-extensions', action="store_true", dest="ignore_extensions")
    
    
def cli_do__team_project_submit(course, args):
    project = course.projects[args.project_id]
    team = course.teams[args.team_id]
    team_project = team.projects[args.project_id]
    
    extensions_requested = args.extensions
    
    github_access_token = chisubmit.core.chisubmit_conf.get("github", "access-token")
    gh = GithubConnection(github_access_token, course.github_organization)
    
    commit = gh.get_commit(team, args.commit)
    
    if commit is None:
        print "Commit %s does not exist in repository" % commit
        return CHISUBMIT_FAIL
        
    commit_time_utc = set_datetime_timezone_utc(commit.commit.author.date)
    commit_time_local = convert_timezone_to_local(commit_time_utc)
        
    extensions_needed = project.extensions_needed(commit_time_local)
    
    extensions_bad = False
    if extensions_requested < extensions_needed:
        print
        print "The number of extensions you have requested is insufficient."
        print
        print "   Deadline: %s" % project.deadline.isoformat()
        print "     Commit: %s" % commit_time_local.isoformat()
        print 
        print "You need to request %s extensions." % extensions_needed
        extensions_bad = True
    elif extensions_requested > extensions_needed:
        print        
        print "The number of extensions you have requested is excessive."
        print
        print "   Deadline: %s" % project.deadline.isoformat()
        print "     Commit: %s" % commit_time_local.isoformat()
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
    yesno = raw_input()
    
    if yesno in ('y', 'Y', 'yes', 'Yes', 'YES'):
        message = "Extensions requested: %i\n" % args.extensions
        message += "Extensions needed: %i\n" % extensions_needed
        if extensions_bad:
            message += "Extensions bad: yes\n"
            
        if submission_tag is None:
            gh.create_submission_tag(team, tag_name, message, commit.commit.sha)
        else:
            pass
            gh.update_submission_tag(team, tag_name, message, commit.commit.sha)
            
        print
        print "Your submission has been completed."
        print "You can use 'chisubmit team-project-submission-verify' to double-check"
        print "that your code was correctly tagged as ready to grade."
        
    return CHISUBMIT_SUCCESS

        
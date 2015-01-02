import click
from chisubmit.cli.common import pass_course
from chisubmit.client.assignment import Assignment
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.repos.factory import RemoteRepositoryConnectionFactory
from chisubmit.common.utils import convert_datetime_to_utc, convert_datetime_to_local
import pytz
from dateutil.parser import parse

@click.group()
@click.pass_context
def student(ctx):
    pass


@click.command(name="register-for-assignment")
@click.argument('assignment_id', type=str)
@click.option('--team-name', type=str)
@click.option('--partner', type=str, multiple=True)
@pass_course
@click.pass_context
def student_assignment_register(ctx, course, assignment_id, team_name, partner):
    a = Assignment.from_course_and_id(course.id, assignment_id)
        
    a.register(team_name = team_name,
               partners = partner)
    
    return CHISUBMIT_SUCCESS

@click.command(name="repo-check")
@click.argument('team_id', type=str)
@pass_course
@click.pass_context
def student_repo_check(ctx, course, team_id):
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist or you do not have access to it" % team_id
        ctx.exit(CHISUBMIT_FAIL)
    
    #if not team.git_repo_created:
    #    print "Team %s does not have a repository." % team.id
    #    return CHISUBMIT_FAIL

    connstr = course.options["git-server-connstr"]

    conn = RemoteRepositoryConnectionFactory.create_connection(connstr)
    server_type = conn.get_server_type_name()
    git_credentials = ctx.obj['config']['git-credentials'].get(server_type, None)

    if git_credentials is None:
        print "You do not have %s credentials." % server_type
        return CHISUBMIT_FAIL

    conn.connect(git_credentials)

    if not conn.exists_team_repository(course, team):
        print "The repository '%s' does not exist or you do not have permission to access it." % team.github_repo
        return CHISUBMIT_FAIL

    # TODO: Check that the user actually has push access
    print "Your repository exists and you have access to it."
    http_url = conn.get_repository_http_url(course, team)
    if http_url is not None:
        print "Repository website: %s" % conn.get_repository_http_url(course, team)
    print "Repository URL: %s" % conn.get_repository_git_url(course, team)

    return CHISUBMIT_SUCCESS

@click.command(name="set-git-username")
@click.argument('username', type=str)
@pass_course
@click.pass_context
def student_set_git_username(ctx, course, username):
    course.set_student_repo_option(None, "git-username", username)
    

def print_commit(commit):
    print "      Commit: %s" % commit.sha
    print "        Date: %s" % commit.committed_date.isoformat(sep=" ")
    print "     Message: %s" % commit.message
    print "      Author: %s <%s>" % (commit.author_name, commit.author_email)        


@click.command(name="submit-assignment")
@click.argument('team_id', type=str)    
@click.argument('assignment_id', type=str)
@click.argument('commit_sha', type=str)
@click.option('--extensions', type=int, default=0)
@click.option('--force', is_flag=True)
@click.option('--yes', is_flag=True)
@pass_course
@click.pass_context  
def student_assignment_submit(ctx, course, team_id, assignment_id, commit_sha, extensions, force, yes):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        return CHISUBMIT_FAIL
    
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        return CHISUBMIT_FAIL
    
    extensions_requested = extensions
    
    conn = RemoteRepositoryConnectionFactory.create_connection(course.options["git-server-connstr"])
    server_type = conn.get_server_type_name()
    git_credentials = ctx.obj['config']['git-credentials'].get(server_type, None)

    if git_credentials is None:
        print "You do not have %s credentials." % server_type
        return CHISUBMIT_FAIL    
    
    conn.connect(git_credentials)        
    commit = conn.get_commit(course, team, commit_sha)
    
    if commit is None:
        print "Commit %s does not exist in repository" % commit_sha
        return CHISUBMIT_FAIL

    response = assignment.submit(team_id, commit_sha, extensions, dry_run=True)

    success = response["success"]
    dry_run = response["dry_run"]

    deadline_utc = parse(response["submission"]["deadline"])
    
    submitted_at_utc = parse(response["submission"]["submitted_at"])
    extensions_needed = response["submission"]["extensions_needed"]
    extensions_requested = response["submission"]["extensions_requested"]    

    extensions_available = response["team"]["extensions_available"]

    deadline_local = convert_datetime_to_local(deadline_utc)
    submitted_at_local = convert_datetime_to_local(submitted_at_utc)
        
    if not success:
        if extensions_needed > extensions_available:
            msg1 = "You do not have enough extensions to submit this assignment."
            msg2 = "You would need %i extensions to submit this assignment at this " \
                   "time, but you only have %i left" % (extensions_needed, extensions_available)
        elif extensions_requested < extensions_needed:
            msg1 = "The number of extensions you have requested is insufficient."
            msg2 = "You need to request %s extensions." % extensions_needed
        elif extensions_requested > extensions_needed:
            msg1 = "The number of extensions you have requested is excessive."
            msg2 = "You only need to request %s extensions." % extensions_needed

        print
        print msg1
        print            
        print "     Deadline (UTC): %s" % deadline_utc.isoformat(sep=" ")
        print "          Now (UTC): %s" % submitted_at_utc.isoformat(sep=" ")
        print 
        print "   Deadline (Local): %s" % deadline_local.isoformat(sep=" ")
        print "        Now (Local): %s" % submitted_at_local.isoformat(sep=" ")
        print 
        print msg2 
        print

        ctx.exit(CHISUBMIT_FAIL)
    else:
        tag_name = assignment.id
        submission_tag = conn.get_submission_tag(course, team, tag_name)
                
        if submission_tag is not None:
            submission_commit = submission_tag.commit
            if not force:
                print        
                print "Submission tag '%s' already exists" % tag_name
                print "It currently points to this commit:"
                print
                print_commit(submission_commit)
                print
                print "If you want to submit again, please use the --force option"
                ctx.exit(CHISUBMIT_FAIL)
            else:
                print
                print "WARNING: Submission tag '%s' already exists and you have requested that it be overwritten" % tag_name
                print "It currently points to this commit:"
                print
                print_commit(submission_commit)
                print
    
        if submission_tag is not None and force:
            msg = "THE ABOVE SUBMISSION FOR %s (%s) WILL BE CANCELLED." % (assignment.id, assignment.name)
            
            print "!"*len(msg)
            print msg
            print "!"*len(msg)
            print
            print "If you continue, your submission for %s (%s)" % (assignment.id, assignment.name)
            print "will now point to the following commit:"                
        else:
            print "You are going to make a submission for %s (%s)." % (assignment.id, assignment.name)
            print "The commit you are submitting is the following:"
        print
        print_commit(commit)
        print
        print "PLEASE VERIFY THIS IS THE EXACT COMMIT YOU WANT TO SUBMIT"
        print 
        print "Are you sure you want to continue? (y/n): ", 
        
        if not yes:
            yesno = raw_input()
        else:
            yesno = 'y'
            print 'y'
        
        if yesno in ('y', 'Y', 'yes', 'Yes', 'YES'):
            message = "Extensions: %i\n" % extensions_requested
                
            response = assignment.submit(team_id, commit_sha, extensions, dry_run=False)
                
            if submission_tag is None:
                conn.create_submission_tag(course, team, tag_name, message, commit.sha)
            else:
                conn.update_submission_tag(course, team, tag_name, message, commit.sha)
                
            print
            print "Your submission has been completed."
            #print "You can use 'chisubmit team-assignment-submission-verify' to double-check"
            #print "that your code was correctly tagged as ready to grade."
            
        return CHISUBMIT_SUCCESS

student.add_command(student_assignment_register)
student.add_command(student_assignment_submit)
student.add_command(student_set_git_username)
student.add_command(student_repo_check)



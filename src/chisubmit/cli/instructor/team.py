import click
from chisubmit.cli.common import pass_course, catch_chisubmit_exceptions,\
    get_assignment_or_exit, get_teams_registrations, require_local_config
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL,\
    ChisubmitException

import pprint
from chisubmit.cli.shared.team import shared_team_list, shared_team_show
import os
from chisubmit.repos.local import LocalGitRepo
from chisubmit.common.utils import create_connection
from git.exc import InvalidGitRepositoryError, GitCommandError
import operator

@click.group(name="team")
@click.pass_context
def instructor_team(ctx):
    pass


@click.command(name="pull-repos")
@click.argument('assignment_id', type=str)
@click.argument('directory', type=str)
@click.option('--only-ready-for-grading', is_flag=True)
@click.option('--reset', is_flag=True)
@click.option('--only', type=str)
@require_local_config
@pass_course
@click.pass_context
def instructor_team_pull_repos(ctx, course, assignment_id, directory, only_ready_for_grading, reset, only):
    assignment = get_assignment_or_exit(ctx, course, assignment_id)

    conn = create_connection(course, ctx.obj['config'])
    
    teams_registrations = get_teams_registrations(course, assignment, only = only)

    directory = os.path.expanduser(directory)
    
    if not os.path.exists(directory):
        os.makedirs(directory)

    teams = sorted([t for t in teams_registrations.keys() if t.active], key = operator.attrgetter("team_id"))

    max_len = max([len(t.team_id) for t in teams])

    for team in teams:
        registration = teams_registrations[team]
        team_dir = "%s/%s" % (directory, team.team_id)
        team_git_url = conn.get_repository_git_url(course, team) 

        if not registration.is_ready_for_grading() and only_ready_for_grading:
            print "%-*s  SKIPPING (not ready for grading)" % (max_len, team.team_id)
            continue
        
        try:
            msg = ""
            if not os.path.exists(team_dir):
                r = LocalGitRepo.create_repo(team_dir, clone_from_url=team_git_url)
                msg = "Cloned repo"
            else:
                r = LocalGitRepo(team_dir)
                if reset:
                    r.fetch("origin")
                    r.reset_branch("origin", "master")
                    msg = "Reset to match origin/master" 
                else:
                    if r.repo.is_dirty():
                        print "%-*s  ERROR: Cannot pull. Local repository has unstaged changes." % (max_len, team.team_id)
                        continue
                    r.checkout_branch("master")
                    r.pull("origin", "master")
                    msg = "Pulled latest changes"
            if only_ready_for_grading:
                r.checkout_commit(registration.final_submission.commit_sha)
                msg += " and checked out commit %s" % (registration.final_submission.commit_sha)               
            print "%-*s  %s" % (max_len, team.team_id, msg)
        except ChisubmitException, ce:
            print "%-*s  ERROR: Could not checkout or pull master branch (%s)" % (max_len, team.team_id, ce.message)
        except GitCommandError, gce:
            print "%-*s  ERROR: Could not checkout or pull master branch" % (max_len, team.team_id)
            print gce
        except InvalidGitRepositoryError, igre:
            print "%-*s  ERROR: Directory %s exists but does not contain a valid git repository"  % (max_len, team.team_id, team_dir)
        except Exception, e:
            print "%-*s  ERROR: Unexpected exception when trying to checkout/pull" % (max_len, team.team_id)
            raise
    
        

    return CHISUBMIT_SUCCESS


@click.command(name="student-add")
@click.argument('team_id', type=str)
@click.argument('student_id', type=str)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_team_student_add(ctx, course, team_id, student_id):
    student = course.get_student(student_id)
    if student is None:
        print "Student %s does not exist" % student_id
        ctx.exit(CHISUBMIT_FAIL)

    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        ctx.exit(CHISUBMIT_FAIL)

    team.add_student(student)

    return CHISUBMIT_SUCCESS


@click.command(name="assignment-add")
@click.argument('team_id', type=str)
@click.argument('assignment_id', type=str)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_team_assignment_add(ctx, course, team_id, assignment_id):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)

    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        ctx.exit(CHISUBMIT_FAIL)

    if team.assignments.has_key(assignment.id):
        print "Team %s has already been assigned assignment %s"  % (team.id, assignment.id)
        ctx.exit(CHISUBMIT_FAIL)

    team.add_assignment(assignment)

    return CHISUBMIT_SUCCESS

@click.command(name="set-active")
@click.argument('team_id', type=str)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_team_set_active(ctx, course, team_id):
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        ctx.exit(CHISUBMIT_FAIL)

    team.active = True

    return CHISUBMIT_SUCCESS

@click.command(name="set-inactive")
@click.argument('team_id', type=str)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_team_set_inactive(ctx, course, team_id):
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        ctx.exit(CHISUBMIT_FAIL)

    team.active = False

    return CHISUBMIT_SUCCESS

@click.command(name="set-attribute")
@click.argument('team_id', type=str)
@click.argument('name', type=str)
@click.argument('value', type=str)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def instructor_team_set_attribute(ctx, course, team_id, name, value):
    team = course.get_team(team_id)
    if team is None:
        print "Team %s does not exist" % team_id
        ctx.exit(CHISUBMIT_FAIL)

    team.set_extra(name, value)

    return CHISUBMIT_SUCCESS


instructor_team.add_command(shared_team_list)
instructor_team.add_command(shared_team_show)

instructor_team.add_command(instructor_team_pull_repos)
instructor_team.add_command(instructor_team_student_add)
instructor_team.add_command(instructor_team_assignment_add)
instructor_team.add_command(instructor_team_set_active)
instructor_team.add_command(instructor_team_set_inactive)
instructor_team.add_command(instructor_team_set_attribute)



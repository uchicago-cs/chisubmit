import click
from chisubmit.cli.common import pass_course, get_teams
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


@click.command(name="search")
@click.option('--verbose', is_flag=True)
@click.argument('team_id', type=str)
@pass_course
@click.pass_context
def instructor_team_search(ctx, course, verbose, team_id):
    teams = course.search_team(team_id)

    pp = pprint.PrettyPrinter(indent=4, depth=6)

    for t in teams:
        tdict = dict(vars(t))
        if verbose:
            tdict["assignments"] = dict(tdict["assignments"])
            for p in tdict["assignments"]:
                tdict["assignments"][p] = vars(tdict["assignments"][p])

            tdict["students"] = [vars(s) for s in tdict["students"]]

        pp.pprint(tdict)

    return CHISUBMIT_SUCCESS

@click.command(name="pull-repos")
@click.argument('assignment_id', type=str)
@click.argument('directory', type=str)
@click.option('--only-ready-for-grading', is_flag=True)
@click.option('--reset', is_flag=True)
@click.option('--only', type=str)
@pass_course
@click.pass_context
def instructor_team_pull_repos(ctx, course, assignment_id, directory, only_ready_for_grading, reset, only):
    assignment = course.get_assignment(assignment_id)
    if assignment is None:
        print "Assignment %s does not exist" % assignment_id
        ctx.exit(CHISUBMIT_FAIL)

    conn = create_connection(course, ctx.obj['config'])
    
    if conn is None:
        print "Could not connect to git server."
        ctx.exit(CHISUBMIT_FAIL)

    teams = get_teams(course, assignment, only = only)

    directory = os.path.expanduser(directory)
    
    if not os.path.exists(directory):
        os.makedirs(directory)

    max_len = max([len(t.id) for t in teams])

    for team in sorted([t for t in teams if t.active], key=operator.attrgetter("id")):
        team_dir = "%s/%s" % (directory, team.id)
        team_git_url = conn.get_repository_git_url(course, team) 
        ta = team.get_assignment(assignment.id)

        if not team.has_assignment_ready_for_grading(assignment) and only_ready_for_grading:
            print "%-*s  SKIPPING (not ready for grading)" % (max_len, team.id)
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
                        print "%-*s  ERROR: Cannot pull. Local repository has unstaged changes." % (max_len, team.id)
                        continue
                    r.checkout_branch("master")
                    r.pull("origin", "master")
                    msg = "Pulled latest changes"
            if only_ready_for_grading:
                r.checkout_commit(ta.commit_sha)
                msg += " and checked out commit %s" % (ta.commit_sha)               
            print "%-*s  %s" % (max_len, team.id, msg)
        except ChisubmitException, ce:
            print "%-*s  ERROR: Could not checkout or pull master branch (%s)" % (max_len, team.id, ce.message)
        except GitCommandError, gce:
            print "%-*s  ERROR: Could not checkout or pull master branch" % (max_len, team.id)
            print gce
        except InvalidGitRepositoryError, igre:
            print "%-*s  ERROR: Directory %s exists but does not contain a valid git repository"  % (max_len, team.id, team_dir)
        except Exception, e:
            print "%-*s  ERROR: Unexpected exception when trying to checkout/pull" % (max_len, team.id)
            raise
    
        

    return CHISUBMIT_SUCCESS


@click.command(name="student-add")
@click.argument('team_id', type=str)
@click.argument('student_id', type=str)
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

instructor_team.add_command(instructor_team_search)
instructor_team.add_command(instructor_team_pull_repos)
instructor_team.add_command(instructor_team_student_add)
instructor_team.add_command(instructor_team_assignment_add)
instructor_team.add_command(instructor_team_set_active)
instructor_team.add_command(instructor_team_set_inactive)
instructor_team.add_command(instructor_team_set_attribute)



import click

import os.path
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.cli.common import create_grading_repos,\
    gradingrepo_push_grading_branch, gradingrepo_pull_grading_branch, get_teams,\
    get_access_token
from chisubmit.repos.grading import GradingGitRepo
from chisubmit.rubric import RubricFile
from chisubmit.cli.common import pass_course, save_changes
from chisubmit.repos.factory import RemoteRepositoryConnectionFactory


@click.group()
@click.pass_context
def grader(ctx):
    pass

@click.command(name="create-local-grading-repos")
@click.argument('grader_id', type=str)
@click.argument('assignment_id', type=str)
@pass_course
@save_changes
@click.pass_context
def grader_create_local_grading_repos(ctx, course, grader_id, assignment_id):
    grader = course.get_grader(grader_id)
    if not grader:
        print "Grader %s does not exist" % grader_id
        ctx.exit(CHISUBMIT_FAIL)

    assignment = course.get_assignment(assignment_id)
    if not assignment:
        print "Assignment %s does not exist"
        ctx.exit(CHISUBMIT_FAIL)

    teams = get_teams(course, assignment, grader = grader)

    if not teams:
        print "No teams found"
        ctx.exit(CHISUBMIT_FAIL)

    repos = create_grading_repos(course, assignment, teams, grader = grader)

    if not repos:
        print "There was some kind of problem creating the grading repos."
        ctx.exit(CHISUBMIT_FAIL)

    for repo in repos:
        repo.set_grader_author()

    for team in teams:
        print "Pulling grading branch for team %s... " % team.id
        gradingrepo_pull_grading_branch(course, team, assignment, staging = True)

    return CHISUBMIT_SUCCESS


@click.command(name="validate-rubrics")
@click.argument('grader_id', type=str)
@click.argument('assignment_id', type=str)
@click.option('--only', type=str)
@pass_course
@save_changes
@click.pass_context
def grader_validate_rubrics(ctx, course, team_id, assignment_id):
    team = course.get_team(team_id)
    if not team:
        print "Team %s does not exist"
        ctx.exit(CHISUBMIT_FAIL)

    assignment = course.get_assignment(assignment_id)
    if not assignment:
        print "Assignment %s does not exist"
        ctx.exit(CHISUBMIT_FAIL)

    repo = GradingGitRepo.get_grading_repo(course, team, assignment)
    if not repo:
        print "Repository for %s does not exist" % (team.id)
        ctx.exit(CHISUBMIT_FAIL)

    rubricfile = repo.repo_path + "/%s.rubric.txt" % assignment.id

    if not os.path.exists(rubricfile):
        print "Repository for %s does not exist have a rubric for assignment %s" % (team.id, assignment.id)
        ctx.exit(CHISUBMIT_FAIL)

    # FIXME 18DEC14: validation explicit
    RubricFile.from_file(open(rubricfile), assignment)
    print "Rubric OK."

    return CHISUBMIT_SUCCESS


@click.command(name="push-grading-branches")
@click.argument('grader_id', type=str)
@click.argument('assignment_id', type=str)
@click.option('--only', type=str)
@pass_course
@save_changes
@click.pass_context
def grader_push_grading_branches(ctx, course, grader_id, assignment_id, only):
    grader = course.get_grader(grader_id)
    if not grader:
        print "Grader %s does not exist" % grader_id
        ctx.exit(CHISUBMIT_FAIL)

    assignment = course.get_assignment(assignment_id)
    if not assignment:
        print "Assignment %s does not exist"
        ctx.exit(CHISUBMIT_FAIL)

    teams = get_teams(course, assignment, grader = grader, only = only)

    if not teams:
        ctx.exit(CHISUBMIT_FAIL)

    for team in teams:
        print "Pushing grading branch for team %s... " % team.id
        gradingrepo_push_grading_branch(course, team, assignment, staging = True)

    return CHISUBMIT_SUCCESS

@click.command(name="pull-grading-branches")
@click.argument('grader_id', type=str)
@click.argument('assignment_id', type=str)
@click.option('--only', type=str)
@pass_course
@save_changes
@click.pass_context
def grader_pull_grading_branches(ctx, course, grader_id, assignment_id, only):
    grader = course.get_grader(grader_id)
    if not grader:
        print "Grader %s does not exist" % grader_id
        ctx.exit(CHISUBMIT_FAIL)

    assignment = course.get_assignment(assignment_id)
    if not assignment:
        print "Assignment %s does not exist"
        ctx.exit(CHISUBMIT_FAIL)

    teams = get_teams(course, assignment, grader = grader, only = only)

    if not teams:
        ctx.exit(CHISUBMIT_FAIL)

    for team in teams:
        print "Pulling grading branch for team %s... " % team.id
        gradingrepo_pull_grading_branch(course, team, assignment, staging = True)

    return CHISUBMIT_SUCCESS

grader.add_command(get_access_token)

grader.add_command(grader_create_local_grading_repos)
grader.add_command(grader_validate_rubrics)
grader.add_command(grader_push_grading_branches)
grader.add_command(grader_pull_grading_branches)

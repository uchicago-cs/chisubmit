import click
import operator
import os.path
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL
from chisubmit.cli.common import create_grading_repos,\
    gradingrepo_push_grading_branch, gradingrepo_pull_grading_branch,\
    get_grader_or_exit, get_assignment_or_exit, get_teams_registrations,\
    catch_chisubmit_exceptions, require_local_config, validate_repo_rubric
from chisubmit.repos.grading import GradingGitRepo
from chisubmit.rubric import RubricFile, ChisubmitRubricException
from chisubmit.cli.common import pass_course
from chisubmit.cli.shared.course import shared_course_get_git_credentials


@click.group()
@click.pass_context
def grader(ctx):
    pass

@click.command(name="pull-grading")
@click.option('--grader', type=str)
@click.argument('assignment_id', type=str)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def grader_pull_grading(ctx, course, grader, assignment_id):
    if grader is None:
        user = ctx.obj["client"].get_user()    
        
        grader = get_grader_or_exit(ctx, course, user.username)
    else:
        grader = get_grader_or_exit(ctx, course, grader)
        
    assignment = get_assignment_or_exit(ctx, course, assignment_id)

    teams_registrations = get_teams_registrations(course, assignment, grader = grader)
    
    if len(teams_registrations) == 0:
        print "No teams found"
        ctx.exit(CHISUBMIT_FAIL)

    teams = sorted(teams_registrations.keys(), key=operator.attrgetter("team_id"))

    for team in teams:
        registration = teams_registrations[team]
        repo = GradingGitRepo.get_grading_repo(ctx.obj['config'], course, team, registration)

        if repo is None:
            print ("%40s -- Creating grading repo... " % team.team_id),
            repo = GradingGitRepo.create_grading_repo(ctx.obj['config'], course, team, registration, staging_only = True)
            repo.sync()
            gradingrepo_pull_grading_branch(ctx.obj['config'], course, team, registration)
            repo.set_grader_author()
            
            print "done"
        else:
            print ("%40s -- Pulling grading branch..." % team.team_id),
            gradingrepo_pull_grading_branch(ctx.obj['config'], course, team, registration)
            print "done"
            
        rubricfile = "%s.rubric.txt" % assignment.assignment_id
        rubricfilepath = "%s/%s" % (repo.repo_path, rubricfile)
        if not os.path.exists(rubricfilepath):
            rubric = RubricFile.from_assignment(assignment)
            rubric.save(rubricfilepath, include_blank_comments=True)            
        
    return CHISUBMIT_SUCCESS


@click.command(name="push-grading")
@click.argument('assignment_id', type=str)
@click.option('--grader', type=str)
@click.option('--only', type=str)
@click.option('--skip-rubric-validation', is_flag=True)
@require_local_config
@pass_course
@click.pass_context
def grader_push_grading(ctx, course, assignment_id, grader, only, skip_rubric_validation):
    if grader is None:
        user = ctx.obj["client"].get_user()    
        
        grader = get_grader_or_exit(ctx, course, user.username)
    else:
        grader = get_grader_or_exit(ctx, course, grader)

    assignment = get_assignment_or_exit(ctx, course, assignment_id)

    teams_registrations = get_teams_registrations(course, assignment, grader = grader, only = only, only_ready_for_grading=True)
    
    if len(teams_registrations) == 0:
        print "No teams found"
        ctx.exit(CHISUBMIT_FAIL)

    for team, registration in teams_registrations.items():
        if not skip_rubric_validation:
            valid, error_msg = validate_repo_rubric(ctx, course, assignment, team, registration)
            if not valid:
                print "Not pushing branch for team %s. Rubric does not validate: %s" % (team.team_id, error_msg)
                continue
        
        print "Pushing grading branch for team %s... " % team.team_id
        gradingrepo_push_grading_branch(ctx.obj['config'], course, team, registration)

    return CHISUBMIT_SUCCESS


@click.command(name="validate-rubrics")
@click.argument('assignment_id', type=str)
@click.option('--grader', type=str)
@click.option('--only', type=str)
@catch_chisubmit_exceptions
@require_local_config
@pass_course
@click.pass_context
def grader_validate_rubrics(ctx, course, assignment_id, grader, only):
    if grader is None:
        user = ctx.obj["client"].get_user()    
        
        grader = get_grader_or_exit(ctx, course, user.username)
    else:
        grader = get_grader_or_exit(ctx, course, grader)

    assignment = get_assignment_or_exit(ctx, course, assignment_id)

    teams_registrations = get_teams_registrations(course, assignment, grader = grader, only = only)
    
    all_valid = True
    for team, registration in teams_registrations.items():
        valid, error_msg = validate_repo_rubric(ctx, course, assignment, team, registration)

        if valid:
            print "%s: Rubric OK." % team.team_id
        else:
            print "%s: Rubric ERROR: %s" % (team.team_id, error_msg)
            all_valid = False
            
    if not all_valid:
        ctx.exit(CHISUBMIT_FAIL)
    else:
        return CHISUBMIT_SUCCESS


grader.add_command(grader_pull_grading)
grader.add_command(grader_push_grading)
grader.add_command(grader_validate_rubrics)
grader.add_command(shared_course_get_git_credentials)


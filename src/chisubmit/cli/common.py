import click

from chisubmit.repos.grading import GradingGitRepo
from chisubmit.common import CHISUBMIT_FAIL, CHISUBMIT_SUCCESS
from chisubmit.client.course import Course

from functools import update_wrapper

from dateutil.parser import parse

def pass_course(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        course_id = ctx.obj["course_id"]
        course_specified = ctx.obj["course_specified"]

        if course_specified:
            course_obj = Course.from_id(course_id)
        else:
            if course_id is None:
                raise click.UsageError("No course specified with --course and there is no default course")
            else:
                course_obj = Course.from_id(course_id)

        if course_obj is None:
            raise click.BadParameter("Course '%s' does not exist" % course_id)

        ctx.obj["course_obj"] = course_obj

        return ctx.invoke(f, ctx.obj["course_obj"], *args, **kwargs)

    return update_wrapper(new_func, f)


def save_changes(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        #ctx.call_on_close(ctx.obj["course_obj"].save)

        return ctx.invoke(f, *args, **kwargs)

    return update_wrapper(new_func, f)


class DateTimeParamType(click.ParamType):
    name = 'datetime'

    def convert(self, value, param, ctx):
        try:
            return parse(value)
        except ValueError:
            self.fail('"%s" is not a valid datetime string' % value, param, ctx)

DATETIME = DateTimeParamType()


def get_teams(course, assignment, grader = None, only = None):
    if only is not None:
        team = course.get_team(only)
        if team is None:
            print "Team %s does not exist"
            return None
        if not team.has_assignment(assignment.id):
            print "Team %s has not been assigned assignment %s" % (team.id, assignment.id)
            return None

        teams = [team]
    else:
        teams = [t for t in course.teams if t.has_assignment(assignment.id)]

        if grader is not None:
            teams = [t for t in teams if t.get_assignment(assignment.id).get_grader().id == grader.id]

    return teams


def create_grading_repos(base_dir, course, assignment, teams, grader = None):
    repos = []

    for team in teams:
        repo = GradingGitRepo.get_grading_repo(base_dir, course, team, assignment)

        if repo is None:
            print ("Creating grading repo for %s... " % team.id),
            repo = GradingGitRepo.create_grading_repo(base_dir, course, team, assignment)
            repo.sync()

            repos.append(repo)

            print "done"
        else:
            print "Grading repo for %s already exists" % team.id

    return repos


def gradingrepo_push_grading_branch(course, team, assignment, github=False, staging=False):
    repo = GradingGitRepo.get_grading_repo(course, team, assignment)

    if repo is None:
        print "%s does not have a grading repository" % team.id
        return CHISUBMIT_FAIL

    if not repo.has_grading_branch():
        print "%s does not have a grading branch" % team.id
        return CHISUBMIT_FAIL

    if github:
        repo.push_grading_branch_to_github()

    if staging:
        repo.push_grading_branch_to_staging()

    return CHISUBMIT_SUCCESS

def gradingrepo_pull_grading_branch(course, team, assignment, github=False, staging=False):
    assert(not (github and staging))
    repo = GradingGitRepo.get_grading_repo(course, team, assignment)

    if repo is None:
        print "%s does not have a grading repository" % team.id
        return CHISUBMIT_FAIL

    if github:
        if not repo.has_grading_branch_staging():
            print "%s does not have a grading branch on GitHub" % team.id
        else:
            repo.pull_grading_branch_from_github()

    if staging:
        if not repo.has_grading_branch_staging():
            print "%s does not have a grading branch in staging" % team.id
        else:
            repo.pull_grading_branch_from_staging()

    return CHISUBMIT_SUCCESS

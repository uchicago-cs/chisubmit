import click

from chisubmit.repos.grading import GradingGitRepo
from chisubmit.common import CHISUBMIT_FAIL, CHISUBMIT_SUCCESS
from chisubmit.client.course import Course

from functools import update_wrapper

from dateutil.parser import parse
import getpass
from chisubmit.client.user import User

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
            teams = [t for t in teams if t.get_assignment(assignment.id).grader.id == grader.user.id]

    return teams


def create_grading_repos(config, course, assignment, teams):
    repos = []

    for team in teams:
        repo = GradingGitRepo.get_grading_repo(config, course, team, assignment)

        if repo is None:
            print ("Creating grading repo for %s... " % team.id),
            repo = GradingGitRepo.create_grading_repo(config, course, team, assignment)
            repo.sync()

            repos.append(repo)

            print "done"
        else:
            print "Grading repo for %s already exists" % team.id

    return repos


def gradingrepo_push_grading_branch(config, course, team, assignment, to_students=False, to_staging=False):
    repo = GradingGitRepo.get_grading_repo(config, course, team, assignment)

    if repo is None:
        print "%s does not have a grading repository" % team.id
        return CHISUBMIT_FAIL

    if not repo.has_grading_branch():
        print "%s does not have a grading branch" % team.id
        return CHISUBMIT_FAIL

    if to_students:
        repo.push_grading_branch_to_students()

    if to_staging:
        repo.push_grading_branch_to_staging()

    return CHISUBMIT_SUCCESS

def gradingrepo_pull_grading_branch(config, course, team, assignment, from_students=False, from_staging=False):
    assert(not (from_students and from_staging))
    repo = GradingGitRepo.get_grading_repo(config, course, team, assignment)

    if repo is None:
        print "%s does not have a grading repository" % team.id
        return CHISUBMIT_FAIL

    if from_students:
        if not repo.has_grading_branch_staging():
            print "%s does not have a grading branch on students' repository" % team.id
        else:
            repo.pull_grading_branch_from_students()

    if from_staging:
        if not repo.has_grading_branch_staging():
            print "%s does not have a grading branch in staging" % team.id
        else:
            repo.pull_grading_branch_from_staging()

    return CHISUBMIT_SUCCESS


@click.command(name="get-access-token")
@click.option('--user', prompt='Enter your chisubmit username', default=lambda: getpass.getuser())
@click.option('--delete', is_flag=True)
@click.pass_context
def get_access_token(ctx, user, delete):

    password = getpass.getpass("Enter your password: ")
    token = User.get_token(user, password, delete)

    if token:
        ctx.obj['config']['api-token'] = token
        click.echo("Your chisubmit access token is: %s")
        click.echo("The token has been stored in your chisubmit configuration file.")
        click.echo("You should now be able to use the chisubmit commands.")
    else:
        click.echo("Unable to create token. Incorrect username/password.")

    return CHISUBMIT_SUCCESS

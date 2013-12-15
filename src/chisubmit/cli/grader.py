from chisubmit.common.utils import create_subparser
from chisubmit.core.repos import GradingGitRepo
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL

def create_grader_subparsers(subparsers):
    subparser = create_subparser(subparsers, "grader-sync-grading-repo", cli_do__grader_sync_grading_repo)
    subparser.add_argument('team_id', type=str)

    subparser = create_subparser(subparsers, "grader-create-grading-branch", cli_do__grader_create_grading_branch)
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('project_id', type=str)

    subparser = create_subparser(subparsers, "grader-push-grading-branch", cli_do__grader_push_grading_branch)
    subparser.add_argument('--staging', action="store_true")
    subparser.add_argument('--github', action="store_true")
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('project_id', type=str)

    subparser = create_subparser(subparsers, "grader-pull-grading-branch", cli_do__grader_pull_grading_branch)
    subparser.add_argument('--staging', action="store_true")
    subparser.add_argument('--github', action="store_true")
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('project_id', type=str)


def cli_do__grader_sync_grading_repo(course, args):
    team = course.teams[args.team_id]
    
    repo = GradingGitRepo.get_grading_repo(course, team)
    
    if repo is None:
        repo = GradingGitRepo.create_grading_repo(course, team)
    else:
        repo.sync()

    return CHISUBMIT_SUCCESS

        
def cli_do__grader_create_grading_branch(course, args):
    team = course.teams[args.team_id]
    project = course.projects[args.project_id]
    
    repo = GradingGitRepo.get_grading_repo(course, team)
    
    if repo is None:
        print "%s does not have a grading repository" % team.id
        return CHISUBMIT_FAIL
    
    repo.create_grading_branch(project)

    return CHISUBMIT_SUCCESS


def cli_do__grader_push_grading_branch(course, args):
    team = course.teams[args.team_id]
    project = course.projects[args.project_id]
    
    repo = GradingGitRepo.get_grading_repo(course, team)
    
    if repo is None:
        print "%s does not have a grading repository" % team.id
        return CHISUBMIT_FAIL
        
    if args.github:
        repo.push_grading_branch_to_github(project)
        
    if args.staging:
        repo.push_grading_branch_to_staging(project)

def cli_do__grader_pull_grading_branch(course, args):
    team = course.teams[args.team_id]
    project = course.projects[args.project_id]
    
    repo = GradingGitRepo.get_grading_repo(course, team)
    
    if repo is None:
        print "%s does not have a grading repository" % team.id
        return CHISUBMIT_FAIL
    
    if args.github:
        repo.pull_grading_branch_from_github(project)
    
    if args.staging:
        repo.pull_grading_branch_from_staging(project)
        
    return CHISUBMIT_SUCCESS
                
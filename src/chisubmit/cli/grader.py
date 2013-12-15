from chisubmit.common.utils import create_subparser
from chisubmit.core.repos import LocalGitRepo
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
    
    repo = LocalGitRepo.get_team_local_repo(course, team)
    
    if repo is None:
        repo = LocalGitRepo.create_team_local_repo(course, team)
    else:
        repo.fetch()
        repo.reset_branch("master")

    return CHISUBMIT_SUCCESS

        
def cli_do__grader_create_grading_branch(course, args):
    team = course.teams[args.team_id]
    project = course.projects[args.project_id]
    
    repo = LocalGitRepo.get_team_local_repo(course, team)
    
    if repo is None:
        print "%s does not have a local repository" % team.id
        return CHISUBMIT_FAIL
    
    tag = repo.get_tag(project.id)
    if tag is None:
        print "%s repository does not have a %s tag" % (team.id, project.id)
        return CHISUBMIT_FAIL
    
    branch_name = project.get_grading_branch_name()
    if repo.has_branch(branch_name):
        print "%s repository already has a %s branch" % (team.id, branch_name)
        return CHISUBMIT_FAIL
    
    repo.create_branch(branch_name, tag.commit)
    repo.checkout_branch(branch_name)

    return CHISUBMIT_SUCCESS


def cli_do__grader_push_grading_branch(course, args):
    team = course.teams[args.team_id]
    project = course.projects[args.project_id]
    
    repo = LocalGitRepo.get_team_local_repo(course, team)
    
    if repo is None:
        print "%s does not have a local repository" % team.id
        return CHISUBMIT_FAIL
        
    branch_name = project.get_grading_branch_name()
    if not repo.has_branch(branch_name):
        print "%s repository does not have a %s branch" % (team.id, branch_name)
        return CHISUBMIT_FAIL
    
    if args.github:
        repo.push_branch_to_github(branch_name)
    
    if args.staging:
        repo.push_branch_to_staging("master")
        repo.push_branch_to_staging(branch_name)
        
    return CHISUBMIT_SUCCESS
        

def cli_do__grader_pull_grading_branch(course, args):
    team = course.teams[args.team_id]
    project = course.projects[args.project_id]
    
    repo = LocalGitRepo.get_team_local_repo(course, team)
    
    if repo is None:
        print "%s does not have a local repository" % team.id
        return CHISUBMIT_FAIL
  
    branch_name = project.get_grading_branch_name()
  
    if args.github:
        repo.pull_branch_from_github(branch_name)
    
    if args.staging:
        repo.pull_branch_from_staging(branch_name)
        
    return CHISUBMIT_SUCCESS
                
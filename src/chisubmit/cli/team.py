import chisubmit.core

from chisubmit.common.utils import create_subparser
from chisubmit.core.model import Team
from chisubmit.core.repos import GithubConnection, LocalGitRepo
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL

def create_team_subparsers(subparsers):
    subparser = create_subparser(subparsers, "team-create", cli_do__team_create)
    subparser.add_argument('id', type=str)
    
    subparser = create_subparser(subparsers, "team-student-add", cli_do__team_student_add)
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('student_id', type=str)

    subparser = create_subparser(subparsers, "team-project-add", cli_do__team_project_add)
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('project_id', type=str)
    
    subparser = create_subparser(subparsers, "team-gh-repo-create", cli_do__team_gh_repo_create)
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('--ignore-existing', action="store_true", dest="ignore_existing")
    
    subparser = create_subparser(subparsers, "team-gh-repo-update", cli_do__team_gh_repo_update)
    subparser.add_argument('team_id', type=str)    

    subparser = create_subparser(subparsers, "team-gh-repo-remove", cli_do__team_gh_repo_remove)
    subparser.add_argument('team_id', type=str)

    subparser = create_subparser(subparsers, "team-local-repo-sync", cli_do__team_local_repo_sync)
    subparser.add_argument('team_id', type=str)

    subparser = create_subparser(subparsers, "team-create-grading-branch", cli_do__team_create_grading_branch)
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('project_id', type=str)


def cli_do__team_create(course, args):
    team = Team(team_id = args.id)
    course.add_team(team)
    
    return CHISUBMIT_SUCCESS

    
def cli_do__team_student_add(course, args):
    student = course.students[args.student_id]
    course.teams[args.team_id].add_student(student)   

    return CHISUBMIT_SUCCESS

    
def cli_do__team_project_add(course, args):
    project = course.projects[args.project_id]
    course.teams[args.team_id].add_project(project)                

    return CHISUBMIT_SUCCESS

    
def cli_do__team_gh_repo_create(course, args):
    team = course.teams[args.team_id]
    github_access_token = chisubmit.core.get_github_token()
    
    if team.github_repo is not None and not args.ignore_existing:
        print "Repository for team %s has already been created." % team.id
        print "Maybe you meant to run team-repo-update?"
        return CHISUBMIT_FAIL
    
    gh = GithubConnection(github_access_token, course.github_organization)
        
    gh.create_team_repository(course, team, fail_if_exists = not args.ignore_existing)

    return CHISUBMIT_SUCCESS

    
def cli_do__team_gh_repo_update(course, args):
    team = course.teams[args.team_id]
    github_access_token = chisubmit.core.get_github_token()
    
    if team.github_repo is None:
        print "Team %s does not have a repository." % team.id
        return CHISUBMIT_FAIL
    
    gh = GithubConnection(github_access_token, course.github_organization)
        
    gh.update_team_repository(team)    

    return CHISUBMIT_SUCCESS

    
def cli_do__team_gh_repo_remove(course, args):
    team = course.teams[args.team_id]
    
    if team.github_repo is None:
        print "Team %s does not have a repository." % team.id
        return CHISUBMIT_FAIL

    github_access_token = chisubmit.core.get_github_delete_token()
    
    if github_access_token is None:
        print "No GitHub access token with delete permissions found."
        print "You need to create an access token with 'repo' and 'delete_repo' scopes"
        return CHISUBMIT_FAIL
        
    gh = GithubConnection(github_access_token, course.github_organization)
        
    gh.delete_team_repository(team)

    return CHISUBMIT_SUCCESS


def cli_do__team_local_repo_sync(course, args):
    team = course.teams[args.team_id]
    
    repo = LocalGitRepo.get_team_local_repo(course, team)
    
    if repo is None:
        repo = LocalGitRepo.create_team_local_repo(course, team)
    else:
        repo.fetch()
        repo.reset_branch("master")

    return CHISUBMIT_SUCCESS

        
def cli_do__team_create_grading_branch(course, args):
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
        
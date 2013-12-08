from chisubmit.common.utils import create_subparser
from chisubmit.core.model import Team
from chisubmit.core.repos import GithubConnection, LocalGitRepo

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
    
    subparser = create_subparser(subparsers, "team-gh-repo-update", cli_do__team_gh_repo_update)
    subparser.add_argument('team_id', type=str)    

    subparser = create_subparser(subparsers, "team-gh-repo-remove", cli_do__team_gh_repo_remove)
    subparser.add_argument('team_id', type=str)

    subparser = create_subparser(subparsers, "team-local-repo-sync", cli_do__team_local_repo_sync)
    subparser.add_argument('team_id', type=str)

    subparser = create_subparser(subparsers, "team-create-grading-branch", cli_do__team_create_grading_branch)
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('project_id', type=str)


def cli_do__team_create(course, config, args):
    team = Team(team_id = args.id)
    course.add_team(team)
    
def cli_do__team_student_add(course, config, args):
    student = course.students[args.student_id]
    course.teams[args.team_id].add_student(student)   
    
def cli_do__team_project_add(course, config, args):
    project = course.projects[args.project_id]
    course.teams[args.team_id].add_project(project)                
    
def cli_do__team_gh_repo_create(course, config, args):
    team = course.teams[args.team_id]
    github_access_token = config.get("github", "access-token")
    
    if team.github_repo is not None:
        print "Repository for team %s has already been created." % team.id
        print "Maybe you meant to run team-repo-update?"
        return
    
    gh = GithubConnection(github_access_token, course.github_organization)
        
    gh.create_team_repository(course, team)
    
def cli_do__team_gh_repo_update(course, config, args):
    team = course.teams[args.team_id]
    github_access_token = config.get("github", "access-token")
    
    if team.github_repo is None:
        print "Team %s does not have a repository." % team.id
        return
    
    gh = GithubConnection(github_access_token, course.github_organization)
        
    gh.update_team_repository(team)    
    
def cli_do__team_gh_repo_remove(course, config, args):
    team = course.teams[args.team_id]
    
    if not config.has_option("github", "access-token-delete"):
        print "Configuration file does not have a [github].access-token-delete option."
        print "You need to set this option to an access token with 'repo' and 'delete_repo' scopes"
        return
        
    github_access_token = config.get("github", "access-token-delete")
    
    if team.github_repo is None:
        print "Team %s does not have a repository." % team.id
        return
    
    gh = GithubConnection(github_access_token, course.github_organization)
        
    gh.delete_team_repository(team)


def cli_do__team_local_repo_sync(course, config, args):
    team = course.teams[args.team_id]
    
    repo = LocalGitRepo.get_team_local_repo(course, team, args.dir)
    
    if repo is None:
        repo = LocalGitRepo.create_team_local_repo(course, team, args.dir)
    else:
        repo.fetch()
        repo.reset_branch("master")
        
def cli_do__team_create_grading_branch(course, config, args):
    team = course.teams[args.team_id]
    project = course.projects[args.project_id]
    
    repo = LocalGitRepo.get_team_local_repo(course, team, args.dir)
    
    if repo is None:
        print "%s does not have a local repository" % team.id
        return
    
    tag = repo.get_tag(project.id)
    if tag is None:
        print "%s repository does not have a %s tag" % (team.id, project.id)
        return
    
    branch_name = project.get_grading_branch_name()
    if repo.has_branch(branch_name):
        print "%s repository already has a %s branch" % (team.id, branch_name)
        return
    
    repo.create_branch(branch_name, tag.commit)
        
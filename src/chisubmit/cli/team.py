from chisubmit.utils import create_subparser, set_datetime_timezone_utc, set_datetime_timezone_local,\
    convert_timezone_to_local
from chisubmit.model import Team
from chisubmit.repos import GithubConnection

def create_team_subparsers(subparsers):
    subparser = create_subparser(subparsers, "team-create", cli_do__team_create)
    subparser.add_argument('id', type=str)
    
    subparser = create_subparser(subparsers, "team-student-add", cli_do__team_student_add)
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('student_id', type=str)

    subparser = create_subparser(subparsers, "team-project-add", cli_do__team_project_add)
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('project_id', type=str)
    
    subparser = create_subparser(subparsers, "team-project-submit", cli_do__team_project_submit)
    subparser.add_argument('team_id', type=str)    
    subparser.add_argument('project_id', type=str)
    subparser.add_argument('commit', type=str)
    subparser.add_argument('extensions', type=int, default=0)

    subparser = create_subparser(subparsers, "team-repo-create", cli_do__team_repo_create)
    subparser.add_argument('team_id', type=str)
    
    subparser = create_subparser(subparsers, "team-repo-update", cli_do__team_repo_update)
    subparser.add_argument('team_id', type=str)    

    subparser = create_subparser(subparsers, "team-repo-remove", cli_do__team_repo_remove)
    subparser.add_argument('team_id', type=str)

def cli_do__team_create(course, config, args):
    team = Team(team_id = args.id)
    course.add_team(team)
    
def cli_do__team_student_add(course, config, args):
    student = course.students[args.student_id]
    course.teams[args.team_id].add_student(student)   
    
def cli_do__team_project_add(course, config, args):
    project = course.projects[args.project_id]
    course.teams[args.team_id].add_project(project)     
    
def cli_do__team_project_submit(course, config, args):
    project = course.projects[args.project_id]
    team = course.teams[args.team_id]
    team_project = team.projects[args.project_id]
    
    github_access_token = config.get("github", "access-token")
    gh = GithubConnection(github_access_token, course.github_organization)
    
    commit = gh.get_commit(team, args.commit)
    
    if commit is None:
        print "Commit %s does not exist in repository" % commit
        return
        
    tag_name = project.id
    
    submission_tag = gh.get_submission_tag(team, tag_name)
    
    if submission_tag is not None:
        submission_commit = gh.get_commit(team, submission_tag.object.sha)
        print "Submission tag '%s' already exists" % tag_name
        print "It points to commit %s (%s)" % (submission_commit.commit.sha, submission_commit.commit.message)
        return
    
    gh.create_submission_tag(team, tag_name, "Extensions: %i" % args.extensions, commit.commit.sha)
           
    
def cli_do__team_repo_create(course, config, args):
    team = course.teams[args.team_id]
    github_access_token = config.get("github", "access-token")
    
    if team.github_repo is not None:
        print "Repository for team %s has already been created." % team.id
        print "Maybe you meant to run team-repo-update?"
        return
    
    gh = GithubConnection(github_access_token, course.github_organization)
        
    gh.create_team_repository(course, team)
    
def cli_do__team_repo_update(course, config, args):
    team = course.teams[args.team_id]
    github_access_token = config.get("github", "access-token")
    
    if team.github_repo is None:
        print "Team %s does not have a repository." % team.id
        return
    
    gh = GithubConnection(github_access_token, course.github_organization)
        
    gh.update_team_repository(team)    
    
def cli_do__team_repo_remove(course, config, args):
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
        
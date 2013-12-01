from chisubmit.cli.utils import create_subparser
from chisubmit.model import Team

def create_team_subparsers(subparsers):
    subparser = create_subparser(subparsers, "team-create", cli_do__team_create)
    subparser.add_argument('id', type=str)
    
    subparser = create_subparser(subparsers, "team-student-add", cli_do__team_student_add)
    subparser.add_argument('team_id', type=str)
    subparser.add_argument('student_id', type=str)

    subparser = create_subparser(subparsers, "team-project-add", cli_do__team_project_add)
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
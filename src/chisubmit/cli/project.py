from chisubmit.common.utils import create_subparser, mkdatetime
from chisubmit.core.model import Project, GradeComponent

def create_project_subparsers(subparsers):
    subparser = create_subparser(subparsers, "project-create", cli_do__project_create)
    subparser.add_argument('id', type=str)
    subparser.add_argument('name', type=str)
    subparser.add_argument('deadline', type=mkdatetime)
    
    subparser = create_subparser(subparsers, "project-grade-component-add", cli_do__project_grade_component_add)
    subparser.add_argument('project_id', type=str)
    subparser.add_argument('name', type=str)
    subparser.add_argument('points', type=int)

    
def cli_do__project_create(course, args):
    project = Project(project_id = args.id,
                      name = args.name,
                      deadline = args.deadline)
    course.add_project(project)
    
   
def cli_do__project_grade_component_add(course, args):
    grade_component = GradeComponent(args.name, args.points)
    course.projects[args.project_id].add_grade_component(grade_component)    
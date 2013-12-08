import chisubmit.core

from chisubmit.common.utils import create_subparser
from chisubmit.core.model import Course
from chisubmit.core.repos import GithubConnection
from chisubmit.common import CHISUBMIT_SUCCESS

def create_course_subparsers(subparsers):
    subparser = create_subparser(subparsers, "course-create", cli_do__course_create)
    subparser.add_argument('--make-default', action="store_true", dest="make_default")
    subparser.add_argument('id', type=str)
    subparser.add_argument('name', type=str)
    subparser.add_argument('extensions', type=int)
    
    subparser = create_subparser(subparsers, "course-github-settings", cli_do__course_github_settings)
    subparser.add_argument('organization', type=str)
    subparser.add_argument('instructors_team', type=str)

    
def cli_do__course_create(course, args):
    course = Course(course_id = args.id,
                    name = args.name,
                    extensions = args.extensions)
    course.course_file = chisubmit.core.get_course_filename(course.id)
    course.save()
    
    if args.make_default:
        chisubmit.core.set_default_course(args.id)
        
    return CHISUBMIT_SUCCESS
    
def cli_do__course_github_settings(course, args):
    course.github_organization = args.organization
    course.github_instructors_team = args.instructors_team
    
    # Try connecting to GitHub
    github_access_token = chisubmit.core.chisubmit_conf.get("github", "access-token")
    GithubConnection(github_access_token, course.github_organization)
    
    return CHISUBMIT_SUCCESS
    
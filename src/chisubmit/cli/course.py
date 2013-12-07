from chisubmit.utils import create_subparser, set_default_course
from chisubmit.model import Course
from chisubmit.repos import GithubConnection

def create_course_subparsers(subparsers):
    subparser = create_subparser(subparsers, "course-create", cli_do__course_create)
    subparser.add_argument('--make-default', action="store_true", dest="make_default")
    subparser.add_argument('id', type=str)
    subparser.add_argument('name', type=str)
    subparser.add_argument('extensions', type=int)
    
    subparser = create_subparser(subparsers, "course-github-settings", cli_do__course_github_settings)
    subparser.add_argument('organization', type=str)
    subparser.add_argument('instructors_team', type=str)

    
def cli_do__course_create(course, config, args):
    course = Course(course_id = args.id,
                    name = args.name,
                    extensions = args.extensions)
    course_file = open(args.dir + "/courses/" + args.id + ".yaml", 'w')
    course.to_file(course_file)
    course_file.close()
    
    if args.make_default:
        set_default_course(args.dir, args.id)
    
def cli_do__course_github_settings(course, config, args):
    course.github_organization = args.organization
    course.github_instructors_team = args.instructors_team
    
    # Try connecting to GitHub
    github_access_token = config.get("github", "access-token")
    GithubConnection(github_access_token, course.github_organization)
    
    
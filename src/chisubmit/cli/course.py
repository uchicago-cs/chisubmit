from chisubmit.cli.utils import create_subparser
from chisubmit.model import Course

def create_course_subparsers(subparsers):
    subparser = create_subparser(subparsers, "course-create", cli_do__course_create)
    subparser.add_argument('--make-default', action="store_true", dest="make_default")
    subparser.add_argument('id', type=str)
    subparser.add_argument('name', type=str)
    subparser.add_argument('extensions', type=int)

    
def cli_do__course_create(course, config, args):
    course = Course(course_id = args.id,
                    name = args.name,
                    extensions = args.extensions)
    course_file = open(args.dir + "/courses/" + args.id + ".yaml", 'w')
    course.to_file(course_file)
    course_file.close()
    
    if args.make_default:
        config.set("general", "default-course", args.id)
        config_file = open(args.config, "w")
        config.write(config_file)
        config_file.close()
    

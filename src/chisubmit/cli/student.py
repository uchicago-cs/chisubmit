from chisubmit.common.utils import create_subparser
from chisubmit.core.model import Student

def create_student_subparsers(subparsers):
    subparser = create_subparser(subparsers, "student-create", cli_do__student_create)
    subparser.add_argument('id', type=str)
    subparser.add_argument('first_name', type=str)
    subparser.add_argument('last_name', type=str)
    subparser.add_argument('email', type=str)
    subparser.add_argument('github_id', type=str)
    
    subparser = create_subparser(subparsers, "student-set-dropped", cli_do__student_set_dropped)
    subparser.add_argument('id', type=str)


def cli_do__student_create(course, args):
    student = Student(student_id = args.id,
                      first_name = args.first_name,
                      last_name = args.last_name,
                      email = args.email,
                      github_id = args.github_id)
    course.add_student(student)
    
def cli_do__student_set_dropped(course, args):
    course.students[args.id].dropped = True   
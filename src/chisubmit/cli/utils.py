import datetime

def create_subparser(subparsers, name, func):
    subparser = subparsers.add_parser(name)
    subparser.set_defaults(func=func)
    
    return subparser

def mkdatetime(datetimestr):
    return datetime.datetime.strptime(datetimestr, '%Y-%m-%dT%H:%M')

def get_course(config, args):
    if args.course:
        course = args.course
    else:
        if config.has_option("general", "default-course"):
            course = config.get("general", "default-course")
        else:
            course = None
    
    return course    
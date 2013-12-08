import datetime
import pytz
from tzlocal import get_localzone

def create_subparser(subparsers, name, func):
    subparser = subparsers.add_parser(name)
    subparser.set_defaults(func=func)
    
    return subparser

def set_datetime_timezone_local(dt):
    return get_localzone().localize(dt)

def set_datetime_timezone_utc(dt):
    return pytz.utc.localize(dt)

def convert_timezone_to_local(dt):
    tz = get_localzone()
    dt = dt.astimezone(tz)
    return tz.normalize(dt)
    

def mkdatetime(datetimestr):
    dt = datetime.datetime.strptime(datetimestr, '%Y-%m-%dT%H:%M')
    return set_datetime_timezone_local(dt)




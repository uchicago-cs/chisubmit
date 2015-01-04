import chisubmit.client.session as session
import tempfile
import os
import json
from chisubmit.backend.webapp.api.users.models import User
from chisubmit.backend.webapp.api.courses.models import Course,\
    CoursesInstructors, CoursesGraders, CoursesStudents
from chisubmit.backend.webapp.api import ChisubmitAPIServer
from click.testing import CliRunner
from functools import update_wrapper
import yaml
from chisubmit.cli import chisubmit_cmd
import sys
from chisubmit.backend.webapp.api.assignments.models import Assignment
from dateutil.parser import parse
import colorama
import git
import functools
from chisubmit.client.session import BadRequestError
import unittest

colorama.init()

class ChisubmitTestClient(object):
    
    API_PREFIX = "/api/v0/"
    
    def __init__(self, app, user_id, api_key):
        self.user_id = user_id
        self.api_key = api_key
        
        self.headers = {'content-type': 'application/json'}
        
        if self.api_key is not None:
            self.headers["CHISUBMIT-API-KEY"] = self.api_key
            
        self.test_client = session.connect_test(app, api_key)

    def get(self, resource):
        return self.test_client.get(self.API_PREFIX + resource, headers = self.headers)

    def post(self, resource, data):
        if isinstance(data, dict):
            datastr = json.dumps(data)
        elif isinstance(data, basestring):
            datastr = data
        return self.test_client.post(self.API_PREFIX + resource, data = datastr, headers = self.headers)

    def put(self, resource, data):
        if isinstance(data, dict):
            datastr = json.dumps(data)
        elif isinstance(data, basestring):
            datastr = data
        return self.test_client.put(self.API_PREFIX + resource, data = datastr, headers = self.headers)


def cli_test(func=None, isolated_filesystem = True):
    if func is None:
        return functools.partial(cli_test, isolated_filesystem = isolated_filesystem)
    def new_func(self, *args, **kwargs):
        runner = CliRunner()
        
        try:
            if isolated_filesystem:
                with runner.isolated_filesystem():
                    func(self, runner, *args, **kwargs)
            else:
                func(self, runner, *args, **kwargs)
        except BadRequestError, bre:
            bre.print_errors()
            raise
    return new_func


class ChisubmitCLITestClient(object):
    
    def __init__(self, user_id, api_key, runner, course = None,
                 git_credentials = {}, verbose = False):
        self.user_id = user_id
        self.home_dir = "test-fs/home/%s" % self.user_id
        self.conf_dir = "%s/.chisubmit" % (self.home_dir)
        self.conf_file = self.conf_dir + "/chisubmit.conf"
        self.runner = runner
        self.verbose = verbose
        self.course = course
        
        git_credentials.update({"Testing" : "testing-credentials"})

        os.makedirs(self.home_dir)
        os.mkdir(self.conf_dir)
        with open(self.conf_file, 'w') as f:
            conf = {"api-url": "NONE",
                    "api-key": api_key,
                    "git-credentials":
                        git_credentials
                    }
            yaml.safe_dump(conf, f, default_flow_style=False)   
            
    def run(self, subcommands, params = [], course = None, catch_exceptions=False):
        chisubmit_args =  ['--testing', '--dir', self.conf_dir, '--conf', self.conf_file]
        
        if course is not None:
            chisubmit_args += ['--course', course]
        elif self.course is not None:
            chisubmit_args += ['--course', self.course]
        
        cmd_args = subcommands.split()
        cmd_args += params
        
        if self.verbose:
            l = []
            for ca in cmd_args:
                if " " in ca:
                    l.append('"%s"' % ca)
                else:
                    l.append(ca)
            s = ""
            s+= colorama.Style.BRIGHT + colorama.Fore.BLUE
            s+= "%s$" % self.user_id
            s+= colorama.Fore.WHITE
            s+= " chisubmit %s" % " ".join(l)
            s+= colorama.Style.RESET_ALL
            print s
        
        result = self.runner.invoke(chisubmit_cmd, chisubmit_args + cmd_args, catch_exceptions=catch_exceptions)
        
        if self.verbose and len(result.output) > 0:
            sys.stdout.write(result.output)
            sys.stdout.flush()
            
        return result
    
    def create_local_git_repository(self, path):
        git_path = "%s/%s" % (self.home_dir, path)
                
        repo = git.Repo.init(git_path)

        return repo, git_path

    def get_local_git_repository(self, path):
        git_path = "%s/%s" % (self.home_dir, path)
                
        repo = git.Repo(git_path)

        return repo, git_path


class BaseChisubmitTestCase(unittest.TestCase):
    
    def __init__(self, *args, **kwargs):
        super(BaseChisubmitTestCase, self).__init__(*args, **kwargs)

        self.git_server_connstr = "server_type=Testing;local_path=./test-fs/server"
        self.git_staging_connstr = "server_type=Testing;local_path=./test-fs/staging"
        self.git_server_user = None
        self.git_staging_user = None
        self.git_api_keys = {}
    
    @classmethod
    def setUpClass(cls):
        cls.server = ChisubmitAPIServer(debug = True)
        cls.db_fd, cls.db_filename = tempfile.mkstemp()
        cls.server.connect_sqlite(cls.db_filename)
            
    @classmethod
    def tearDownClass(cls):
        os.close(cls.db_fd)
        os.unlink(cls.db_filename)
    
    def set_git_server_connstr(self, connstr):
        self.git_server_connstr = connstr

    def set_git_server_user(self, user):
        self.git_server_user = user

    def set_git_staging_connstr(self, connstr):
        self.git_staging_connstr = connstr

    def set_git_staging_user(self, user):
        self.git_staging_user = user
        
    def add_api_key(self, git_type, apikey):
        self.git_api_keys[git_type] = apikey        
    
    def get_admin_test_client(self):
        return ChisubmitTestClient(self.server.app, "admin", "admin")
    
    def get_test_client(self, user = None):
        if user is None:
            return ChisubmitTestClient(self.server.app, "anonymous", None)
        else:
            return ChisubmitTestClient(self.server.app, user["id"], user["api_key"])
        
    def assert_http_code(self, response, expected):
        self.assertEquals(response.status_code, expected, "Expected HTTP response code %i, got %i" % (expected, response.status_code))
        
    
class ChisubmitTestCase(BaseChisubmitTestCase):
        
    def setUp(self):
        self.server.init_db()
        self.server.create_admin(api_key="admin")
        
        if hasattr(self, "FIXTURE"):
            load_fixture(self.server.db, self.FIXTURE)
        
        
    def tearDown(self):
        self.server.db.session.remove()
        self.server.db.drop_all()
    

class ChisubmitMultiTestCase(BaseChisubmitTestCase):
        
    @classmethod
    def setUpClass(cls):
        super(ChisubmitMultiTestCase, cls).setUpClass()
        cls.server.init_db()
        cls.server.create_admin(api_key="admin")
        
        if hasattr(cls, "FIXTURE"):
            load_fixture(cls.server.db, cls.FIXTURE)
        

    @classmethod
    def tearDownClass(cls):
        cls.server.db.session.remove()
        cls.server.db.drop_all()
        super(ChisubmitMultiTestCase, cls).tearDownClass()
    
class ChisubmitFixtureTestCase(ChisubmitMultiTestCase):
    
    def test_get_courses(self):        
        for course in self.FIXTURE["courses"].values():
            for instructor in course["instructors"]:
                c = self.get_test_client(self.FIXTURE["users"][instructor])
                response = c.get("courses")
                self.assert_http_code(response, 200)
         
                expected_ncourses = len([c for c in self.FIXTURE["courses"].values()
                                         if instructor in c["instructors"]])
         
                data = json.loads(response.get_data())        
                self.assertIn("courses", data)
                self.assertEquals(len(data["courses"]), expected_ncourses)
                 
    def test_get_course(self):
        for course in self.FIXTURE["courses"].values():
            for instructor in course["instructors"]:
                c = self.get_test_client(self.FIXTURE["users"][instructor])
                response = c.get("courses/" + course["id"])
                self.assert_http_code(response, 200)
                data = json.loads(response.get_data())        
                self.assertIn("course", data)
                self.assertEquals(data["course"]["name"], course["name"])
                 
        for course1 in self.FIXTURE["courses"].values():
            for course2 in self.FIXTURE["courses"].values():
                if course1 != course2:
                    for instructor in course1["instructors"]:    
                        c = self.get_test_client(self.FIXTURE["users"][instructor])
                        response = c.get("courses/" + course2["id"])
                        self.assert_http_code(response, 404)
 
    
def load_fixture(db, fixture):
    
    user_objs = {}
    
    for u_id, user in fixture["users"].items():
        u = User(first_name=user["first_name"], 
                   last_name=user["last_name"], 
                   id=user["id"],
                   api_key=user["api_key"])
        
        user_objs[u_id] = u
        db.session.add(u)

    for c_id, course in fixture["courses"].items():
        c = Course(id = course["id"],
                   name = course["name"])
        
        db.session.add(c)
        
        if course.has_key("instructors"):
            for instructor in course["instructors"]:
                o = user_objs[instructor]
                db.session.add(CoursesInstructors(instructor_id = o.id, 
                                                  course_id     = c.id))
        
        if course.has_key("graders"):
            for grader in course["graders"]:
                o = user_objs[grader]
                db.session.add(CoursesGraders(grader_id = o.id, 
                                              course_id = c.id))

        if course.has_key("students"):
            for student in course["students"]:
                o = user_objs[student]
                db.session.add(CoursesStudents(student_id = o.id, 
                                               course_id = c.id))

        if course.has_key("assignments"):
            for assignment in course["assignments"].values():
                db.session.add(Assignment(id = assignment["id"], 
                                          name = assignment["name"],
                                          deadline = parse(assignment["deadline"]),
                                          course_id = c.id))
    
    db.session.commit()
        
    
    
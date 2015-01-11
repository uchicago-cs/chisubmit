import tempfile
import os
import json
import yaml
import sys
import colorama
import git
import functools
import unittest
import random
import string
import re

import chisubmit.client.session as session
from click.testing import CliRunner
from chisubmit.cli import chisubmit_cmd
from dateutil.parser import parse
from chisubmit.client.session import BadRequestError

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
            
    def run(self, subcommands, params = [], course = None, cmd=chisubmit_cmd, catch_exceptions=False, cmd_input = None):
        chisubmit_args =  ['--testing', '--dir', self.conf_dir, '--conf', self.conf_file]
        
        if course is not None:
            chisubmit_args += ['--course', course]
        elif self.course is not None:
            chisubmit_args += ['--course', self.course]
        
        if subcommands is None:
            cmd_args = []
        else:
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
        
        result = self.runner.invoke(cmd, chisubmit_args + cmd_args, catch_exceptions=catch_exceptions, input=cmd_input)
        
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
        from chisubmit.backend.webapp.api import ChisubmitAPIServer

        cls.server = ChisubmitAPIServer(debug = True)
        cls.db_fd, cls.db_filename = tempfile.mkstemp()
        cls.server.connect_sqlite(cls.db_filename)
        
        password_length=random.randint(50,80)
        cls.auth_password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(password_length))
        cls.server.set_auth_testing(cls.auth_password)
            
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
    from chisubmit.backend.webapp.api.users.models import User
    from chisubmit.backend.webapp.api.assignments.models import Assignment
    from chisubmit.backend.webapp.api.courses.models import Course,\
        CoursesInstructors, CoursesGraders, CoursesStudents
        
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
        
    
class ChisubmitIntegrationTestCase(ChisubmitTestCase):
        
    def create_user(self, admin_runner, user_id):
        from chisubmit.backend.webapp.api.users.models import User

        fname = "f_" + user_id
        lname = "l_" + user_id
        email = user_id + "@example.org"
        result = admin_runner.run("admin user add", [user_id, fname, lname, email])
        self.assertEquals(result.exit_code, 0)
            
        user = User.from_id(user_id)
        self.assertIsNotNone(user)
        self.assertEquals(user.id, user_id)            
        self.assertEquals(user.first_name, fname)            
        self.assertEquals(user.last_name, lname)            
        self.assertEquals(user.email, email)      
        
        # TODO: We manually set the API key here, since the CLI
        # and the server are not completely set up for fetching
        # API keys yet. 
        user.api_key = user_id
        self.server.db.session.add(user)
        self.server.db.session.commit()

    def create_clients(self, runner, course_id, admin_id, instructor_ids, grader_ids, student_ids):
        admin = ChisubmitCLITestClient(admin_id, admin_id, runner, git_credentials=self.git_api_keys, verbose = True)
        
        instructors = []
        for instructor_id in instructor_ids:
            instructors.append(ChisubmitCLITestClient(instructor_id, instructor_id, runner, git_credentials=self.git_api_keys,  verbose = True, course = course_id))

        graders = []
        for grader_id in grader_ids:
            graders.append(ChisubmitCLITestClient(grader_id, grader_id, runner, git_credentials=self.git_api_keys,  verbose = True, course = course_id))

        students = []
        for student_id in student_ids:
            students.append(ChisubmitCLITestClient(student_id, student_id, runner, git_credentials=self.git_api_keys,  verbose = True, course = course_id))
                        
        return admin, instructors, graders, students    
            
    def create_users(self, admin, user_ids):
        for user_id in user_ids:
            self.create_user(admin, user_id)

    def create_course(self, admin, course_id, course_name):
        from chisubmit.backend.webapp.api.courses.models import Course

        result = admin.run("admin course add", [course_id, course_name])
        self.assertEquals(result.exit_code, 0)
        
        course = Course.from_id(course_id)
        self.assertIsNotNone(course)
        self.assertEquals(course.name, course_name)
        
        result = admin.run("admin course list")
        self.assertEquals(result.exit_code, 0)
        self.assertIn(course_id, result.output)
        self.assertIn(course_name, result.output)
        
        git_server_connstr = self.git_server_connstr
        git_staging_connstr = self.git_staging_connstr

        result = admin.run("admin course set-option %s git-server-connstr %s" % (course_id, git_server_connstr))
        self.assertEquals(result.exit_code, 0)

        result = admin.run("admin course set-option %s git-staging-connstr %s" % (course_id, git_staging_connstr))
        self.assertEquals(result.exit_code, 0)
        
        course = Course.from_id(course_id)
        self.assertIn("git-server-connstr", course.options)
        self.assertIn("git-staging-connstr", course.options)
        self.assertEquals(course.options["git-server-connstr"], git_server_connstr)
        self.assertEquals(course.options["git-staging-connstr"], git_staging_connstr)
        
        result = admin.run("admin course unsetup-repo %s" % (course_id))
        self.assertEquals(result.exit_code, 0)
        
        result = admin.run("admin course setup-repo %s" % (course_id))
        self.assertEquals(result.exit_code, 0)

        result = admin.run("admin course unsetup-repo %s --staging" % (course_id))
        self.assertEquals(result.exit_code, 0)

        result = admin.run("admin course setup-repo %s --staging" % (course_id))
        self.assertEquals(result.exit_code, 0)        
        
        
    def add_users_to_course(self, admin, course_id, instructors, graders, students):
        from chisubmit.backend.webapp.api.courses.models import CoursesStudents        
        
        for instructor in instructors:
            result = admin.run("admin course add-instructor %s %s" % (course_id, instructor.user_id))
            self.assertEquals(result.exit_code, 0)
        
        for grader in graders:
            result = admin.run("admin course add-grader %s %s" % (course_id, grader.user_id))
            self.assertEquals(result.exit_code, 0)
        
        for student in students:
            result = admin.run("admin course add-student %s %s" % (course_id, student.user_id))
            self.assertEquals(result.exit_code, 0)
                
        for instructor in instructors:
            if self.git_server_user is None:
                git_username = "git-" + instructors[0].user_id
            else:
                git_username = self.git_server_user
    
            result = instructors[0].run("instructor user set-repo-option", 
                                    ["instructor", instructors[0].user_id, "git-username", git_username])
            self.assertEquals(result.exit_code, 0)

        for grader in graders:
            if self.git_server_user is None:
                git_username = "git-" + graders[0].user_id
            else:
                git_username = self.git_server_user
    
            result = instructors[0].run("instructor user set-repo-option", 
                                        ["grader", graders[0].user_id, "git-username", git_username])
            self.assertEquals(result.exit_code, 0)
                
        result = admin.run("admin course update-repo-access", [course_id])
        self.assertEquals(result.exit_code, 0)
                
        result = admin.run("admin course update-repo-access", [course_id, "--staging"])
        self.assertEquals(result.exit_code, 0)
        
        for student in students:
            if self.git_server_user is None:
                git_username = "git-" + student.user_id
            else:
                git_username = self.git_server_user
                
            result = student.run("student course set-git-username", [git_username])
            self.assertEquals(result.exit_code, 0)
            
            course_student = CoursesStudents.query.filter_by(
                course_id=course_id).filter_by(
                student_id=student.user_id).first()
                
            self.assertIn("git-username", course_student.repo_info)
            self.assertEquals(course_student.repo_info["git-username"], git_username)


    def create_team_repos(self, admin, course_id, teams, students_team):
        
        team_git_paths = []
        team_git_repos = []
        team_commits = []
        
        for team, students in zip(teams, students_team):
            result = admin.run("admin course team-repo-remove", [course_id, team, "--ignore-non-existing"])
            self.assertEquals(result.exit_code, 0)
            result = admin.run("admin course team-repo-remove", ["--staging", course_id, team, "--ignore-non-existing"])
            self.assertEquals(result.exit_code, 0)

            result = admin.run("admin course team-repo-create", [course_id, team, "--public"])
            self.assertEquals(result.exit_code, 0)
            result = admin.run("admin course team-repo-create", ["--staging", course_id, team, "--public"])
            self.assertEquals(result.exit_code, 0)

        
            result = students[0].run("student team repo-check", [team])
            self.assertEquals(result.exit_code, 0)
            
            r = re.findall(r"^Repository URL: (.*)$", result.output, flags=re.MULTILINE)
            self.assertEquals(len(r), 1, "student team repo-check didn't produce the expected output")
            repo_url = r[0]

            team_git_repo, team_git_path = students[0].create_local_git_repository(team)
            team_remote = team_git_repo.create_remote("origin", repo_url)
            
            team_git_repos.append(team_git_repo)
            team_git_paths.append(team_git_path)

            commits = []
                        
            files = ["foo", "bar", "baz"]
            
            for f in files:
                open("%s/%s" % (team_git_path, f), "w").close()
                
            team_git_repo.index.add(files)
            team_git_repo.index.commit("First commit of %s" % team)
                
            commits.append(team_git_repo.heads.master.commit)
    
            team_remote.push("master")
            
            f = open("%s/foo" % (team_git_path), "w")
            f.write("Hello, team1!")
            f.close()
            
            team_git_repo.index.add(["foo"])
            team_git_repo.index.commit("Second commit of %s" % team)

            commits.append(team_git_repo.heads.master.commit)
            
            team_remote.push("master")
            
            team_commits.append(commits)
            
            
        for team1, students1 in zip(teams, students_team):
            for team2, students2 in zip(teams, students_team):
                if team1 != team2:
                    result = students1[0].run("student team repo-check", [team2])
                    self.assertNotEquals(result.exit_code, 0)
                    result = students2[0].run("student team repo-check", [team1])
                    self.assertNotEquals(result.exit_code, 0)
            
        return team_git_paths, team_git_repos, team_commits

            
    def register_team(self, student_clients, team_name, assignment_id, course_id):
        from chisubmit.backend.webapp.api.users.models import User
        from chisubmit.backend.webapp.api.teams.models import Team, StudentsTeams

        for s in student_clients:
            partners = [s2 for s2 in student_clients if s2!=s]
            partner_args = []
            for p in partners:
                partner_args += ["--partner", p.user_id]
        
            s.run("student assignment register", 
                  [ assignment_id, "--team-name", team_name] + partner_args)

            s.run("student team show", [team_name])
        
        
        students_in_team = [User.from_id(s.user_id) for s in student_clients]
        
        ts = Team.find_teams_with_students(course_id, students_in_team)
        
        self.assertGreaterEqual(len(ts), 1)
        self.assertIn(team_name, [t.id for t in ts])
        
        team = [t for t in ts if t.id == team_name]
        self.assertEqual(len(team), 1)
        t = team[0]
        self.assertEquals(t.id, team_name)
        self.assertListEqual(sorted([s.id for s in students_in_team]), 
                             sorted([s.id for s in t.students]))
        for st in t.students_teams:
            self.assertEquals(st.status, StudentsTeams.STATUS_CONFIRMED)      
    
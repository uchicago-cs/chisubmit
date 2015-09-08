import tempfile
import os
import yaml
import sys
import colorama
import git
import functools
import re
from rest_framework.test import APILiveServerTestCase

from click.testing import CliRunner
from chisubmit.client.exceptions import BadRequestException
from chisubmit.cli import chisubmit_cmd
from chisubmit.backend.api.models import Course, Student
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.conf import settings

cli_verbose = False

def set_cli_verbose(v):
    global cli_verbose
    
    cli_verbose = v

colorama.init()

COURSE1_ID = "cmsc40100"
COURSE1_NAME = "Introduction to Software Testing"
COURSE1_INSTRUCTORS = ["instructor1"]
COURSE1_GRADERS =     ["grader1", "grader2"]
COURSE1_STUDENTS =    ["student1", "student2", "student3", "student4"]
COURSE1_USERS = COURSE1_INSTRUCTORS + COURSE1_GRADERS + COURSE1_STUDENTS
COURSE1_ASSIGNMENTS = ["pa1", "pa2"]
COURSE1_RUBRICS = {"pa1": ["First Task", "Second Task"],
                   "pa2": ["First Task", "Second Task", "Third Task"],}
COURSE1_TEAMS = ["student1-student2", "student3-student4"]
COURSE1_TEAM_MEMBERS = {"student1-student2": ["student1", "student2"],
                        "student3-student4": ["student3", "student4"]}

COURSE2_ID = "cmsc40110"
COURSE2_NAME = "Advanced Software Testing"
COURSE2_INSTRUCTORS = ["instructor2"]
COURSE2_GRADERS =     ["grader3", "grader4"]
COURSE2_STUDENTS =    ["student5", "student6", "student7", "student8"]
COURSE2_USERS = COURSE2_INSTRUCTORS + COURSE2_GRADERS + COURSE2_STUDENTS
COURSE2_ASSIGNMENTS = ["hw1", "hw2"]
    
ALL_USERS = list(set(COURSE1_USERS + COURSE2_USERS + ["admin"]))


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
        except BadRequestException, bre:
            bre.print_errors()
            raise
    return new_func


class ChisubmitCLITestClient(object):
    
    def __init__(self, api_url, user_id, api_key, runner, 
                       course = None, git_credentials = {}, verbose = False):
        global cli_verbose
        
        self.user_id = user_id
        self.home_dir = "test-fs/home/%s" % self.user_id
        self.work_dir = "%s/chisubmit-test" % (self.home_dir)
        self.conf_dir = "%s/.chisubmit" % (self.work_dir)
        self.conf_file = "%s/chisubmit.conf" % (self.conf_dir)

        self.runner = runner
        if cli_verbose:
            self.verbose = True
        else:
            self.verbose = verbose
        self.course = course
        
        git_credentials.update({"Testing" : "testing-credentials"})

        os.makedirs(self.home_dir)
        os.mkdir(self.work_dir)
        os.mkdir(self.conf_dir)
        with open(self.conf_file, 'w') as f:
            conf = {"api-url": api_url,
                    "api-key": api_key,
                    "git-credentials":
                        git_credentials
                    }
            yaml.safe_dump(conf, f, default_flow_style=False)   
            
    def run(self, subcommands, params = [], course = None, cmd=chisubmit_cmd, catch_exceptions=False, cmd_input = None):
        chisubmit_args = ['--debug', '--work-dir', self.work_dir, '--config-dir', self.conf_dir]
        
        if course is not None:
            chisubmit_args += ['-c', "course={}".format(course)]
        elif self.course is not None:
            chisubmit_args += ['-c', "course={}".format(self.course)]
        
        if subcommands is None:
            cmd_args = []
        else:
            cmd_args = subcommands.split()

        cmd_args += params

        if self.verbose:
            global cli_verbose
            if cli_verbose:
                print
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


class ChisubmitCLITestCase(APILiveServerTestCase):
    
    def __init__(self, *args, **kwargs):
        super(ChisubmitCLITestCase, self).__init__(*args, **kwargs)

        if settings.DEBUG == False:
            settings.DEBUG = True

        self.git_server_connstr = "server_type=Testing;local_path=./test-fs/server"
        self.git_staging_connstr = "server_type=Testing;local_path=./test-fs/staging"
        self.git_server_user = None
        self.git_staging_user = None
        self.git_api_keys = {}
    
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
    
    def assert_http_code(self, response, expected):
        self.assertEquals(response.status_code, expected, "Expected HTTP response code %i, got %i" % (expected, response.status_code))                
        
    def create_user(self, admin_runner, username):
        fname = "f_" + username
        lname = "l_" + username
        email = username + "@example.org"
        result = admin_runner.run("admin user add", [username, fname, lname, email])
        self.assertEquals(result.exit_code, 0)
            
        try:
            user_obj = User.objects.get(username=username)
        except User.DoesNotExist:
            self.fail("User was not added to database")              

        self.assertEquals(user_obj.username, username)            
        self.assertEquals(user_obj.first_name, fname)            
        self.assertEquals(user_obj.last_name, lname)            
        self.assertEquals(user_obj.email, email)      
        
        # Creating a custom token cannot be done throught the API or CLI, so
        # we create a Token object directly.
        Token.objects.create(key=username+"token", user=user_obj)

    def create_clients(self, runner, admin_id, instructor_ids = [], grader_ids = [], student_ids = [], course_id=None, verbose=False):
        base_url = self.live_server_url + "/api/v1"
        
        admin = ChisubmitCLITestClient(base_url, admin_id, admin_id+"token", runner, git_credentials=self.git_api_keys, verbose = verbose)
        
        instructors = []
        for instructor_id in instructor_ids:
            instructors.append(ChisubmitCLITestClient(base_url, instructor_id, instructor_id+"token", runner, git_credentials=self.git_api_keys,  verbose = verbose, course = course_id))

        graders = []
        for grader_id in grader_ids:
            graders.append(ChisubmitCLITestClient(base_url, grader_id, grader_id+"token", runner, git_credentials=self.git_api_keys,  verbose = verbose, course = course_id))

        students = []
        for student_id in student_ids:
            students.append(ChisubmitCLITestClient(base_url, student_id, student_id+"token", runner, git_credentials=self.git_api_keys,  verbose = verbose, course = course_id))
                        
        return admin, instructors, graders, students    
            
    def create_users(self, admin, user_ids):
        for user_id in user_ids:
            self.create_user(admin, user_id)

    def create_course(self, admin, course_id, course_name):
        result = admin.run("admin course add", [course_id, course_name])
        self.assertEquals(result.exit_code, 0)
        
        course = Course.get_by_course_id(course_id)
        self.assertIsNotNone(course)
        self.assertEquals(course.name, course_name)
        
        result = admin.run("admin course list")
        self.assertEquals(result.exit_code, 0)
        self.assertIn(course_id, result.output)
        self.assertIn(course_name, result.output)

        result = admin.run("admin course set-attribute %s git_usernames custom" % (course_id))
        self.assertEquals(result.exit_code, 0)
        
        git_server_connstr = self.git_server_connstr
        git_staging_connstr = self.git_staging_connstr

        result = admin.run("admin course set-attribute %s git_server_connstr %s" % (course_id, git_server_connstr))
        self.assertEquals(result.exit_code, 0)

        result = admin.run("admin course set-attribute %s git_staging_connstr %s" % (course_id, git_staging_connstr))
        self.assertEquals(result.exit_code, 0)
        
        course = Course.get_by_course_id(course_id)
        self.assertEquals(course.git_server_connstr, git_server_connstr)
        self.assertEquals(course.git_staging_connstr, git_staging_connstr)
        
        result = admin.run("admin course unsetup-repo %s" % (course_id))
        self.assertEquals(result.exit_code, 0)
        
        result = admin.run("admin course setup-repo %s" % (course_id))
        self.assertEquals(result.exit_code, 0)

        result = admin.run("admin course unsetup-repo %s --staging" % (course_id))
        self.assertEquals(result.exit_code, 0)

        result = admin.run("admin course setup-repo %s --staging" % (course_id))
        self.assertEquals(result.exit_code, 0)        
        
        
    def add_users_to_course(self, admin, course_id, instructors, graders, students):  
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
    
            result = instructors[0].run("instructor course set-user-attribute", 
                                    ["instructor", instructors[0].user_id, "git_username", git_username])
            self.assertEquals(result.exit_code, 0)

            if self.git_staging_user is None:
                git_staging_username = "git-" + instructors[0].user_id
            else:
                git_staging_username = self.git_staging_user
    
            result = instructors[0].run("instructor course set-user-attribute", 
                                    ["instructor", instructors[0].user_id, "git_staging_username", git_staging_username])
            self.assertEquals(result.exit_code, 0)


        for grader in graders:
            if self.git_server_user is None:
                git_username = "git-" + graders[0].user_id
            else:
                git_username = self.git_server_user
    
            result = instructors[0].run("instructor course set-user-attribute", 
                                        ["grader", graders[0].user_id, "git_username", git_username])
            self.assertEquals(result.exit_code, 0)

            if self.git_staging_user is None:
                git_staging_username = "git-" + graders[0].user_id
            else:
                git_staging_username = self.git_staging_user
    
            result = instructors[0].run("instructor course set-user-attribute", 
                                    ["grader", graders[0].user_id, "git_staging_username", git_staging_username])
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
            
            student_obj = Student.objects.get(course__course_id = course_id, user__username = student.user_id)
                
            self.assertEquals(student_obj.git_username, git_username)


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
        for s in student_clients:
            partners = [s2 for s2 in student_clients if s2!=s]
            partner_args = []
            for p in partners:
                partner_args += ["--partner", p.user_id]
        
            s.run("student assignment register", 
                  [ assignment_id ] + partner_args)

            s.run("student team show", [team_name])
        
        return 
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
    
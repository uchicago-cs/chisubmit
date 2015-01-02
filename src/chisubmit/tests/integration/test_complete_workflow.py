from chisubmit.tests.common import cli_test, ChisubmitCLITestClient, ChisubmitTestCase
from chisubmit.backend.webapp.api.courses.models import Course, CoursesStudents
from chisubmit.backend.webapp.api.users.models import User
from chisubmit.backend.webapp.api.teams.models import Team, StudentsTeams
from chisubmit.common.utils import get_datetime_now_utc, convert_datetime_to_local
from chisubmit.client.session import BadRequestError
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL

from datetime import timedelta
import re

class CLICompleteWorkflow(ChisubmitTestCase):
            
    def create_user(self, admin_runner, user_id):
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
            
    def register_team(self, student_clients, team_name, assignment_id, course_id):
        
        for s in student_clients:
            partners = [s2 for s2 in student_clients if s2!=s]
            partner_args = []
            for p in partners:
                partner_args += ["--partner", p.user_id]
        
            s.run("student register-for-assignment", 
                  [ assignment_id, "--team-name", team_name] + partner_args)
        
        
        students_in_team = [User.from_id(s.user_id) for s in student_clients]
        
        t = Team.find_teams_with_students(course_id, students_in_team)
        
        self.assertEquals(len(t), 1)
        t = t[0]
        self.assertEquals(t.id, team_name)
        self.assertListEqual(sorted([s.id for s in students_in_team]), 
                             sorted([s.id for s in t.students]))
        for st in t.students_teams:
            self.assertEquals(st.status, StudentsTeams.STATUS_CONFIRMED)        
            

    @cli_test
    def test_complete_workflow(self, runner):
        course_id = u"cmsc40200"
        course_name = u"Foobarmentals of Foobar"

        admin_id = u"admin"
        instructor_id = u"instructor"
        grader_id = u"grader"
        student_ids = [u"student1", u"student2", u"student3", u"student4"]
        
        team_name1 = "the-flaming-foobars"
        team_name2 = "the-magnificent-mallocs"
        
        if self.git_api_keys is not None and len(self.git_api_keys) > 0:
            git_credentials = self.git_api_keys
        else:
            git_credentials = {}
        
        admin = ChisubmitCLITestClient(admin_id, admin_id, runner, git_credentials=git_credentials, verbose = True)
        instructor = ChisubmitCLITestClient(instructor_id, instructor_id, runner, git_credentials=git_credentials,  verbose = True, course = "cmsc40200")
        grader = ChisubmitCLITestClient(grader_id, grader_id, runner, git_credentials=git_credentials,  verbose = True, course = "cmsc40200")
        student = [ChisubmitCLITestClient(s, s, runner, git_credentials=git_credentials,  verbose = True, course = "cmsc40200") for s in student_ids]

        students_team1 = student[0:2]
        students_team2 = student[2:4]

        print

        # Create users
        self.create_user(admin, instructor_id)
        self.create_user(admin, grader_id)
        for s in student_ids:
            self.create_user(admin, s)
        
        # Create course        
        result = admin.run("admin course add", [course_id, course_name])
        self.assertEquals(result.exit_code, 0)
        
        course = Course.from_id(course_id)
        self.assertIsNotNone(course)
        self.assertEquals(course.name, course_name)
        
        result = admin.run("admin course list")
        self.assertEquals(result.exit_code, 0)
        self.assertIn(course_id, result.output)
        self.assertIn(course_name, result.output)
        
        result = admin.run("admin course add-instructor %s %s" % (course_id, instructor_id))
        self.assertEquals(result.exit_code, 0)
        
        result = admin.run("admin course add-grader %s %s" % (course_id, grader_id))
        self.assertEquals(result.exit_code, 0)
        
        for s in student_ids:
            result = admin.run("admin course add-student %s %s" % (course_id, s))
            self.assertEquals(result.exit_code, 0)

        git_server_connstr = self.git_server_connstr
        git_staging_connstr = self.git_staging_connstr

        result = admin.run("admin course set-option %s git-server-connstr %s" % (course_id, git_server_connstr))
        self.assertEquals(result.exit_code, 0)

        result = admin.run("admin course set-option %s git-staging-connstr %s" % (course_id, git_staging_connstr))
        self.assertEquals(result.exit_code, 0)

        result = admin.run("admin course set-option %s default-extensions 2" % (course_id))
        self.assertEquals(result.exit_code, 0)
        
        course = Course.from_id(course_id)
        self.assertIn("git-server-connstr", course.options)
        self.assertIn("git-staging-connstr", course.options)
        self.assertEquals(course.options["git-server-connstr"], git_server_connstr)
        self.assertEquals(course.options["git-staging-connstr"], git_staging_connstr)

        if self.git_server_user is None:
            git_username = "git" + instructor_id
        else:
            git_username = self.git_server_user

        result = instructor.run("instructor user set-repo-option", 
                                ["instructor", instructor_id, "git-username", git_username])
        self.assertEquals(result.exit_code, 0)

        if self.git_server_user is None:
            git_username = "git" + grader_id
        else:
            git_username = self.git_server_user

        result = instructor.run("instructor user set-repo-option", 
                                ["grader", grader_id, "git-username", git_username])
        self.assertEquals(result.exit_code, 0)

        deadline = get_datetime_now_utc() - timedelta(hours=23)
        deadline = convert_datetime_to_local(deadline)
        deadline = deadline.replace(tzinfo=None).isoformat(sep=" ")        

        result = instructor.run("instructor assignment add", 
                                ["pa1", "Programming Assignment 1", deadline])
        self.assertEquals(result.exit_code, 0)


        deadline = get_datetime_now_utc() - timedelta(hours=49)
        deadline = deadline.isoformat(sep=" ")

        result = instructor.run("instructor assignment add", 
                                ["pa2", "Programming Assignment 2", deadline])
        self.assertEquals(result.exit_code, 0)
        
        
        result = admin.run("admin course show", ["--include-users", "--include-assignments", course_id])
        self.assertEquals(result.exit_code, 0)

        for s in student:
            if self.git_server_user is None:
                git_username = "git" + s.user_id
            else:
                git_username = self.git_server_user
            result = s.run("student set-git-username", [git_username])
            self.assertEquals(result.exit_code, 0)
            
            course_student = CoursesStudents.query.filter_by(
                course_id=course_id).filter_by(
                student_id=s.user_id).first()
                
            self.assertIn("git-username", course_student.repo_info)
            self.assertEquals(course_student.repo_info["git-username"], git_username)
        
        
        
        self.register_team(students_team1, team_name1, "pa1", course_id)
        self.register_team(students_team1, team_name1, "pa2", course_id)

        self.register_team(students_team2, team_name2, "pa1", course_id)


        result = instructor.run("instructor team repo-create", [team_name1])
        self.assertEquals(result.exit_code, 0)
        result = instructor.run("instructor team repo-create", ["--staging", team_name1])
        self.assertEquals(result.exit_code, 0)

        result = instructor.run("instructor team repo-create", [team_name2])
        self.assertEquals(result.exit_code, 0)
        result = instructor.run("instructor team repo-create", ["--staging", team_name2])
        self.assertEquals(result.exit_code, 0)
        
        result = student[0].run("student repo-check", [team_name1])
        self.assertEquals(result.exit_code, 0)
        
        r = re.findall(r"^Repository URL: (.*)$", result.output, flags=re.MULTILINE)
        self.assertEquals(len(r), 1, "student repo-check didn't produce the expected output")
        team1_remote_repo = r[0]
        
        result = student[2].run("student repo-check", [team_name2])
        self.assertEquals(result.exit_code, 0)

        r = re.findall(r"^Repository URL: (.*)$", result.output, flags=re.MULTILINE)
        self.assertEquals(len(r), 1, "student repo-check didn't produce the expected output")
        team2_remote_repo = r[0]

        result = student[0].run("student repo-check", [team_name2])
        self.assertNotEquals(result.exit_code, 0)
        result = student[2].run("student repo-check", [team_name1])
        self.assertNotEquals(result.exit_code, 0)

        team1_git_repo, team1_git_path = students_team1[0].create_local_git_repository(team_name1)
        team2_git_repo, team2_git_path = students_team2[0].create_local_git_repository(team_name1)

        team1_remote = team1_git_repo.create_remote("origin", team1_remote_repo)
        team2_remote = team2_git_repo.create_remote("origin", team2_remote_repo)
        
        files = ["foo", "bar", "baz"]
        
        for f in files:
            open("%s/%s" % (team1_git_path, f), "w").close()
        
        for f in files:
            open("%s/%s" % (team2_git_path, f), "w").close()

        team1_git_repo.index.add(files)
        team1_git_repo.index.commit("First commit of team1")
        
        team2_git_repo.index.add(files)
        team2_git_repo.index.commit("First commit of team2")

        team1_commit1 = team1_git_repo.heads.master.commit
        team2_commit1 = team2_git_repo.heads.master.commit

        team1_remote.push("master")
        team2_remote.push("master")
        
        f = open("%s/foo" % (team1_git_path), "w")
        f.write("Hello, team1!")
        f.close()
        
        f = open("%s/foo" % (team2_git_path), "w")
        f.write("Hello, team2!")
        f.close()
        
        team1_git_repo.index.add(["foo"])
        team1_git_repo.index.commit("Second commit of team1")
        
        team2_git_repo.index.add(["foo"])
        team2_git_repo.index.commit("Second commit of team2")
                
        team1_remote.push("master")
        team2_remote.push("master")      
        
        team1_commit2 = team1_git_repo.heads.master.commit
        team2_commit2 = team2_git_repo.heads.master.commit
                
        
        # Try to submit without enough extensions
        result = student[0].run("student submit-assignment", 
                                [team_name1, "pa1", team1_commit1.hexsha, 
                                 "--extensions", "0",
                                 "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_FAIL)
        
        # Try to submit with too many extensions
        result = student[0].run("student submit-assignment", 
                                [team_name1, "pa1", team1_commit1.hexsha, 
                                 "--extensions", "2",
                                 "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_FAIL)

        # Submit with just the right number
        result = student[0].run("student submit-assignment", 
                                [team_name1, "pa1", team1_commit1.hexsha, 
                                 "--extensions", "1",
                                 "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)

        # Try submitting an already-submitted assignment
        result = student[0].run("student submit-assignment", 
                                [team_name1, "pa1", team1_commit2.hexsha, 
                                 "--extensions", "1",
                                 "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_FAIL)
        
        # Submit an already-submitted assignment
        result = student[0].run("student submit-assignment", 
                                [team_name1, "pa1", team1_commit2.hexsha, 
                                 "--extensions", "1",
                                 "--yes", "--force"])
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)        
        
        # Try requesting more extensions than the team has
        result = student[0].run("student submit-assignment", 
                                [team_name1, "pa2", team1_commit2.hexsha, 
                                 "--extensions", "3",
                                 "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_FAIL)
        
        # Try submitting for a project the team is not registered for
        with self.assertRaises(BadRequestError) as cm:
            student[2].run("student submit-assignment", 
                           [team_name2, "pa2", team2_commit2.hexsha, 
                           "--extensions", "0",
                           "--yes"])        

        bre = cm.exception
        bre.print_errors()
        
        
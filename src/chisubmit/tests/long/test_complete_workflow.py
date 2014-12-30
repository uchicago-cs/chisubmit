from chisubmit.tests.common import cli_test, ChisubmitCLITestClient, ChisubmitTestCase
import unittest
from chisubmit.backend.webapp.api.courses.models import Course
from chisubmit.backend.webapp.api.users.models import User

class CLICompleteWorkflow(ChisubmitTestCase, unittest.TestCase):
            
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
            
    @cli_test
    def test_complete_workflow(self, runner):
        course_id = u"cmsc40200"
        course_name = u"Foobarmentals of Foobar"

        admin_id = u"admin"
        instructor_id = u"instructor"
        grader_id = u"grader"
        student_ids = [u"student1", u"student2", u"student3", u"student4"]
        
        admin = ChisubmitCLITestClient(admin_id, admin_id, runner, verbose = True)
        instructor = ChisubmitCLITestClient(instructor_id, instructor_id, runner, verbose = True)
        grader = ChisubmitCLITestClient(grader_id, grader_id, runner, verbose = True)
        student = [ChisubmitCLITestClient(s, s, runner, verbose = True) for s in student_ids]

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

        git_server_connstr = "server_type=local;path=./server"
        git_staging_connstr = "server_type=local;path=./staging"

        result = admin.run("admin course set-option %s git-server-connstr %s" % (course_id, git_server_connstr))
        self.assertEquals(result.exit_code, 0)

        result = admin.run("admin course set-option %s git-staging-connstr %s" % (course_id, git_staging_connstr))
        self.assertEquals(result.exit_code, 0)
        
        course = Course.from_id(course_id)
        self.assertIn("git-server-connstr", course.options)
        self.assertIn("git-staging-connstr", course.options)
        self.assertEquals(course.options["git-server-connstr"], git_server_connstr)
        self.assertEquals(course.options["git-staging-connstr"], git_staging_connstr)


        result = instructor.run("instructor assignment add", 
                                ["pa1", "Programming Assignment 1", "2042-01-21T20:00"],
                                course = "cmsc40200")
        self.assertEquals(result.exit_code, 0)

        
        
        result = admin.run("admin course show", ["--include-users", "--include-assignments", course_id])
        self.assertEquals(result.exit_code, 0)
        
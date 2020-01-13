from __future__ import print_function
from builtins import zip
from chisubmit.tests.common import cli_test, ChisubmitCLITestCase
from chisubmit.common.utils import get_datetime_now_utc, set_testing_now, convert_datetime_to_local
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL

from datetime import timedelta
from chisubmit.backend.api.models import Course

class CLICompleteWorkflowGradescope(ChisubmitCLITestCase):
            
    fixtures = ['admin_user']
            
    @cli_test
    def test_complete_with_gradescope(self, runner):
        course_id = u"cmsc40300"
        course_name = u"Foobarmentals of Foobar II"

        admin_id = u"admin"
        instructor_ids = [u"instructor"]
        grader_ids= [u"grader"]
        student_ids = [u"student1", u"student2", u"student3", u"student4"]
        
        all_users = instructor_ids + grader_ids + student_ids
        
        admin, instructors, graders, students = self.create_clients(runner, admin_id, instructor_ids, grader_ids, student_ids, course_id, gradescope_api_key="gradescope-testing", verbose = True)
        self.create_users(admin, all_users)
        
        self.create_course(admin, course_id, course_name)
        
        course = Course.get_by_course_id(course_id)
        self.assertIsNotNone(course)
        self.assertEqual(course.name, course_name)

        result = admin.run("admin course set-attribute %s gradescope_id 4242" % (course_id))
        self.assertEqual(result.exit_code, 0)

        self.add_users_to_course(admin, course_id, instructors, graders, students)
        
        deadline = get_datetime_now_utc() + timedelta(hours=1)
        deadline = convert_datetime_to_local(deadline)
        deadline = deadline.replace(tzinfo=None).isoformat(sep=" ")

        result = instructors[0].run("instructor assignment add", 
                                    ["pa1", "Programming Assignment 1", deadline])
        self.assertEqual(result.exit_code, 0)
        
        result = instructors[0].run("instructor assignment set-attribute", 
                                    ["pa1", "max_students", "2"])
        self.assertEqual(result.exit_code, 0)
        
        result = instructors[0].run("instructor assignment set-attribute", 
                                    ["pa1", "gradescope_id", "3737"])
        self.assertEqual(result.exit_code, 0)

        result = instructors[0].run("instructor assignment set-attribute",
                                    ["pa1", "expected_files", "foo,b*,qux"])
        self.assertEqual(result.exit_code, 0)
            
        teams = [u"student1-student2", 
                 u"student3-student4"]        

        students_team = [ (students[0], students[1]),
                          (students[2], students[3])]
        

        self.register_team(students_team[0], teams[0], "pa1", course_id)
        self.register_team(students_team[1], teams[1], "pa1", course_id)
        
        _, _, team_commits = self.create_team_repos(admin, course_id, teams[0:2], students_team[0:2])
                
        # Team 0 and 1 submit
        result = students_team[0][0].run("student assignment submit", 
                                         ["pa1", "--yes"])        
        self.assertEqual(result.exit_code, CHISUBMIT_SUCCESS)

        result = students_team[1][0].run("student assignment submit",
                                         ["pa1", "--yes"])        
        self.assertEqual(result.exit_code, CHISUBMIT_SUCCESS)

        for team, student_team in zip(teams, students_team):
            result = student_team[0].run("student team show", [team])
            self.assertEqual(result.exit_code, CHISUBMIT_SUCCESS)

        # Let the deadline "pass"
        new_now = get_datetime_now_utc() + timedelta(hours=2)
        set_testing_now(new_now)

        print()
        print("~~~ Time has moved 'forward' by two hours ~~~")
        print()

        # Instructor uploads to Gradescope. Both repos should be skipped
        # because we haven't created the the grading repos yet
        result = instructors[0].run("instructor grading gradescope-upload", ["--dry-run", "pa1"])
        self.assertEqual(result.exit_code, 0)

        # Instructor creates grading repos
        result = instructors[0].run("instructor grading create-grading-repos", ["--master", "pa1"])
        self.assertEqual(result.exit_code, 0)
        
        # Instructor uploads to Gradescope. Both repos should be skipped
        # because they're missing required file "qux"
        result = instructors[0].run("instructor grading gradescope-upload", ["--dry-run", "pa1"])
        self.assertEqual(result.exit_code, 0)

        # We change the list of expected files
        result = instructors[0].run("instructor assignment set-attribute",
                                    ["pa1", "expected_files", "foo,b*"])
        self.assertEqual(result.exit_code, 0)

        # Instructor uploads to Gradescope. Both repos should be uploaded
        # (but we're running in dry-run mode, so we don't actually contact
        # Gradescope)
        result = instructors[0].run("instructor grading gradescope-upload", ["--dry-run", "pa1"])
        self.assertEqual(result.exit_code, 0)

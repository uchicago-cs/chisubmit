from chisubmit.tests.common import cli_test, ChisubmitCLITestCase
from chisubmit.common.utils import get_datetime_now_utc, set_testing_now
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL

from datetime import timedelta
from chisubmit.backend.api.models import Course

class CLICompleteWorkflowCancelRegistration(ChisubmitCLITestCase):
            
    fixtures = ['admin_user']
            
    @cli_test
    def test_complete_with_registration_cancellation(self, runner):
        course_id = u"cmsc40300"
        course_name = u"Foobarmentals of Foobar II"

        admin_id = u"admin"
        instructor_ids = [u"instructor"]
        grader_ids= [u"grader"]
        student_ids = [u"student1", u"student2", u"student3", u"student4"]
        
        all_users = instructor_ids + grader_ids + student_ids
        
        admin, instructors, graders, students = self.create_clients(runner, admin_id, instructor_ids, grader_ids, student_ids, course_id, verbose = True)
        self.create_users(admin, all_users)
        
        self.create_course(admin, course_id, course_name)
        
        course = Course.get_by_course_id(course_id)
        self.assertIsNotNone(course)
        self.assertEquals(course.name, course_name)        

        result = admin.run("admin course set-attribute %s default_extensions 2" % (course_id))
        self.assertEquals(result.exit_code, 0)
        
        result = admin.run("admin course set-attribute %s extension_policy per-student" % (course_id))
        self.assertEquals(result.exit_code, 0)
        
        self.add_users_to_course(admin, course_id, instructors, graders, students)
        
        deadline = get_datetime_now_utc() - timedelta(minutes=5)
        deadline = deadline.isoformat(sep=" ")

        result = instructors[0].run("instructor assignment add", 
                                    ["pa1", "Programming Assignment 1", deadline])
        self.assertEquals(result.exit_code, 0)
        
        result = instructors[0].run("instructor assignment set-attribute", 
                                    ["pa1", "max_students", "2"])
        self.assertEquals(result.exit_code, 0)        
            
        teams = [u"student1-student2", 
                 u"student3-student4"]        

        students_team = [ (students[0], students[1]),
                          (students[2], students[3])]
        

        self.register_team(students_team[0], teams[0], "pa1", course_id)
        self.register_team(students_team[1], teams[1], "pa1", course_id)
        
        _, _, team_commits = self.create_team_repos(admin, course_id, teams[0:2], students_team[0:2])
                
        # Team 0 cancels their registration, which they can do because they haven't submitted yet. 
        result = students_team[0][0].run("student assignment cancel-registration", 
                                         ["pa1", "--yes"])        
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)
        
        # Team 0 tries to cancel their registration again, which doesn't work. There's nothing to cancel.
        result = students_team[0][0].run("student assignment cancel-registration", 
                                         ["pa1", "--yes"])        
        self.assertEquals(result.exit_code, CHISUBMIT_FAIL)
        
        # Team 0 registers again     
        result = students_team[0][0].run("student assignment register", 
                                         ["pa1", "--partner", students_team[0][1].user_id])        
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)           
        
        # Team 1 submits.
        result = students_team[1][0].run("student assignment submit", 
                                         ["pa1", "--yes"])        
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)

        # Team 1 tries to cancel their registration, which doesn't work. They have a submission.
        result = students_team[1][0].run("student assignment cancel-registration", 
                                         ["pa1", "--yes"])        
        self.assertEquals(result.exit_code, CHISUBMIT_FAIL)        

        # Team 1 cancels their submission
        result = students_team[1][0].run("student assignment cancel-submit", 
                                         ["pa1", "--yes"])        
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)        

        # Team 1 can now cancel their registration.
        result = students_team[1][0].run("student assignment cancel-registration", 
                                         ["pa1", "--yes"])        
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)        


        for team, student_team in zip(teams, students_team):
            result = student_team[0].run("student team show", [team])
            self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)

        
        

from chisubmit.tests.common import cli_test, ChisubmitIntegrationTestCase
from chisubmit.common.utils import get_datetime_now_utc, set_testing_now
from chisubmit.common import CHISUBMIT_SUCCESS, CHISUBMIT_FAIL

from datetime import timedelta
import time

class CLICompleteWorkflowCancelSubmission(ChisubmitIntegrationTestCase):
            
    @cli_test
    def test_complete_with_submission_cancelling(self, runner):
        course_id = u"cmsc40300"
        course_name = u"Foobarmentals of Foobar II"

        admin_id = u"admin"
        instructor_ids = [u"instructor"]
        grader_ids= [u"grader"]
        student_ids = [u"student1", u"student2", u"student3", u"student4"]
        
        all_users = instructor_ids + grader_ids + student_ids
        
        admin, instructors, graders, students = self.create_clients(runner, course_id, admin_id, instructor_ids, grader_ids, student_ids)
        self.create_users(admin, all_users)
        
        self.create_course(admin, course_id, course_name)

        result = admin.run("admin course set-option %s default-extensions 3" % (course_id))
        self.assertEquals(result.exit_code, 0)
        
        result = admin.run("admin course set-option %s extension-policy per_student" % (course_id))
        self.assertEquals(result.exit_code, 0)
        
        self.add_users_to_course(admin, course_id, instructors, graders, students)
        
        deadline = get_datetime_now_utc() - timedelta(hours=23)
        deadline = deadline.isoformat(sep=" ")

        result = instructors[0].run("instructor assignment add", 
                                    ["pa1", "Programming Assignment 1", deadline])
        self.assertEquals(result.exit_code, 0)
        
        teams = [u"the-flaming-foobars", 
                 u"the-magnificent-mallocs"]        

        students_team = [ (students[0], students[1]),
                          (students[2], students[3])]
        

        self.register_team(students_team[0], teams[0], "pa1", course_id)
        self.register_team(students_team[1], teams[1], "pa1", course_id)
        
        _, _, team_commits = self.create_team_repos(admin, course_id, teams[0:2], students_team[0:2])
        

        # Team 0 cancels their submission
        # Fails because there is nothing to cancel
        result = students_team[0][0].run("student assignment cancel-submit", 
                                         [teams[0], "pa1", "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_FAIL)           

        
        # Team 0 and 1 submit with one extension to pa1
        result = students_team[0][0].run("student assignment submit", 
                                         [teams[0], "pa1", team_commits[0][0].hexsha, 
                                          "--extensions", "1",
                                          "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)
        
        result = students_team[1][0].run("student assignment submit", 
                                         [teams[1], "pa1", team_commits[1][0].hexsha, 
                                          "--extensions", "1",
                                          "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)


        # Team 0 cancels their submission
        result = students_team[0][0].run("student assignment cancel-submit", 
                                         [teams[0], "pa1", "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)

        
        # Team 0 cancels their submission (again)
        # Fails because there is nothing to cancel
        result = students_team[0][0].run("student assignment cancel-submit", 
                                         [teams[0], "pa1", "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_FAIL)        


        # Team 1 resubmits and is successful because the deadline hasn't passed yet
        result = students_team[1][0].run("student assignment submit", 
                                         [teams[1], "pa1", team_commits[1][1].hexsha, 
                                          "--extensions", "1",
                                          "--force",
                                          "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)

        
        # Let the deadline "pass"
        new_now = get_datetime_now_utc() + timedelta(hours=2)
        set_testing_now(new_now)

        print
        print "~~~ Time has moved 'forward' by two hours ~~~"
        print
        
        # Team 0 submits and is successful because they cancelled their previous submission
        result = students_team[0][0].run("student assignment submit", 
                                         [teams[0], "pa1", team_commits[0][1].hexsha, 
                                          "--extensions", "2",
                                          "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)


        # Team 1 submits and fails because their previous submission is final
        result = students_team[1][0].run("student assignment submit", 
                                         [teams[1], "pa1", team_commits[1][0].hexsha, 
                                          "--extensions", "2",
                                          "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_FAIL)
        
        # Team 1 cancels their submission
        # Fails because the previous submission is final
        result = students_team[1][0].run("student assignment cancel-submit", 
                                         [teams[1], "pa1", "--yes"])
        self.assertEquals(result.exit_code, CHISUBMIT_FAIL)        
 

        for team, student_team in zip(teams, students_team):
            result = student_team[0].run("student team show", [team])
            self.assertEquals(result.exit_code, CHISUBMIT_SUCCESS)

        
        

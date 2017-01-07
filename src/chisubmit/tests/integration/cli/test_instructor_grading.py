from chisubmit.tests.common import cli_test, ChisubmitCLITestCase

class CLIInstructorGrades(ChisubmitCLITestCase):
            
    fixtures = ['users', 'course1', 'course1_users', 'course1_teams', 
                     'course1_pa1', 'course1_pa1_registrations_with_submissions',
                     'course1_pa1_grades',
                     'course1_pa2']
                
    @cli_test
    def test_instructor_list_grades(self, runner):
        _, instructors, _, _ = self.create_clients(runner, "admin", instructor_ids=["instructor1"], course_id="cmsc40100")
        
        instructor1 = instructors[0]
        
        result = instructor1.run("instructor grading list-grades --detailed")
        self.assertEquals(result.exit_code, 0)
        
    @cli_test
    def test_instructor_grading_status(self, runner):
        _, instructors, _, _ = self.create_clients(runner, "admin", instructor_ids=["instructor1"], course_id="cmsc40100")
        
        instructor1 = instructors[0]
        
        result = instructor1.run("instructor grading show-grading-status --use-stored-grades --by-grader", ["pa1"])
        self.assertEquals(result.exit_code, 0)
from chisubmit.tests.common import ChisubmitMultiTestCase, cli_test,\
    ChisubmitCLITestClient, ChisubmitTestCase
from chisubmit.tests.fixtures import users_and_courses
from chisubmit.backend.api.models import Course
    
    
class CLIAdminCourse(ChisubmitTestCase):
            
    @cli_test
    def test_admin_course_add(self, runner):
        
        admin = ChisubmitCLITestClient("admin", "admin", runner)
        
        course_id = u"cmsc12300"
        course_name = u"Foobarmentals of Foobar"
        
        result = admin.run("admin course add", [course_id, course_name])
        self.assertEquals(result.exit_code, 0)
        
        course = Course.get_by_course_id(course_id)
        self.assertIsNotNone(course)
        self.assertEquals(course.name, course_name)
 
        
class CLIAdminCourseFixture(ChisubmitMultiTestCase):
    
    fixtures = ['users', 'complete_course1']
        
    @cli_test
    def test_admin_course_list(self, runner):
        admin = ChisubmitCLITestClient("admin", "admin", runner)
        
        result = admin.run("admin course list")

        self.assertEquals(result.exit_code, 0)

        print result.output
        #for course in self.FIXTURE["courses"].values():            
        #    self.assertIn(course["name"], result.output)
            
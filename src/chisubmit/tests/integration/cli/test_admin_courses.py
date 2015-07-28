from chisubmit.tests.common import cli_test, ChisubmitCLITestClient, ChisubmitCLITestCase,\
    COURSE1_ID, COURSE1_NAME, COURSE2_ID, COURSE2_NAME
from chisubmit.backend.api.models import Course

class CLIAdminCourse(ChisubmitCLITestCase):
            
    fixtures = ['admin_user']
            
    @cli_test
    def test_admin_course_add(self, runner):
        
        admin, _, _, _ = self.create_clients(runner, "admin")
        
        course_id = u"cmsc12300"
        course_name = u"Foobarmentals of Foobar"
        
        result = admin.run("admin course add", [course_id, course_name])
        self.assertEquals(result.exit_code, 0)
        
        try:
            course_obj = Course.objects.get(course_id=course_id)
        except Course.DoesNotExist:
            self.fail("Course was not added to database")  
            
        self.assertEquals(course_obj.course_id, course_id)                  
        self.assertEquals(course_obj.name, course_name) 
           
        
class CLIAdminCourseFixture(ChisubmitCLITestCase):
    
    fixtures = ['users', 'course1', 'course2']
        
    @cli_test
    def test_admin_course_list(self, runner):
        admin, _, _, _ = self.create_clients(runner, "admin")
        
        result = admin.run("admin course list")

        self.assertEquals(result.exit_code, 0)

        for val in [COURSE1_ID, COURSE1_NAME, COURSE2_ID, COURSE2_NAME]:            
            self.assertIn(val, result.output)
            
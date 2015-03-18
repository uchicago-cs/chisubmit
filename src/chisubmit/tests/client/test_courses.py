from chisubmit.tests.common import ChisubmitMultiTestCase
from chisubmit.tests.fixtures import complete_course
        
        
class CompleteCourse(ChisubmitMultiTestCase):
    
    FIXTURE = complete_course
        
    def test_get_course(self):
        c = self.get_api_client("admin")
        
        course = c.get_course("cmsc40100")
        self.assertEquals(course.name, "Introduction to Software Testing")
        
        #students = course.students
        
        #self.assertEquals(len(students), 4)

            
        
                
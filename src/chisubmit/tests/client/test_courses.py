from chisubmit.tests.common import ChisubmitMultiTestCase
from chisubmit.client.course import Course
from chisubmit.tests.fixtures import complete_course
import unittest
        
        
class CompleteCourse(ChisubmitMultiTestCase):
    
    FIXTURE = complete_course
        
    def test_get_course(self):
        
        self.get_test_client({"id":"admin", "api_key":"admin"})
        
        course = Course.from_id("cmsc40100")
        self.assertEquals(course.name, "Introduction to Software Testing")
        
        students = course.students
        
        self.assertEquals(len(students), 4)

            
        
                
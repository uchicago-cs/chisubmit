from chisubmit.tests.common import ChisubmitMultiTestCase
from chisubmit.client.course import Course
from chisubmit.tests.fixtures import users_and_courses
import unittest
        
        
class CompleteCourse(ChisubmitMultiTestCase, unittest.TestCase):
    
    FIXTURE = users_and_courses
        
    def test_get_course(self):
        
        self.get_test_client({"id":"admin", "api_key":"admin"})
        
        course = Course.from_course_id("cmsc40100")
        self.assertEquals(course.name, "Introduction to Software Testing")
        
                
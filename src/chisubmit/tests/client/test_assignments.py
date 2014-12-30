from chisubmit.tests.common import ChisubmitMultiTestCase
from chisubmit.client.course import Course
from chisubmit.tests.fixtures import users_and_courses
import unittest
from chisubmit.client.assignment import Assignment
        
        
class CompleteCourse(ChisubmitMultiTestCase, unittest.TestCase):
    
    FIXTURE = users_and_courses
        
    def test_create_assignment(self):
        
        self.get_test_client({"id":"admin", "api_key":"admin"})
        
        assignment = Assignment(id = "pa1",
                                name = "Programming Assignment 1",
                                deadline = "2042-01-21T20:00",
                                course_id = "cmsc40100")        
        
        
                
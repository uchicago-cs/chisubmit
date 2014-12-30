from chisubmit.tests.common import ChisubmitMultiTestCase
from chisubmit.client.course import Course
from chisubmit.tests.fixtures import users_and_courses, complete_course
import unittest
from chisubmit.client.assignment import Assignment
        
        
class EmptyCourse(ChisubmitMultiTestCase, unittest.TestCase):
    
    FIXTURE = users_and_courses
        
    def test_create_assignment(self):
        
        self.get_test_client({"id":"admin", "api_key":"admin"})
        
        assignment = Assignment(id = "pa1",
                                name = "Programming Assignment 1",
                                deadline = "2042-01-21T20:00",
                                course_id = "cmsc40100")        
        
        
class CompleteCourse(ChisubmitMultiTestCase, unittest.TestCase):
    
    FIXTURE = complete_course
        
    def test_get_assignments(self):
        
        self.get_test_client({"id":"student1", "api_key":"student1"})
        
        assignments = Assignment.all_in_course("cmsc40100")
        
        print assignments        
        
    def test_get_assignment(self):
        
        self.get_test_client({"id":"student1", "api_key":"student1"})
        
        assignment = Assignment.from_course_and_id("cmsc40100", "pa1")
        

        
                              
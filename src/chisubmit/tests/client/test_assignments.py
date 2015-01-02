from chisubmit.tests.common import ChisubmitMultiTestCase, ChisubmitTestCase
from chisubmit.client.course import Course
from chisubmit.tests.fixtures import users_and_courses, complete_course
from chisubmit.client.assignment import Assignment

import unittest
from chisubmit.client.session import BadRequestError
        
        
class EmptyCourse(ChisubmitMultiTestCase):
    
    FIXTURE = users_and_courses
        
    def test_create_assignment(self):
        
        self.get_test_client({"id":"admin", "api_key":"admin"})
        
        assignment = Assignment(id = "pa1",
                                name = "Programming Assignment 1",
                                deadline = "2042-01-21T20:00",
                                course_id = "cmsc40100")        
        
        
class CompleteCourse(ChisubmitMultiTestCase):
    
    FIXTURE = complete_course
        
    def test_get_assignments(self):
        
        self.get_test_client({"id":"student1", "api_key":"student1"})
        
        assignments = Assignment.all("cmsc40100")
                
    def test_get_assignment(self):
        
        self.get_test_client({"id":"student1", "api_key":"student1"})
        
        assignment = Assignment.from_id("cmsc40100", "pa1")
        
        
class Registration(ChisubmitTestCase):
    
    FIXTURE = complete_course
        
    def test_single_registration1(self):
        
        self.get_test_client({"id":"student1", "api_key":"student1"})
        
        course = self.FIXTURE["courses"]["cmsc40100"]
        assignment = course["assignments"]["pa1"] 
        
        a = Assignment.from_id(course["id"], assignment["id"])
        self.assertEquals(a.name, assignment["name"])
                
        r = a.register(partners=["student2", "student3"]) 
        
    def test_single_registration2(self):
        
        self.get_test_client({"id":"student1", "api_key":"student1"})
        
        course = self.FIXTURE["courses"]["cmsc40100"]
        assignment = course["assignments"]["pa1"] 
        
        a = Assignment.from_id(course["id"], assignment["id"])
        self.assertEquals(a.name, assignment["name"])
                
        r = a.register(partners=["student2", "student3"])         
            
        self.get_test_client({"id":"student2", "api_key":"student2"})
        r = a.register(partners=["student1", "student3"])         

        self.get_test_client({"id":"student3", "api_key":"student3"})
        r = a.register(partners=["student1", "student2"])         

            
    def test_team_multiple_registration1(self):
        
        self.get_test_client({"id":"student1", "api_key":"student1"})
        
        course = self.FIXTURE["courses"]["cmsc40100"]
        assignment1 = course["assignments"]["pa1"] 
        assignment2 = course["assignments"]["pa2"] 
        
        a1 = Assignment.from_id(course["id"], assignment1["id"])
        self.assertEquals(a1.name, assignment1["name"])

        a2 = Assignment.from_id(course["id"], assignment2["id"])
        self.assertEquals(a2.name, assignment2["name"])
                
        r1 = a1.register(partners=["student2"]) 
        r2 = a2.register(partners=["student2"]) 
     

        
                              
from chisubmit.tests.integration.clientlibs import ChisubmitClientLibsTestCase
from chisubmit.tests.common import COURSE1_ASSIGNMENTS, COURSE2_ASSIGNMENTS
from chisubmit.client.exceptions import BadRequestException
from chisubmit.backend.api.models import Course, Assignment

class AssignmentTests(ChisubmitClientLibsTestCase):
    
    fixtures = ['users', 'course1', 'course1_pa1', 'course1_pa2']
    
    def test_get_assignments(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        assignments = course.get_assignments()
        
        self.assertEquals(len(assignments), len(COURSE1_ASSIGNMENTS))
        self.assertItemsEqual([a.assignment_id for a in assignments], COURSE1_ASSIGNMENTS)
        
    def test_get_assignment(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        for assignment_id in COURSE1_ASSIGNMENTS:
            assignment = course.get_assignment(assignment_id)
            
            self.assertEquals(assignment.assignment_id, assignment_id)
            
    def test_create_assignment(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        assignment = course.create_assignment(assignment_id = "pa3",
                                              name = "Programming Assignment 3",
                                              deadline = "2042-02-04 20:00:00+00:00",
                                              min_students = 2,
                                              max_students = 2)
        self.assertEquals(assignment.assignment_id, "pa3")
        self.assertEquals(assignment.name, "Programming Assignment 3")
        
        course_obj = Course.get_by_course_id("cmsc40100")
        self.assertIsNotNone(course_obj)
        
        assignment_obj = course_obj.get_assignment("pa3")
        self.assertIsNotNone(assignment_obj, "Assignment was not added to database")
            
        self.assertEquals(assignment_obj.assignment_id, "pa3")                  
        self.assertEquals(assignment_obj.name, "Programming Assignment 3")                  
        self.assertEquals(assignment_obj.min_students, 2)                  
        self.assertEquals(assignment_obj.max_students, 2)                  
                    
            
            
class AssignmentValidationTests(ChisubmitClientLibsTestCase):
    
    fixtures = ['users', 'course1', 'course1_pa1', 'course1_pa2',
                         'course2', 'course2_hw1', 'course2_hw2']
    
    def test_create_assignment_invalid_id(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        with self.assertRaises(BadRequestException) as cm:
            assignment = course.create_assignment(assignment_id = "pa 3",
                                                  name = "Programming Assignment 3",
                                                  deadline = "2042-02-04 20:00:00+00:00",
                                                  min_students = 2,
                                                  max_students = 2)
        
        bre = cm.exception
        self.assertItemsEqual(bre.errors.keys(), ["assignment_id"])
        self.assertEqual(len(bre.errors["assignment_id"]), 1)
        
    def test_create_assignment_multiple_errors(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        with self.assertRaises(BadRequestException) as cm:
            assignment = course.create_assignment(assignment_id = "pa 3",
                                                  name = None,
                                                  deadline = "2042-02-04 20:00:00+00:00",
                                                  min_students = 2,
                                                  max_students = 2)
        
        bre = cm.exception
        self.assertItemsEqual(bre.errors.keys(), ["assignment_id", "name"])
        self.assertEqual(len(bre.errors["assignment_id"]), 1)        
        self.assertEqual(len(bre.errors["name"]), 1)        
          
    def test_create_assignment_existing_assignment(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        with self.assertRaises(BadRequestException) as cm:
            assignment = course.create_assignment(assignment_id = "pa1",
                                                  name = "Programming Assignment 1",
                                                  deadline = "2042-02-04 20:00:00+00:00",
                                                  min_students = 2,
                                                  max_students = 2)
        
        bre = cm.exception
        self.assertItemsEqual(bre.errors.keys(), ["assignment_id"])
        self.assertEqual(len(bre.errors["assignment_id"]), 1)      
        
    def test_create_assignment_unique_within_course(self):
        c = self.get_api_client("admintoken")
        
        course1 = c.get_course("cmsc40100")
        course2 = c.get_course("cmsc40110")
        
        with self.assertRaises(BadRequestException):
            assignment1 = course1.create_assignment(assignment_id = "pa1",
                                                    name = "Programming Assignment 1",
                                                    deadline = "2042-02-04 20:00:00+00:00",
                                                    min_students = 2,
                                                    max_students = 2)        
        
        with self.assertRaises(BadRequestException):
            assignment2 = course2.create_assignment(assignment_id = "hw1",
                                                    name = "Homework 1",
                                                    deadline = "2042-02-04 20:00:00+00:00",
                                                    min_students = 2,
                                                    max_students = 2)                
        
        # Should not raise exceptions because course1 has pa1, pa2
        # and course2 has hw1, hw2
        assignment1 = course1.create_assignment(assignment_id = "hw1",
                                                name = "Homework 1",
                                                deadline = "2042-02-04 20:00:00+00:00",
                                                min_students = 2,
                                                max_students = 2)

        assignment2 = course2.create_assignment(assignment_id = "pa1",
                                                name = "Programming Assignment 1",
                                                deadline = "2042-02-04 20:00:00+00:00",
                                                min_students = 2,
                                                max_students = 2)
        
        assignments1 = course1.get_assignments()
        
        self.assertEquals(len(assignments1), len(COURSE1_ASSIGNMENTS) + 1)
        self.assertItemsEqual([a.assignment_id for a in assignments1], COURSE1_ASSIGNMENTS + ["hw1"])        
        
        assignments2 = course2.get_assignments()        
        
        self.assertEquals(len(assignments2), len(COURSE2_ASSIGNMENTS) + 1)
        self.assertItemsEqual([a.assignment_id for a in assignments2], COURSE2_ASSIGNMENTS + ["pa1"])        
                  
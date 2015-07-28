from chisubmit.tests.integration.clientlibs import ChisubmitClientLibsTestCase
from chisubmit.tests.common import COURSE1_ASSIGNMENTS, COURSE2_ASSIGNMENTS,\
    COURSE1_RUBRICS
from chisubmit.client.exceptions import BadRequestException
from chisubmit.backend.api.models import Course, Assignment

class RubricComponentTests(ChisubmitClientLibsTestCase):
    
    fixtures = ['users', 'course1', 'course1_pa1', 'course1_pa2']
    
    def test_get_rubric_components(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        for assignment_id in COURSE1_ASSIGNMENTS:
            assignment = course.get_assignment(assignment_id)
            rcs = assignment.get_rubric_components()
            
            self.assertEquals(len(rcs), len(COURSE1_RUBRICS[assignment_id]))
            self.assertItemsEqual([rc.description for rc in rcs], COURSE1_RUBRICS[assignment_id])
            
    def test_create_rubric_component(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        assignment = course.get_assignment("pa1")
        rc = assignment.create_rubric_component(description = "Third Task",
                                                points = 50,
                                                order = 3)
        
        course_obj = Course.get_by_course_id("cmsc40100")
        self.assertIsNotNone(course_obj)
        
        assignment_obj = course_obj.get_assignment("pa1")
        self.assertIsNotNone(assignment_obj)
        
        rc_obj = assignment_obj.get_rubric_component_by_description("Third Task")
        self.assertIsNotNone(rc_obj, "Rubric Component was not added to database")
            
        self.assertEquals(rc_obj.description, "Third Task")                  
        self.assertEquals(rc_obj.points, 50)                  
        self.assertEquals(rc_obj.order, 3)                  
        
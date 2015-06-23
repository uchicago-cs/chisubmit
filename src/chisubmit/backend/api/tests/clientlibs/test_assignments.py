from chisubmit.backend.api.models import Course
from chisubmit.backend.api.tests.clientlibs import ChisubmitClientLibsTests,\
    COURSE1_USERS, COURSE2_USERS, COURSE1_GRADERS, COURSE1_STUDENTS,\
    COURSE1_INSTRUCTORS, COURSE1_ASSIGNMENTS
from chisubmit.client.exceptions import UnknownObjectException

class AssignmentTests(ChisubmitClientLibsTests):
    
    fixtures = ['users', 'complete_course1']
    
    def test_get_assignments(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        assignments = course.get_assignments()
        
        self.assertEquals(len(assignments), len(COURSE1_ASSIGNMENTS))
        self.assertItemsEqual([a.shortname for a in assignments], COURSE1_ASSIGNMENTS)
        
    def test_get_assignment(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        for assignment_id in COURSE1_ASSIGNMENTS:
            assignment = course.get_assignment(assignment_id)
            
            self.assertEquals(assignment.shortname, assignment_id)
            
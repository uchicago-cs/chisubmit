from chisubmit.tests.integration.clientlibs import ChisubmitClientLibsTestCase
from chisubmit.tests.common import COURSE1_ASSIGNMENTS

class AssignmentTests(ChisubmitClientLibsTestCase):
    
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
            
from chisubmit.tests.common import ChisubmitMultiTestCase, example_fixture_1
from chisubmit.client.course import Course
        
        
class CompleteCourse(ChisubmitMultiTestCase):
    
    @classmethod
    def setUpClass(cls):
        super(CompleteCourse, cls).setUpClass()
        example_fixture_1(cls.server.db)
        
    def test_get_course(self):
        pass
        #c = Course.from_course_id("cmsc40100")
        #self.assertEquals(c.name, "Introduction to Software Testing")
        
                
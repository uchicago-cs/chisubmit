from chisubmit.tests.common import ChisubmitMultiTestCase, fixture1,\
    load_fixture
from chisubmit.client.course import Course
        
        
class CompleteCourse(ChisubmitMultiTestCase):
    
    @classmethod
    def setUpClass(cls):
        super(CompleteCourse, cls).setUpClass()
        load_fixture(cls.server.db, fixture1)
        
    def test_get_course(self):
        pass
        #c = Course.from_course_id("cmsc40100")
        #self.assertEquals(c.name, "Introduction to Software Testing")
        
                
from chisubmit.tests.common import ChisubmitTestCase, ChisubmitMultiTestCase,\
    example_fixture_1
import json

class Courses(ChisubmitTestCase):
    
    def test_get_courses(self):
        response = self.get("courses")
        self.assert_http_code(response, 200)
        
        data = json.loads(response.get_data())        
        self.assertIn("courses", data)
        self.assertEquals(len(data["courses"]), 0)
        
        
class CompleteCourse(ChisubmitMultiTestCase):
    
    @classmethod
    def setUpClass(cls):
        super(CompleteCourse, cls).setUpClass()
        example_fixture_1(cls.server.db)
        
    def test_get_course(self):
        response = self.get("courses")
        self.assert_http_code(response, 200)
        
        data = json.loads(response.get_data())        
        self.assertIn("courses", data)
        self.assertEquals(len(data["courses"]), 1)
        
                
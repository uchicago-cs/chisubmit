from chisubmit.tests.common import ChisubmitTestCase, ChisubmitMultiTestCase,\
    example_fixture_1
import json

class Courses(ChisubmitTestCase):
    
    def test_get_courses(self):
        c = self.get_admin_test_client()
        
        response = c.get("courses")
        self.assert_http_code(response, 200)
        
        data = json.loads(response.get_data())        
        self.assertIn("courses", data)
        self.assertEquals(len(data["courses"]), 0)
        
        
class CompleteCourse(ChisubmitMultiTestCase):
    
    @classmethod
    def setUpClass(cls):
        super(CompleteCourse, cls).setUpClass()
        instructors, courses = example_fixture_1(cls.server.db)
        
        cls.instructors = instructors
        cls.courses = courses
        
    def test_get_courses(self):
        ci1 = self.get_test_client(self.instructors[0])
        response = ci1.get("courses")
        self.assert_http_code(response, 200)
        
        data = json.loads(response.get_data())        
        self.assertIn("courses", data)
        self.assertEquals(len(data["courses"]), 2)
                
    def test_get_course(self):
        ci1 = self.get_test_client(self.instructors[0])
        response = ci1.get("courses/" + self.courses[0].id)
        self.assert_http_code(response, 200)
        
        data = json.loads(response.get_data())        
        self.assertIn("course", data)
        self.assertEquals(data["course"]["name"], self.courses[0].name)
    
                
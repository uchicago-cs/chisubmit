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
        
    def test_get_courses2(self):
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
        courses = example_fixture_1(cls.server.db)
         
        cls.courses = courses
         
    def test_get_courses(self):
        for course in self.courses:
            for instructor in course.instructors:
                c = self.get_test_client(instructor)
                response = c.get("courses")
                self.assert_http_code(response, 200)
         
                data = json.loads(response.get_data())        
                self.assertIn("courses", data)
                self.assertEquals(len(data["courses"]), 2)
                 
    def test_get_course(self):
        for course in self.courses:
            for instructor in course.instructors:
                c = self.get_test_client(instructor)
                response = c.get("courses/" + course.id)
                self.assert_http_code(response, 200)
                data = json.loads(response.get_data())        
                self.assertIn("course", data)
                self.assertEquals(data["course"]["name"], course.name)
                 
        for course1 in self.courses:
            for course2 in self.courses:
                if course1 != course2:
                    for instructor in course1.instructors:       
                        c = self.get_test_client(instructor)
                        response = c.get("courses/" + course2.id)
                        self.assert_http_code(response, 404)
        
                
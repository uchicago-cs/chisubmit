from chisubmit.tests.common import ChisubmitTestCase, ChisubmitMultiTestCase,\
    fixture1, load_fixture
import json
from chisubmit.backend.webapp.api.courses.models import Course
from sqlalchemy.orm import eagerload_all, eagerload

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
        load_fixture(cls.server.db, fixture1)
         
    def test_get_courses(self):        
        for course in fixture1["courses"].values():
            for instructor in course["instructors"]:
                c = self.get_test_client(fixture1["users"][instructor])
                response = c.get("courses")
                self.assert_http_code(response, 200)
         
                expected_ncourses = len([c for c in fixture1["courses"].values()
                                         if instructor in c["instructors"]])
         
                data = json.loads(response.get_data())        
                self.assertIn("courses", data)
                self.assertEquals(len(data["courses"]), expected_ncourses)
                 
    def test_get_course(self):
        for course in fixture1["courses"].values():
            for instructor in course["instructors"]:
                c = self.get_test_client(fixture1["users"][instructor])
                response = c.get("courses/" + course["id"])
                self.assert_http_code(response, 200)
                data = json.loads(response.get_data())        
                self.assertIn("course", data)
                self.assertEquals(data["course"]["name"], course["name"])
                 
        for course1 in fixture1["courses"].values():
            for course2 in fixture1["courses"].values():
                if course1 != course2:
                    for instructor in course1["instructors"]:    
                        c = self.get_test_client(fixture1["users"][instructor])
                        response = c.get("courses/" + course2["id"])
                        self.assert_http_code(response, 404)
        
                
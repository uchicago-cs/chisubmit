from chisubmit.tests.common import ChisubmitTestCase, ChisubmitMultiTestCase
from chisubmit.tests.fixtures import complete_course, users_and_courses
import json

class Empty(ChisubmitTestCase):
    
    def test_get_courses(self):
        c = self.get_admin_test_client()
        
        response = c.get("courses")
        self.assert_http_code(response, 200)
        
        data = json.loads(response.get_data())        
        self.assertIn("courses", data)
        self.assertEquals(len(data["courses"]), 0)
        
    def test_create_course(self):
        c = self.get_admin_test_client()
        
        data = {"id": "cmsc12300", "name": "Foobarmentals of Foobar"}        
        response = c.post("courses", data)
        self.assert_http_code(response, 201)
           

class CoursesAndUsers(ChisubmitMultiTestCase):
    
    FIXTURE = users_and_courses
    
    def __get_courses(self, client, expected):
        response = client.get("courses")
        self.assert_http_code(response, 200)
        
        data = json.loads(response.get_data())        
        self.assertIn("courses", data)
        self.assertEquals(len(data["courses"]), expected)
        
        return data

    def __get_course(self, client, course):
        response = client.get("courses/%s" % course["id"])
        self.assert_http_code(response, 200)
        
        data = json.loads(response.get_data())        
        self.assertIn("course", data)
        self.assertEquals(len(data), 1)
        self.assertEquals(data["course"]["name"], course["name"])
        
        return data

    
    def test_get_courses_admin(self):
        c = self.get_admin_test_client()
        data = self.__get_courses(c, len(self.FIXTURE["courses"]))
        
    def test_get_courses(self):
        c = self.get_test_client(self.FIXTURE["users"]["instructor1"])
        data = self.__get_courses(c, 1)
           
        c = self.get_test_client(self.FIXTURE["users"]["grader1"])        
        data = self.__get_courses(c, 1)

        c = self.get_test_client(self.FIXTURE["users"]["student1"])        
        data = self.__get_courses(c, 1)


    def test_get_course_admin(self):
        c = self.get_admin_test_client()
        data = self.__get_course(c, self.FIXTURE["courses"]["cmsc40100"])
        
    def test_get_course(self):
        c = self.get_test_client(self.FIXTURE["users"]["instructor1"])
        data = self.__get_course(c, self.FIXTURE["courses"]["cmsc40100"])

        c = self.get_test_client(self.FIXTURE["users"]["grader1"])        
        data = self.__get_course(c, self.FIXTURE["courses"]["cmsc40100"])

        c = self.get_test_client(self.FIXTURE["users"]["student1"])        
        data = self.__get_course(c, self.FIXTURE["courses"]["cmsc40100"])
         
class CompleteCourse(ChisubmitTestCase):
    
    FIXTURE = complete_course
        
    def test_update_student1(self):
        from chisubmit.backend.webapp.api.courses.models import CoursesStudents

        c = self.get_admin_test_client()
        
        attrs = {'name': 'git_username', 'value': 'foobar'}
        
        data = {"students": 
                {
                 "update": [
                            {"student_id": "student1",
                             "repo_info": [attrs]}
                           ]
                }
               }
                                     
        response = c.put("courses/cmsc40100", data)
        
        course_student = CoursesStudents.query.filter_by(
                        course_id="cmsc40100").filter_by(
                        student_id="student1").first()
                        

    def test_update_student2(self):
        from chisubmit.backend.webapp.api.courses.models import CoursesStudents

        c = self.get_admin_test_client()
        
        
        data = {"students": 
                {
                 "update": [
                            {"student_id": "student1",
                             "dropped": True}
                           ]
                }
               }
                                     
        response = c.put("courses/cmsc40100", data)
        
        course_student = CoursesStudents.query.filter_by(
                        course_id="cmsc40100").filter_by(
                        student_id="student1").first()
                        
                
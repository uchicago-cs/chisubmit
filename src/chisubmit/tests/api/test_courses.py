from chisubmit.tests.common import ChisubmitTestCase, ChisubmitMultiTestCase
import json
import unittest
from chisubmit.tests.fixtures import complete_course
from chisubmit.backend.webapp.api.courses.models import CoursesStudents

class Courses(ChisubmitTestCase):
    
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
           
         
class CompleteCourse(ChisubmitTestCase):
    
    FIXTURE = complete_course
        
    def test_update_student1(self):
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
                        
        print course_student.student_id
        print course_student.repo_info
        print course_student.dropped       


    def test_update_student2(self):
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
                        
        print course_student.student_id
        print course_student.repo_info 
        print course_student.dropped       
                
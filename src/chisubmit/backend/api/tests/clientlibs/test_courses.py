from chisubmit import client
from rest_framework.test import APILiveServerTestCase
from chisubmit.backend.api.models import Course

class CourseTests(APILiveServerTestCase):
    
    fixtures = ['users', 'complete_course1']
    
    def get_api_client(self, api_token):
        base_url = self.live_server_url + "/api/v1"
        
        return client.Chisubmit(api_token=api_token, base_url=base_url)    
    
    def test_get_courses(self):
        c = self.get_api_client("admintoken")
        
        courses = c.get_courses()
        self.assertEquals(len(courses), 1)
    
    def test_get_course(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        self.assertEquals(course.name, "Introduction to Software Testing")
        

    def test_create_course(self):
        c = self.get_api_client("admintoken")
        
        course = c.create_course(course_id = "cmsc40110",
                                 name = "Advanced Software Testing")
        self.assertEquals(course.name, "Advanced Software Testing")        
        
        try:
            course_obj = Course.objects.get(shortname="cmsc40110")
        except Course.DoesNotExist:
            self.fail("Course was not added to database")  
            
        self.assertEquals(course_obj.shortname, "cmsc40110")                  
        self.assertEquals(course_obj.name, "Advanced Software Testing")                  
        
        
    def test_edit_course(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        
        course.edit(name="Intro to Software Testing",
                    default_extensions = 10)

        self.assertEquals(course.name, "Intro to Software Testing")                    
        self.assertEquals(course.default_extensions, 10)
                 
        try:
            course_obj = Course.objects.get(shortname="cmsc40100")
        except Course.DoesNotExist:
            self.fail("Course not found in database")  
            
        self.assertEquals(course_obj.name, "Intro to Software Testing")                    
        self.assertEquals(course_obj.default_extensions, 10)                  
                 
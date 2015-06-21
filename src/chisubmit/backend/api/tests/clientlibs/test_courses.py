from chisubmit import client
from rest_framework.test import APILiveServerTestCase

class CourseTests(APILiveServerTestCase):
    
    fixtures = ['users', 'complete_course']
    
    def get_api_client(self, api_token):
        base_url = self.live_server_url + "/api/v1"
        
        return client.Chisubmit(api_token=api_token, base_url=base_url)    
    
    def test_get_course(self):
        c = self.get_api_client("admintoken")
        
        course = c.get_course("cmsc40100")
        self.assertEquals(course.name, "Introduction to Software Testing")
        

        
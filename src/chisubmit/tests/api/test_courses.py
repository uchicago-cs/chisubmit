from chisubmit.tests.common import ChisubmitTestCase
import json
import unittest

class Courses(ChisubmitTestCase, unittest.TestCase):
    
    def test_get_courses(self):
        c = self.get_admin_test_client()
        
        response = c.get("courses")
        self.assert_http_code(response, 200)
        
        data = json.loads(response.get_data())        
        self.assertIn("courses", data)
        self.assertEquals(len(data["courses"]), 0)
        
    
         

        
                
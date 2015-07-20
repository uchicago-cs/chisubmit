from chisubmit.tests.integration.clientlibs import ChisubmitClientLibsTestCase
from chisubmit.tests.common import ALL_USERS
from django.contrib.auth.models import User

class UserTests(ChisubmitClientLibsTestCase):
    
    fixtures = ['users', 'complete_course1']
    
    def test_get_users(self):
        c = self.get_api_client("admintoken")
        
        users = c.get_users()
        self.assertItemsEqual([u.username for u in users], ALL_USERS)

    
    def test_get_user(self):
        c = self.get_api_client("admintoken")
        
        user = c.get_user("instructor1")
        self.assertEquals(user.username, "instructor1")
        self.assertEquals(user.first_name, "F_instructor1")
        self.assertEquals(user.last_name, "L_instructor1")

    def test_create_user(self):
        c = self.get_api_client("admintoken")
        
        user = c.create_user(username = "student100",
                             first_name = "F_student100",
                             last_name = "L_student100",
                             email = "student100@example.org")
        self.assertEquals(user.username, "student100")
        self.assertEquals(user.first_name, "F_student100")
        self.assertEquals(user.last_name, "L_student100")
        self.assertEquals(user.email, "student100@example.org")
        
        try:
            user_obj = User.objects.get(username="student100")
        except User.DoesNotExist:
            self.fail("User was not added to database")  
            
        self.assertEquals(user_obj.username, "student100")
        self.assertEquals(user_obj.first_name, "F_student100")
        self.assertEquals(user_obj.last_name, "L_student100")
        self.assertEquals(user_obj.email, "student100@example.org")

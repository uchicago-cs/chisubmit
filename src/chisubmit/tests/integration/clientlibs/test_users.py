from chisubmit.tests.integration.clientlibs import ChisubmitClientLibsTestCase
from chisubmit.tests.common import ALL_USERS
from django.contrib.auth.models import User
from chisubmit.client.exceptions import UnknownObjectException,\
    UnauthorizedException
from rest_framework.authtoken.models import Token

class UserTests(ChisubmitClientLibsTestCase):
    
    fixtures = ['users']
    
    def test_get_users(self):
        c = self.get_api_client("admintoken")
        
        users = c.get_users()
        self.assertCountEqual([u.username for u in users], ALL_USERS)

    
    def test_get_user(self):
        c = self.get_api_client("admintoken")
        
        user = c.get_user("instructor1")
        self.assertEqual(user.username, "instructor1")
        self.assertEqual(user.first_name, "F_instructor1")
        self.assertEqual(user.last_name, "L_instructor1")

    def test_create_user(self):
        c = self.get_api_client("admintoken")
        
        user = c.create_user(username = "student100",
                             first_name = "F_student100",
                             last_name = "L_student100",
                             email = "student100@example.org")
        self.assertEqual(user.username, "student100")
        self.assertEqual(user.first_name, "F_student100")
        self.assertEqual(user.last_name, "L_student100")
        self.assertEqual(user.email, "student100@example.org")
        
        try:
            user_obj = User.objects.get(username="student100")
        except User.DoesNotExist:
            self.fail("User was not added to database")  
            
        self.assertEqual(user_obj.username, "student100")
        self.assertEqual(user_obj.first_name, "F_student100")
        self.assertEqual(user_obj.last_name, "L_student100")
        self.assertEqual(user_obj.email, "student100@example.org")
        
class UserTokenTests(ChisubmitClientLibsTestCase):
    
    fixtures = ['users']
    
    def test_get_own_token_as_admin(self):
        c = self.get_api_client("admintoken")
        
        token, created = c.get_user_token()
        self.assertEqual(token, "admintoken")    
        self.assertEqual(created, False)
        
    def test_get_other_token_as_admin(self):
        c = self.get_api_client("admintoken")
        
        token, created = c.get_user_token(username = "instructor1")
        self.assertEqual(token, "instructor1token")    
        self.assertEqual(created, False)        
        
    def test_get_own_token(self):
        c = self.get_api_client("instructor1", password="instructor1")
        
        token, created = c.get_user_token()
        self.assertEqual(token, "instructor1token")    
        self.assertEqual(created, False)         

    def test_create_own_token(self):
        c = self.get_api_client("instructor1", password="instructor1")
        
        token = Token.objects.get(user__username="instructor1")
        self.assertEqual(token.key, "instructor1token")    
        token.delete()
        
        token, created = c.get_user_token()
        self.assertNotEqual(token, "instructor1token")    
        self.assertEqual(created, True)         
        
    def test_reset_own_token(self):
        c = self.get_api_client("instructor1", password="instructor1")
        
        token, created = c.get_user_token(reset=True)
        self.assertNotEqual(token, "instructor1token")    
        self.assertEqual(created, True)                
            
    def test_get_other_token(self):
        c = self.get_api_client("instructor1", password="instructor1")
        
        with self.assertRaises(UnknownObjectException) as cm:
            token, created = c.get_user_token(username="instructor2")   
            
    def test_basic_auth_fail(self):
        c = self.get_api_client("instructor1", password="foobar")
        
        with self.assertRaises(UnauthorizedException) as cm:
            token, created = c.get_user_token(username="instructor1")                         

from chisubmit.backend.api.tests.clientlibs import ChisubmitClientLibsTests,\
    ALL_USERS

class UserTests(ChisubmitClientLibsTests):
    
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

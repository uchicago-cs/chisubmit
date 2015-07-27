from chisubmit.tests.common import ChisubmitCLITestClient,\
    cli_test, ChisubmitCLITestCase
from chisubmit.cli import chisubmit_get_credentials_cmd
from rest_framework.authtoken.models import Token
    
class CLIGetChisubmitCredentials(ChisubmitCLITestCase):
                    
    fixtures = ['users']
                
    @cli_test
    def test_auth1(self, runner):
        admin, instructors, _, _ = self.create_clients(runner, "admin", instructor_ids=["instructor1"])
        
        instructor = instructors[0]
        
        token = Token.objects.get(user__username="instructor1")
        self.assertEqual(token.key, "instructor1token")    
        token.delete()
        
        result = instructor.run(None, 
                                cmd = chisubmit_get_credentials_cmd,
                                cmd_input = "instructor1\ninstructor1\n")
        self.assertEquals(result.exit_code, 0)
        
        token = Token.objects.get(user__username="instructor1")
        self.assertNotEqual(token.key, "instructor1token")    

    @cli_test
    def test_auth2(self, runner):
        admin, instructors, _, _ = self.create_clients(runner, "admin", instructor_ids=["instructor1"])
        
        instructor = instructors[0]
                
        result = instructor.run(None, 
                                cmd = chisubmit_get_credentials_cmd,
                                cmd_input = "instructor1\ninstructor1\n")
        self.assertEquals(result.exit_code, 0)
        
        token = Token.objects.get(user__username="instructor1")
        self.assertEqual(token.key, "instructor1token")

    @cli_test
    def test_auth3(self, runner):
        admin, instructors, _, _ = self.create_clients(runner, "admin", instructor_ids=["instructor1"])
        
        instructor = instructors[0]
                
        result = instructor.run(None, 
                                ["--reset"],
                                cmd = chisubmit_get_credentials_cmd,
                                cmd_input = "instructor1\ninstructor1\n")
        self.assertEquals(result.exit_code, 0)
        
        token = Token.objects.get(user__username="instructor1")
        self.assertNotEqual(token.key, "instructor1token")

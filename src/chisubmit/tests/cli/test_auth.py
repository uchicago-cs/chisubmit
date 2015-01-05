from chisubmit.tests.common import ChisubmitTestCase, ChisubmitCLITestClient,\
    cli_test
from chisubmit.tests.fixtures import complete_course
from chisubmit.cli import chisubmit_get_credentials_cmd
from chisubmit.backend.webapp.api.users.models import User
    
class CLIGetChisubmitCredentials(ChisubmitTestCase):
            
    FIXTURE = complete_course
            
    @cli_test
    def test_auth1(self, runner):
        instructor = ChisubmitCLITestClient("instructor1", None, runner,
                                            verbose = True)
        
        user = User.from_id("instructor1")
        user.api_key = None
        self.server.db.session.add(user)
        self.server.db.session.commit()
        
        result = instructor.run(None, 
                                cmd = chisubmit_get_credentials_cmd,
                                cmd_input = "instructor1\n"+self.auth_password+'\n')
        self.assertEquals(result.exit_code, 0)
        
        user = User.from_id("instructor1")
        self.assertIsNotNone(user.api_key)
        self.assertNotEquals(user.api_key, "instructor1")

    @cli_test
    def test_auth2(self, runner):
        instructor = ChisubmitCLITestClient("instructor1", None, runner,
                                            verbose = True)
                
        result = instructor.run(None, 
                                cmd = chisubmit_get_credentials_cmd,
                                cmd_input = "instructor1\n"+self.auth_password+'\n')
        self.assertEquals(result.exit_code, 0)
        
        user = User.from_id("instructor1")
        self.assertIsNotNone(user.api_key)
        self.assertEquals(user.api_key, "instructor1")

    @cli_test
    def test_auth3(self, runner):
        instructor = ChisubmitCLITestClient("instructor1", None, runner,
                                            verbose = True)
                
        result = instructor.run(None, 
                                ["--reset"],
                                cmd = chisubmit_get_credentials_cmd,
                                cmd_input = "instructor1\n"+self.auth_password+'\n')
        self.assertEquals(result.exit_code, 0)
        
        user = User.from_id("instructor1")
        self.assertIsNotNone(user.api_key)
        self.assertNotEquals(user.api_key, "instructor1")

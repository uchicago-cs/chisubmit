from chisubmit.backend.webapp.auth import Auth


class TestingAuth(Auth):
    
    def __init__(self, server, password):
        super(TestingAuth, self).__init__(server)

        self.password = password
        
        
    def check_auth(self, username, password):
        print "CHECK", username, password
        if password == self.password:
            return True
        else:
            return False
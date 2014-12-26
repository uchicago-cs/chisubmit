import unittest
from chisubmit.backend.server import ChisubmitServer
import chisubmit.client.session as session
import tempfile
import os
from chisubmit.backend.webapp.api.people.models import Person
from chisubmit.backend.webapp.api.courses.models import Course

def setUp(obj):
    obj.server = ChisubmitServer()
    obj.db_fd, obj.db_filename = tempfile.mkstemp()
    obj.server.app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + obj.db_filename
    obj.server.app.config["TESTING"] = True
    obj.server.init_db()
    obj.test_client = session.connect_test(obj.server.app)        
    
def tearDown(obj):
    os.close(obj.db_fd)
    os.unlink(obj.db_filename)

class BaseChisubmitTestCase(unittest.TestCase):
    
    API_PREFIX = "/api/v0/"
        
    def assert_http_code(self, response, expected):
        self.assertEquals(response.status_code, expected, "Expected HTTP response code %i, got %i" % (expected, response.status_code))
        
    def get(self, resource):
        return self.test_client.get(self.API_PREFIX + resource)
    
class ChisubmitTestCase(BaseChisubmitTestCase):
        
    def setUp(self):
        setUp(self)
        
    def tearDown(self):
        tearDown(self)        
    

class ChisubmitMultiTestCase(BaseChisubmitTestCase):
        
    @classmethod
    def setUpClass(cls):
        setUp(cls)

    @classmethod
    def tearDownClass(cls):
        tearDown(cls)      
    
def example_fixture_1(db):
    admin = Person(first_name="Administrator", 
                   last_name="Administrator", 
                   id="admin",
                   api_key="admin", 
                   admin=1)    
    
    instructor = Person(first_name="Joe", 
                        last_name="Instructor", 
                        id="jinstr",
                        api_key="jinstr")
    
    course = Course(id = "cmsc40100",
                    name = "Introduction to Software Testing",
                    extensions = 0)
    
    db.session.add(admin)
    db.session.add(instructor)
    db.session.add(course)
    db.session.commit()
    
    
    
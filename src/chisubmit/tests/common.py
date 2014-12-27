import unittest
from chisubmit.backend.server import ChisubmitServer
import chisubmit.client.session as session
import tempfile
import os
from chisubmit.backend.webapp.api.people.models import Person
from chisubmit.backend.webapp.api.courses.models import Course,\
    CoursesInstructors

def setUp(obj):
    obj.server = ChisubmitServer()
    obj.db_fd, obj.db_filename = tempfile.mkstemp()
    obj.server.app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + obj.db_filename
    obj.server.app.config["TESTING"] = True
    obj.server.init_db()
    obj.server.create_admin(api_key="admin")
            
    
def tearDown(obj):
    os.close(obj.db_fd)
    os.unlink(obj.db_filename)

class ChisubmitTestClient(object):
    
    API_PREFIX = "/api/v0/"
    
    def __init__(self, app, user_id, api_key):
        self.user_id = user_id
        self.api_key = api_key
        
        if self.api_key is not None:
            self.headers = {"CHISUBMIT-API-KEY":self.api_key}
        else:
            self.headers = None
            
        self.test_client = session.connect_test(app)

    def get(self, resource):
        return self.test_client.get(self.API_PREFIX + resource, headers = self.headers)


class BaseChisubmitTestCase(unittest.TestCase):
    
    def get_admin_test_client(self):
        return ChisubmitTestClient(self.server.app, "admin", "admin")
    
    def get_test_client(self, person = None):
        if person is None:
            return ChisubmitTestClient(self.server.app, "anonymous", None)
        else:
            return ChisubmitTestClient(self.server.app, person.id, person.api_key)
        
    def assert_http_code(self, response, expected):
        self.assertEquals(response.status_code, expected, "Expected HTTP response code %i, got %i" % (expected, response.status_code))
        
    
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
    instructor1 = Person(first_name="Joe", 
                         last_name="Instructor", 
                         id="jinstr",
                         api_key="jinstr")

    instructor2 = Person(first_name="Sam", 
                         last_name="Instructor", 
                         id="sinstr",
                         api_key="sinstr")
    
    course1 = Course(id = "cmsc40100",
                     name = "Introduction to Software Testing",
                     extensions = 0)

    course2 = Course(id = "cmsc40110",
                     name = "Advanced Software Testing",
                     extensions = 0)

    
    db.session.add(instructor1)
    db.session.add(instructor2)
    db.session.add(course1)
    db.session.add(course2)
    
    db.session.add(CoursesInstructors(instructor_id = instructor1.id, course_id=course1.id))
    db.session.add(CoursesInstructors(instructor_id = instructor2.id, course_id=course2.id))
    
    db.session.commit()
    
    return [instructor1, instructor2], [course1, course2]
    
    
    
import unittest
from chisubmit.backend.server import ChisubmitServer
import chisubmit.client.session as session
import tempfile
import os
from chisubmit.backend.webapp.api.users.models import User
from chisubmit.backend.webapp.api.courses.models import Course,\
    CoursesInstructors
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import sessionmaker


class ChisubmitTestClient(object):
    
    API_PREFIX = "/api/v0/"
    
    def __init__(self, app, user_id, api_key):
        self.user_id = user_id
        self.api_key = api_key
        
        if self.api_key is not None:
            self.headers = {"CHISUBMIT-API-KEY":self.api_key}
        else:
            self.headers = None
            
        self.test_client = session.connect_test(app, api_key)

    def get(self, resource):
        return self.test_client.get(self.API_PREFIX + resource, headers = self.headers)


class BaseChisubmitTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.server = ChisubmitServer()
        cls.db_fd, cls.db_filename = tempfile.mkstemp()
        cls.server.app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + cls.db_filename
        cls.server.app.config["TESTING"] = True

    @classmethod
    def tearDownClass(cls):
        os.close(cls.db_fd)
        os.unlink(cls.db_filename)
    
    def get_admin_test_client(self):
        return ChisubmitTestClient(self.server.app, "admin", "admin")
    
    def get_test_client(self, user = None):
        if user is None:
            return ChisubmitTestClient(self.server.app, "anonymous", None)
        else:
            return ChisubmitTestClient(self.server.app, user["id"], user["api_key"])
        
    def assert_http_code(self, response, expected):
        self.assertEquals(response.status_code, expected, "Expected HTTP response code %i, got %i" % (expected, response.status_code))
        
    
class ChisubmitTestCase(BaseChisubmitTestCase):
        
    def setUp(self):
        self.server.init_db()
        self.server.create_admin(api_key="admin")
        
    def tearDown(self):
        self.server.db.session.remove()
        self.server.db.drop_all()
    

class ChisubmitMultiTestCase(BaseChisubmitTestCase):
        
    @classmethod
    def setUpClass(cls):
        super(ChisubmitMultiTestCase, cls).setUpClass()
        cls.server.init_db()
        cls.server.create_admin(api_key="admin")

    @classmethod
    def tearDownClass(cls):
        cls.server.db.session.remove()
        cls.server.db.drop_all()
        super(ChisubmitMultiTestCase, cls).tearDownClass()
    
fixture1 = { "users": { "jinstr": {"first_name": "Joe",
                                    "last_name": "Instructor",
                                    "id": "jinstr",
                                    "api_key": "jinstr"},
                         
                         "sinstr": {"first_name": "Sam",
                                    "last_name": "Instructor",
                                    "id": "sinstr",
                                    "api_key": "sinstr"},
                        },
             "courses": { "cmsc40100": {"id": "cmsc40100",
                                        "name": "Introduction to Software Testing",
                                        "extensions": 0,
                                        "instructors": ["jinstr"]},
                          "cmsc40110": {"id": "cmsc40110",
                                        "name": "Advanced Software Testing",
                                        "extensions": 0,
                                        "instructors": ["sinstr"]}
                        }
            }
 
    
def load_fixture(db, fixture):
    
    user_objs = {}
    
    for u_id, user in fixture["users"].items():
        u = User(first_name=user["first_name"], 
                   last_name=user["last_name"], 
                   id=user["id"],
                   api_key=user["api_key"])
        
        user_objs[u_id] = u
        db.session.add(u)

    for c_id, course in fixture["courses"].items():
        c = Course(id = course["id"],
                   name = course["name"],
                   extensions = course["extensions"])
        
        db.session.add(c)
        
        for instructor in course["instructors"]:
            o = user_objs[instructor]
            db.session.add(CoursesInstructors(instructor_id = o.id, 
                                              course_id     = c.id))
    
    db.session.commit()
        
    
    
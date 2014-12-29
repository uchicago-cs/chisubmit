import unittest
import chisubmit.client.session as session
import tempfile
import os
import json
from chisubmit.backend.webapp.api.users.models import User
from chisubmit.backend.webapp.api.courses.models import Course,\
    CoursesInstructors
from chisubmit.backend.webapp.api import ChisubmitAPIServer


class ChisubmitTestClient(object):
    
    API_PREFIX = "/api/v0/"
    
    def __init__(self, app, user_id, api_key):
        self.user_id = user_id
        self.api_key = api_key
        
        self.headers = {'content-type': 'application/json'}
        
        if self.api_key is not None:
            self.headers["CHISUBMIT-API-KEY"] = self.api_key
            
        self.test_client = session.connect_test(app, api_key)

    def get(self, resource):
        return self.test_client.get(self.API_PREFIX + resource, headers = self.headers)

    def post(self, resource, data):
        if isinstance(data, dict):
            datastr = json.dumps(data)
        elif isinstance(data, basestring):
            datastr = data
        return self.test_client.post(self.API_PREFIX + resource, data = datastr, headers = self.headers)

class BaseChisubmitTestCase(object):
    
    @classmethod
    def setUpClass(cls):
        cls.server = ChisubmitAPIServer(debug = True)
        cls.db_fd, cls.db_filename = tempfile.mkstemp()
        cls.server.connect_sqlite(cls.db_filename)
            
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
        
        if hasattr(self, "FIXTURE"):
            load_fixture(self.server.db, self.FIXTURE)
        
        
    def tearDown(self):
        self.server.db.session.remove()
        self.server.db.drop_all()
    

class ChisubmitMultiTestCase(BaseChisubmitTestCase):
        
    @classmethod
    def setUpClass(cls):
        super(ChisubmitMultiTestCase, cls).setUpClass()
        cls.server.init_db()
        cls.server.create_admin(api_key="admin")
        
        if hasattr(cls, "FIXTURE"):
            load_fixture(cls.server.db, cls.FIXTURE)
        

    @classmethod
    def tearDownClass(cls):
        cls.server.db.session.remove()
        cls.server.db.drop_all()
        super(ChisubmitMultiTestCase, cls).tearDownClass()
    
class ChisubmitFixtureTestCase(ChisubmitMultiTestCase):
    
    def test_get_courses(self):        
        for course in self.FIXTURE["courses"].values():
            for instructor in course["instructors"]:
                c = self.get_test_client(self.FIXTURE["users"][instructor])
                response = c.get("courses")
                self.assert_http_code(response, 200)
         
                expected_ncourses = len([c for c in self.FIXTURE["courses"].values()
                                         if instructor in c["instructors"]])
         
                data = json.loads(response.get_data())        
                self.assertIn("courses", data)
                self.assertEquals(len(data["courses"]), expected_ncourses)
                 
    def test_get_course(self):
        for course in self.FIXTURE["courses"].values():
            for instructor in course["instructors"]:
                c = self.get_test_client(self.FIXTURE["users"][instructor])
                response = c.get("courses/" + course["id"])
                self.assert_http_code(response, 200)
                data = json.loads(response.get_data())        
                self.assertIn("course", data)
                self.assertEquals(data["course"]["name"], course["name"])
                 
        for course1 in self.FIXTURE["courses"].values():
            for course2 in self.FIXTURE["courses"].values():
                if course1 != course2:
                    for instructor in course1["instructors"]:    
                        c = self.get_test_client(self.FIXTURE["users"][instructor])
                        response = c.get("courses/" + course2["id"])
                        self.assert_http_code(response, 404)
 
    
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
                   name = course["name"])
        
        db.session.add(c)
        
        for instructor in course["instructors"]:
            o = user_objs[instructor]
            db.session.add(CoursesInstructors(instructor_id = o.id, 
                                              course_id     = c.id))
    
    db.session.commit()
        
    
    
from chisubmit.tests.common import ChisubmitFixtureTestCase
from chisubmit.tests.fixtures import users_and_courses
import unittest

class UsersAndCoursesFixtureCheck(ChisubmitFixtureTestCase, unittest.TestCase):
        
    FIXTURE = users_and_courses 
    
from . import test_admin_courses
from unittest.suite import TestSuite
from chisubmit.tests.cli import test_auth

test_cases = [test_admin_courses, test_auth]

def load_tests(loader, tests, pattern):
    suite = TestSuite()
    for test_module in test_cases:
        tests = loader.loadTestsFromModule(test_module)
        suite.addTests(tests)
    return suite
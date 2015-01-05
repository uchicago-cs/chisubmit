from unittest.suite import TestSuite

from . import test_courses
from . import test_assignments

test_cases = [test_courses, test_assignments]

def load_tests(loader, tests, pattern):
    suite = TestSuite()
    for test_module in test_cases:
        tests = loader.loadTestsFromModule(test_module)
        suite.addTests(tests)
    return suite
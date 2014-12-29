import unittest
from . import api
from . import client
from . import cli
from long import test_complete_workflow

api_tests = unittest.TestLoader().loadTestsFromModule(api)
client_tests = unittest.TestLoader().loadTestsFromModule(client)
cli_tests = unittest.TestLoader().loadTestsFromModule(cli)

short_tests = unittest.TestSuite([api_tests, client_tests, cli_tests])

complete_workflow = unittest.TestLoader().loadTestsFromModule(test_complete_workflow) 


if __name__ == "__main__":
    unittest.main(defaultTest="short_tests")
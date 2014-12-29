import unittest
from . import api
from . import client
 

api_tests = unittest.TestLoader().loadTestsFromModule(api)
client_tests = unittest.TestLoader().loadTestsFromModule(client)

short_tests = unittest.TestSuite([api_tests, client_tests])#, cli_tests]


if __name__ == "__main__":
    unittest.main(defaultTest="short_tests")
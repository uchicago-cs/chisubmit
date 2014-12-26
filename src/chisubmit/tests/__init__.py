import unittest
from chisubmit.tests import test_api, test_client

alltests = unittest.TestSuite([
                               unittest.TestLoader().loadTestsFromModule(test_api),
                               unittest.TestLoader().loadTestsFromModule(test_client),
                               ])

if __name__ == "__main__":
    unittest.main(defaultTest="alltests")
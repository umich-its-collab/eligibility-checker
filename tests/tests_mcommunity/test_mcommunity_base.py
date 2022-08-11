import logging
import unittest

import ldap

from mcommunity.mcommunity_base import ldap_connect
from tests.tests_mcommunity import mcommunity_mocks as mocks


class MCommunityBaseTestCase(unittest.TestCase):

    def test_error_invalid_credentials(self):
        with self.assertRaises(ldap.INVALID_CREDENTIALS):
            ldap_connect(mocks.test_app, mocks.test_secret)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main(verbosity=3)

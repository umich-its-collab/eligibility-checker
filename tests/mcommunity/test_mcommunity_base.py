import logging
import unittest

import ldap

from mcommunity.mcommunity_base import ldap_connect

test_app = 'ITS-FakeTestApp-McDirApp001'
test_secret = 'test123'


class MCommunityBaseTestCase(unittest.TestCase):

    def test_error_invalid_credentials(self):
        with self.assertRaises(ldap.INVALID_CREDENTIALS):
            ldap_connect(test_app, test_secret)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main(verbosity=3)

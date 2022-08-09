import logging
import unittest
from unittest.mock import patch

from mcommunity.mcommunity_group import MCommunityGroup
from mcommunity.mcommunity_user import MCommunityUser
from tests.mcommunity import mcommunity_mocks
from tests.mcommunity.test_mcommunity_base import test_app, test_secret

test_group = 'test-group'


class MCommunityGroupTestCase(unittest.TestCase):
    group = None

    @classmethod
    @patch('mcommunity.mcommunity_group.MCommunityGroup._populate_group_data')
    def setUpClass(cls, magic_mock) -> None:
        magic_mock.side_effect = mcommunity_mocks.mcomm_group_side_effect
        cls.group = MCommunityGroup(test_group, test_app, test_secret)

    def test_init_sets_cn(self):
        self.assertEqual(test_group, self.group.cn)

    def test_init_sets_raw_group(self):
        self.assertEqual(mcommunity_mocks.group_mock, self.group.raw_group)
        self.assertEqual(list, type(self.group.raw_group))
        self.assertEqual(1, len(self.group.raw_group))  # LDAP should always return a 1-item list for a real group
        self.assertEqual(2, len(self.group.raw_group[0]))  # LDAP should always return a 2-item tuple for a real group

    def test_init_sets_members(self):
        self.assertEqual(['nemcardf', 'nemcardrs', 'nemcarda', 'nemcards'], self.group.members)

    @patch('mcommunity.mcommunity_user.MCommunityUser._populate_user_data')
    def test_populate_members_mcomm_users(self, magic_mock):
        print('mcomm users')
        magic_mock.side_effect = mcommunity_mocks.mcomm_user_side_effect
        self.assertEqual([], self.group.members_mcomm_users)  # Before populating, there should not be any
        self.group.populate_members_mcomm_users()
        members = [
            MCommunityUser(uniqname, self.group.mcommunity_app_cn, self.group.mcommunity_app_cn)
            for uniqname in self.group.members
        ]
        self.assertEqual(len(members), len(self.group.members_mcomm_users))  # Should be 4 members
        self.assertEqual(members[0].dn, self.group.members_mcomm_users[0].dn)  # Make sure first element is same

    def test_group_exists(self):
        self.assertEqual(True, self.group.exists)

    @patch('mcommunity.mcommunity_group.MCommunityGroup._populate_group_data')
    def test_group_not_exists(self, magic_mock):
        magic_mock.side_effect = mcommunity_mocks.mcomm_group_side_effect
        with self.assertRaises(NameError):
            self.assertEqual(False, MCommunityGroup('fake', test_app, test_secret).exists)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main(verbosity=3)

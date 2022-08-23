import logging
import unittest
from unittest.mock import patch

from collab_eligibility_checker.mcommunity.mcommunity_group import MCommunityGroup
from collab_eligibility_checker.mcommunity.mcommunity_user import MCommunityUser
from tests.tests_mcommunity import mcommunity_mocks as mocks

test_group = 'test-group'


class MCommunityGroupTestCase(unittest.TestCase):
    group = None

    @classmethod
    @patch('collab_eligibility_checker.mcommunity.mcommunity_base.MCommunityBase.search')
    def setUpClass(cls, magic_mock) -> None:
        magic_mock.side_effect = mocks.mcomm_side_effect
        cls.group = MCommunityGroup(test_group, mocks.test_app, mocks.test_secret)

    def test_init_sets_cn(self):
        self.assertEqual(test_group, self.group.name)

    def test_init_sets_raw_group(self):
        self.assertEqual(mocks.group_mock, self.group.raw_result)
        self.assertEqual(list, type(self.group.raw_result))
        self.assertEqual(1, len(self.group.raw_result))  # LDAP should always return a 1-item list for a real group
        self.assertEqual(2, len(self.group.raw_result[0]))  # LDAP should always return a 2-item tuple for a real group

    def test_init_sets_members(self):
        self.assertEqual(['nemcardf', 'nemcardrs', 'nemcarda'], self.group.members)

    @patch('collab_eligibility_checker.mcommunity.mcommunity_base.MCommunityBase.search')
    def test_populate_members_mcomm_users(self, magic_mock):
        magic_mock.side_effect = mocks.mcomm_side_effect
        self.assertEqual([], self.group.members_mcomm_users)  # Before populating, there should not be any
        self.group.populate_members_mcomm_users()
        members = [
            MCommunityUser(uniqname, self.group.mcommunity_app_cn, self.group.mcommunity_app_cn)
            for uniqname in self.group.members
        ]
        self.assertEqual(len(members), len(self.group.members_mcomm_users))  # Should be 4 members
        self.assertEqual(members[0].name, self.group.members_mcomm_users[0].name)  # Make sure first element is same

    def test_group_exists(self):
        self.assertEqual(True, self.group.exists)

    @patch('collab_eligibility_checker.mcommunity.mcommunity_base.MCommunityBase.search')
    def test_group_not_exists(self, magic_mock):
        magic_mock.side_effect = mocks.mcomm_side_effect
        with self.assertRaises(NameError):
            self.assertEqual(False, MCommunityGroup('fake', mocks.test_app, mocks.test_secret).exists)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main(verbosity=3)

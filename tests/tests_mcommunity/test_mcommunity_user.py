import logging
import unittest
from unittest.mock import patch

from collab_eligibility_checker.mcommunity.mcommunity_user import MCommunityUser
from tests.tests_mcommunity import mcommunity_mocks as mocks

test_user = 'nemcardf'


class MCommunityUserTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.patcher = patch('collab_eligibility_checker.mcommunity.mcommunity_base.MCommunityBase.search')
        self.mock = self.patcher.start()
        self.mock.side_effect = mocks.mcomm_side_effect
        self.user = MCommunityUser(test_user, mocks.test_app, mocks.test_secret)

    def test_init_sets_name(self):
        self.assertEqual(test_user, self.user.name)

    def test_init_sets_email(self):
        self.assertEqual(f'{test_user}@umich.edu', self.user.email)

    def test_user_not_exists(self):
        with self.assertRaises(NameError):
            user = MCommunityUser('fake', mocks.test_app, mocks.test_secret)
            self.assertEqual(False, user.exists)

    def test_user_exists(self):
        self.assertEqual(True, self.user.exists)

    def test_init_sets_entityid(self):
        self.assertEqual('00000000', self.user.entityid)

    def test_init_sets_display_name(self):
        self.assertEqual('Natalie Emcard', self.user.display_name)

    def test_init_sets_raw_result(self):
        self.assertEqual(mocks.faculty_mock, self.user.raw_result)
        self.assertEqual(list, type(self.user.raw_result))
        self.assertEqual(1, len(self.user.raw_result))  # LDAP should always return a 1-item list for a real person
        self.assertEqual(2, len(self.user.raw_result[0]))  # LDAP should always return a 2-item tuple for a real person

    def test_check_service_entitlements_eligible(self):
        self.assertEqual(True, self.user.check_service_entitlement('enterprise'))

    def test_check_service_entitlements_not_eligible(self):
        user = MCommunityUser('nemcardr', mocks.test_app, mocks.test_secret)  # Retiree uniqname
        self.assertEqual(False, user.check_service_entitlement('enterprise'))

    def test_check_sponsorship_type_sa1(self):
        user = MCommunityUser('nemcardsa1', mocks.test_app, mocks.test_secret)
        self.assertEqual(1, user.check_sponsorship_type())

    def test_check_sponsorship_type_sa2(self):
        user = MCommunityUser('nemcardsa2', mocks.test_app, mocks.test_secret)
        self.assertEqual(2, user.check_sponsorship_type())

    def test_check_sponsorship_type_sa3(self):
        user = MCommunityUser('um999999', mocks.test_app, mocks.test_secret)
        self.assertEqual(3, user.check_sponsorship_type())

    def test_check_sponsorship_type_not_sponsored(self):
        self.assertEqual(0, self.user.check_sponsorship_type())

    def test_populate_affiliations(self):
        self.assertEqual([], self.user.affiliations)  # Before populating, there should not be any
        self.user.populate_affiliations()
        self.assertEqual([
            'FacultyAA', 'RegularStaffDBRN', 'StudentFLNT', 'TemporaryStaffFLNT', 'SponsoredAffiliateAA',
            'Retiree', 'AlumniAA'
        ], self.user.affiliations)

    def test_populate_highest_affiliation_faculty(self):
        self.assertEqual('', self.user.highest_affiliation)
        self.user.populate_highest_affiliation()
        self.assertEqual('Faculty', self.user.highest_affiliation)

    def test_populate_highest_affiliation_regstaff(self):
        user = MCommunityUser('nemcardrs', mocks.test_app, mocks.test_secret)
        self.assertEqual('', user.highest_affiliation)
        user.populate_highest_affiliation()
        self.assertEqual('RegularStaff', user.highest_affiliation)

    def test_populate_highest_affiliation_student(self):
        user = MCommunityUser('nemcards', mocks.test_app, mocks.test_secret)
        self.assertEqual('', user.highest_affiliation)
        user.populate_highest_affiliation()
        self.assertEqual('Student', user.highest_affiliation)

    def test_populate_highest_affiliation_tempstaff(self):
        user = MCommunityUser('nemcardts', mocks.test_app, mocks.test_secret)
        self.assertEqual('', user.highest_affiliation)
        user.populate_highest_affiliation()
        self.assertEqual('TemporaryStaff', user.highest_affiliation)

    def test_populate_highest_affiliation_sa1(self):
        user = MCommunityUser('nemcardsa1', mocks.test_app, mocks.test_secret)
        self.assertEqual('', user.highest_affiliation)
        user.populate_highest_affiliation()
        self.assertEqual('SponsoredAffiliate', user.highest_affiliation)

    def test_populate_highest_affiliation_retiree(self):
        user = MCommunityUser('nemcardr', mocks.test_app, mocks.test_secret)
        self.assertEqual('', user.highest_affiliation)
        user.populate_highest_affiliation()
        self.assertEqual('Retiree', user.highest_affiliation)

    def test_populate_highest_affiliation_alumni(self):
        user = MCommunityUser('nemcarda', mocks.test_app, mocks.test_secret)
        self.assertEqual('', user.highest_affiliation)
        user.populate_highest_affiliation()
        self.assertEqual('Alumni', user.highest_affiliation)

    def test_populate_highest_affiliation_na(self):
        with self.assertRaises(NameError):
            user = MCommunityUser('fake', mocks.test_app, mocks.test_secret)
            self.assertEqual('', user.highest_affiliation)
            user.populate_highest_affiliation()
            self.assertEqual('NA', user.highest_affiliation)

    def tearDown(self) -> None:
        self.patcher.stop()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main(verbosity=3)

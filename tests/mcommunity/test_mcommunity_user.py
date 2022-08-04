import logging
import unittest
from unittest.mock import patch

from mcommunity.mcommunity_user import MCommunityUser
from tests.mcommunity import mcommunity_mocks
from tests.mcommunity.test_mcommunity_base import test_app, test_secret

test_user = 'nemcardf'


def custom_side_effect(*args):
    user = args[0]
    if user == 'nemcardf':
        return mcommunity_mocks.faculty_mock
    elif user == 'nemcardrs':
        return mcommunity_mocks.regstaff_mock
    elif user == 'nemcards':
        return mcommunity_mocks.student_mock
    elif user == 'nemcardts':
        return mcommunity_mocks.tempstaff_mock
    elif user == 'nemcardsa1':
        return mcommunity_mocks.t1sponsored_mock
    elif user == 'nemcardsa2':
        return mcommunity_mocks.t2sponsored_mock
    elif user == 'um999999':
        return mcommunity_mocks.t3sponsored_mock
    elif user == 'nemcardr':
        return mcommunity_mocks.retiree_mock
    elif user == 'nemcarda':
        return mcommunity_mocks.alumni_mock
    else:
        return mcommunity_mocks.fake_mock


class MCommunityUserTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.patcher = patch('mcommunity.mcommunity_user.MCommunityUser._populate_user_data')
        self.mock = self.patcher.start()
        self.mock.side_effect = custom_side_effect
        self.user = MCommunityUser(test_user, test_app, test_secret)

    def test_decode_str(self):
        self.assertEqual('test_decoding_str', self.user._decode('test_str'))

    def test_decode_single_item_list_as_list(self):
        self.assertEqual(['Natalie Emcard'], self.user._decode('cn', return_str_if_single_item_list=False))

    def test_decode_single_item_list_as_str(self):
        self.assertEqual('Natalie Emcard', self.user._decode('cn'))

    def test_decode_list(self):
        self.assertEqual([
            'FacultyAA', 'RegularStaffDBRN', 'StudentFLNT', 'TemporaryStaffFLNT', 'SponsoredAffiliateAA',
            'Retiree', 'AlumniAA'
        ], self.user._decode('umichInstRoles', return_str_if_single_item_list=False))

    def test_init_sets_dn(self):
        self.assertEqual(test_user, self.user.dn)

    def test_init_sets_email(self):
        self.assertEqual(f'{test_user}@umich.edu', self.user.email)

    def test_user_not_exists(self):
        user = MCommunityUser('fake', test_app, test_secret)
        self.assertEqual(False, user.exists)

    def test_user_exists(self):
        self.assertEqual(True, self.user.exists)

    def test_init_sets_entityid(self):
        self.assertEqual('00000000', self.user.entityid)

    def test_init_sets_name(self):
        self.assertEqual('Natalie Emcard', self.user.name)

    def test_init_sets_raw_user(self):
        self.assertEqual(mcommunity_mocks.faculty_mock, self.user.raw_user)
        self.assertEqual(list, type(self.user.raw_user))
        self.assertEqual(1, len(self.user.raw_user))  # LDAP should always return a 1-item list for a real person
        self.assertEqual(2, len(self.user.raw_user[0]))  # LDAP should always return a 2-item tuple for a real person

    def test_check_service_entitlements_eligible(self):
        self.assertEqual(True, self.user.check_service_entitlement('enterprise'))

    def test_check_service_entitlements_not_eligible(self):
        user = MCommunityUser('nemcardr', test_app, test_secret)  # Retiree uniqname
        self.assertEqual(False, user.check_service_entitlement('enterprise'))

    def test_check_sponsorship_type_sa1(self):
        user = MCommunityUser('nemcardsa1', test_app, test_secret)
        self.assertEqual(1, user.check_sponsorship_type())

    def test_check_sponsorship_type_sa2(self):
        user = MCommunityUser('nemcardsa2', test_app, test_secret)
        self.assertEqual(2, user.check_sponsorship_type())

    def test_check_sponsorship_type_sa3(self):
        user = MCommunityUser('um999999', test_app, test_secret)
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
        user = MCommunityUser('nemcardrs', test_app, test_secret)
        self.assertEqual('', user.highest_affiliation)
        user.populate_highest_affiliation()
        self.assertEqual('RegularStaff', user.highest_affiliation)

    def test_populate_highest_affiliation_student(self):
        user = MCommunityUser('nemcards', test_app, test_secret)
        self.assertEqual('', user.highest_affiliation)
        user.populate_highest_affiliation()
        self.assertEqual('Student', user.highest_affiliation)

    def test_populate_highest_affiliation_tempstaff(self):
        user = MCommunityUser('nemcardts', test_app, test_secret)
        self.assertEqual('', user.highest_affiliation)
        user.populate_highest_affiliation()
        self.assertEqual('TemporaryStaff', user.highest_affiliation)

    def test_populate_highest_affiliation_sa1(self):
        user = MCommunityUser('nemcardsa1', test_app, test_secret)
        self.assertEqual('', user.highest_affiliation)
        user.populate_highest_affiliation()
        self.assertEqual('SponsoredAffiliate', user.highest_affiliation)

    def test_populate_highest_affiliation_retiree(self):
        user = MCommunityUser('nemcardr', test_app, test_secret)
        self.assertEqual('', user.highest_affiliation)
        user.populate_highest_affiliation()
        self.assertEqual('Retiree', user.highest_affiliation)

    def test_populate_highest_affiliation_alumni(self):
        user = MCommunityUser('nemcarda', test_app, test_secret)
        self.assertEqual('', user.highest_affiliation)
        user.populate_highest_affiliation()
        self.assertEqual('Alumni', user.highest_affiliation)

    def test_populate_highest_affiliation_na(self):
        user = MCommunityUser('fake', test_app, test_secret)
        self.assertEqual('', user.highest_affiliation)
        user.populate_highest_affiliation()
        self.assertEqual('NA', user.highest_affiliation)

    def tearDown(self) -> None:
        self.patcher.stop()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main(verbosity=3)

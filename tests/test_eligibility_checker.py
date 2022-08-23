import logging
import unittest
from unittest.mock import patch

from eligibility_checker.checker import EligibilityChecker
from mcommunity.mcommunity_user import MCommunityUser
import mcommunity.mcommunity_mocks as mocks

test_user = 'nemcardf'


class EligibilityCheckerUSETestClass(EligibilityChecker):
    service_friendly = 'Test Service with uSE'


class EligibilityCheckerAffiliationsTestClass(EligibilityChecker):
    service_friendly = 'Test Service with no uSE'
    service_entitlement = None


class EligibilityCheckerTestCase(unittest.TestCase):
    checker_use = None
    checker_affils = None

    @classmethod
    @patch('mcommunity.mcommunity_base.MCommunityBase.search')
    def setUpClass(cls, magic_mock) -> None:
        magic_mock.side_effect = mocks.mcomm_side_effect
        cls.checker_use = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)
        cls.checker_affils = EligibilityCheckerAffiliationsTestClass(mocks.test_app, mocks.test_secret)

    def setUp(self) -> None:
        self.patcher = patch('mcommunity.mcommunity_base.MCommunityBase.search')
        self.mock = self.patcher.start()
        self.mock.side_effect = mocks.mcomm_side_effect

    def test_init_populates_override_group_members(self):
        self.assertEqual(['nemcardf', 'nemcardrs', 'nemcarda'], self.checker_use.override_group_members)

    @patch('eligibility_checker.checker.EligibilityChecker._validate')
    def test_init_validates_attributes(self, magic_mock):
        EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)
        self.assertTrue(magic_mock.called)

    def test_check_affiliation_eligibility_sa_eligible(self):
        user = MCommunityUser('nemcardsa1', self.checker_use.mcommunity_app_cn, self.checker_use.mcommunity_secret)
        response = self.checker_use._check_affiliation_eligibility(user)
        self.assertEqual(True, response.eligible)
        self.assertEqual('Sponsored affiliates t1 are eligible for Test Service with uSE', response.reason)
        self.assertIsInstance(response.user, MCommunityUser)
        self.assertIsNone(response.errors)

    def test_check_affiliation_eligibility_sa_ineligible(self):
        user = MCommunityUser('um999999', self.checker_use.mcommunity_app_cn, self.checker_use.mcommunity_secret)
        response = self.checker_use._check_affiliation_eligibility(user)
        self.assertEqual(False, response.eligible)
        self.assertEqual('Sponsored affiliates t3 are not eligible for Test Service with uSE', response.reason)
        self.assertIsInstance(response.user, MCommunityUser)
        self.assertIsNone(response.errors)

    def test_check_affiliation_eligibility_sa_ineligible_override_eligible_types(self):
        user = MCommunityUser('nemcardsa2', self.checker_use.mcommunity_app_cn, self.checker_use.mcommunity_secret)
        self.assertEqual(False, self.checker_use._check_affiliation_eligibility(user).eligible)  # Control
        self.checker_use.eligible_sa_types.append(2)  # Make type 2s eligible
        self.assertEqual(True, self.checker_use._check_affiliation_eligibility(user).eligible)
        self.checker_use.eligible_sa_types = [1]  # Reset

    def test_check_affiliation_eligibility_faculty_eligible(self):
        user = MCommunityUser('nemcardf', self.checker_use.mcommunity_app_cn, self.checker_use.mcommunity_secret)
        response = self.checker_use._check_affiliation_eligibility(user)
        self.assertEqual(True, response.eligible)
        self.assertEqual('Faculty are eligible for Test Service with uSE', response.reason)
        self.assertIsInstance(response.user, MCommunityUser)
        self.assertIsNone(response.errors)

    def test_check_affiliation_eligibility_retiree_ineligible(self):
        user = MCommunityUser('nemcardr', self.checker_use.mcommunity_app_cn, self.checker_use.mcommunity_secret)
        response = self.checker_use._check_affiliation_eligibility(user)
        self.assertEqual(False, response.eligible)
        self.assertEqual('Retiree are not eligible for Test Service with uSE', response.reason)
        self.assertIsInstance(response.user, MCommunityUser)
        self.assertIsNone(response.errors)

    def test_check_affiliation_eligibility_student_override_eligible_types(self):
        user = MCommunityUser('nemcards', self.checker_use.mcommunity_app_cn, self.checker_use.mcommunity_secret)
        self.assertEqual(True, self.checker_use._check_affiliation_eligibility(user).eligible)  # Control
        self.checker_use.eligible_affiliations_minus_sa = [
            'Faculty', 'RegularStaff', 'TemporaryStaff'
        ]  # Make students ineligible
        self.assertEqual(False, self.checker_use._check_affiliation_eligibility(user).eligible)
        self.checker_use.eligible_affiliations_minus_sa = ['Faculty', 'RegularStaff', 'Student', 'TemporaryStaff']

    def test_check_eligibility_override(self):
        response = self.checker_use.check_eligibility('nemcarda', validate_affiliation=False)
        self.assertEqual(True, response.eligible)
        self.assertEqual('Override group member', response.reason)
        self.assertIsInstance(response.user, MCommunityUser)
        self.assertIsNone(response.errors)

    def test_use_check_eligibility_no_validation_not_eligible(self):
        response = self.checker_use.check_eligibility('nemcardr', validate_affiliation=False)
        self.assertEqual(False, response.eligible)
        self.assertEqual('enterprise entitlement is False', response.reason)
        self.assertIsInstance(response.user, MCommunityUser)
        self.assertIsNone(response.errors)

    def test_use_check_eligibility_with_validation_not_eligible(self):
        response = self.checker_use.check_eligibility('nemcardr')
        self.assertEqual(False, response.eligible)
        self.assertEqual('enterprise entitlement is False', response.reason)
        self.assertIsInstance(response.user, MCommunityUser)
        self.assertIsNone(response.errors)

    def test_use_check_eligibility_no_validation_eligible(self):
        response = self.checker_use.check_eligibility('nemcards', validate_affiliation=False)
        self.assertEqual(True, response.eligible)
        self.assertEqual('enterprise entitlement is True', response.reason)
        self.assertIsInstance(response.user, MCommunityUser)
        self.assertIsNone(response.errors)

    def test_use_check_eligibility_with_validation_eligible(self):
        response = self.checker_use.check_eligibility('nemcardts')
        self.assertEqual(True, response.eligible)
        self.assertEqual('enterprise entitlement is True', response.reason)
        self.assertIsInstance(response.user, MCommunityUser)
        self.assertIsNone(response.errors)

    def test_use_check_eligibility_with_validation_error(self):
        # No enterprise uSE, but faculty is highest affiliation
        response = self.checker_use.check_eligibility('nemcardferr')
        self.assertEqual(True, response.eligible)
        self.assertEqual(
            'Highest affiliation Faculty shows nemcardferr should have a valid enterprise entitlement but they do not',
            response.reason)
        self.assertIsInstance(response.user, MCommunityUser)
        self.assertIsInstance(response.errors, RuntimeError)

    def test_use_check_eligibility_with_validation_alum_hanging_use(self):
        # Alumni are ineligible but still has uSE to simulate alumni within 30 days post-grad--should not error
        response = self.checker_use.check_eligibility('nemcardaerr')
        self.assertEqual(True, response.eligible)
        self.assertEqual('enterprise entitlement is True', response.reason)
        self.assertIsInstance(response.user, MCommunityUser)
        self.assertIsNone(response.errors)

    def test_use_check_eligibility_na(self):
        # check_eligibility should suppress the NameError and return False
        response = self.checker_use.check_eligibility('fake')
        self.assertEqual(False, response.eligible)
        self.assertEqual('No user found in MCommunity for fake', response.reason)
        self.assertIsInstance(response.user, MCommunityUser)
        self.assertIsInstance(response.errors, NameError)

    def test_affils_check_eligibility_not_eligible(self):
        response = self.checker_affils.check_eligibility('nemcardr')
        self.assertEqual(False, response.eligible)
        self.assertEqual('Retiree are not eligible for Test Service with no uSE', response.reason)
        self.assertIsInstance(response.user, MCommunityUser)
        self.assertIsNone(response.errors)

    def test_affils_check_eligibility_eligible(self):
        response = self.checker_affils.check_eligibility('nemcards')
        self.assertEqual(True, response.eligible)
        self.assertEqual('Student are eligible for Test Service with no uSE', response.reason)
        self.assertIsInstance(response.user, MCommunityUser)
        self.assertIsNone(response.errors)

    def test_affils_check_eligibility_na(self):
        # check_eligibility should suppress the NameError and return False
        response = self.checker_affils.check_eligibility('fake')
        self.assertEqual(False, response.eligible)
        self.assertEqual('No user found in MCommunity for fake', response.reason)
        self.assertIsInstance(response.user, MCommunityUser)
        self.assertIsInstance(response.errors, NameError)

    def test_validate_errors_if_no_admins(self):
        self.checker_use.override_groups = []
        with self.assertRaises(RuntimeError):
            self.checker_use._validate()
        self.checker_use.override_groups = ['collab-iam-admins']

    def test_validate_errors_if_sa_in_affils(self):
        self.checker_use.eligible_affiliations_minus_sa.append('SponsoredAffiliate')
        with self.assertRaises(RuntimeError):
            self.checker_use._validate()
        self.checker_use.eligible_affiliations_minus_sa = ['Faculty', 'RegularStaff', 'Student', 'TemporaryStaff']

    def test_validate_warns_if_affils_too_short(self):
        self.checker_use.eligible_affiliations_minus_sa = self.checker_use.eligible_affiliations_minus_sa[:3]
        with self.assertRaises(UserWarning):
            self.checker_use._validate()
        self.checker_use.eligible_affiliations_minus_sa = ['Faculty', 'RegularStaff', 'Student', 'TemporaryStaff']

    def test_validate_errors_if_invalid_affil(self):
        self.checker_use.eligible_affiliations_minus_sa.append('TestAffil')
        with self.assertRaises(RuntimeError):
            self.checker_use._validate()
        self.checker_use.eligible_affiliations_minus_sa = ['Faculty', 'RegularStaff', 'Student', 'TemporaryStaff']

    def test_validate_errors_if_affils_empty(self):
        self.checker_use.eligible_affiliations_minus_sa = []
        with self.assertRaises(RuntimeError):
            self.checker_use._validate()
        self.checker_use.eligible_affiliations_minus_sa = ['Faculty', 'RegularStaff', 'Student', 'TemporaryStaff']

    def test_validate_errors_if_invalid_sa_type(self):
        self.checker_use.eligible_sa_types.append(5)
        with self.assertRaises(RuntimeError):
            self.checker_use._validate()
        self.checker_use.eligible_sa_types = [1, 'blah']
        with self.assertRaises(RuntimeError):
            self.checker_use._validate()
        self.checker_use.eligible_sa_types = [1]

    def test_validate_warn_if_sa_types_empty(self):
        self.checker_use.eligible_sa_types = []
        with self.assertRaises(UserWarning):
            self.checker_use._validate()
        self.checker_use.eligible_sa_types = [1]

    def tearDown(self) -> None:
        self.patcher.stop()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main(verbosity=3)

import logging
import unittest
from unittest.mock import patch

from collab_eligibility_checker.checker import EligibilityChecker
from tests.tests_mcommunity import mcommunity_mocks as mocks
from collab_eligibility_checker.mcommunity.mcommunity_user import MCommunityUser

test_user = 'nemcardf'


class EligibilityCheckerUSETestClass(EligibilityChecker):
    service_friendly = 'Test Service with uSE'

    def _deprovision(self, uniqname) -> bool:
        return True


class EligibilityCheckerAffiliationsTestClass(EligibilityChecker):
    service_friendly = 'Test Service with no uSE'
    service_entitlement = None

    def _deprovision(self, uniqname) -> bool:
        return True


class EligibilityCheckerTestCase(unittest.TestCase):
    checker_use = None
    checker_affils = None

    @classmethod
    @patch('collab_eligibility_checker.mcommunity.mcommunity_base.MCommunityBase.search')
    def setUpClass(cls, magic_mock) -> None:
        magic_mock.side_effect = mocks.mcomm_side_effect
        cls.checker_use = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)
        cls.checker_affils = EligibilityCheckerAffiliationsTestClass(mocks.test_app, mocks.test_secret)

    def setUp(self) -> None:
        self.patcher = patch('collab_eligibility_checker.mcommunity.mcommunity_base.MCommunityBase.search')
        self.mock = self.patcher.start()
        self.mock.side_effect = mocks.mcomm_side_effect

    def test_init_populates_override_group_members(self):
        self.assertEqual(['nemcardf', 'nemcardrs', 'nemcarda', 'nemcards'], self.checker_use.override_group_members)

    @patch('collab_eligibility_checker.checker.EligibilityChecker._validate')
    def test_init_validates_attributes(self, magic_mock):
        EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)
        self.assertTrue(magic_mock.called)

    def test_check_affiliation_eligibility_sa_eligible(self):
        user = MCommunityUser('nemcardsa1', self.checker_use.mcommunity_app_cn, self.checker_use.mcommunity_secret)
        self.assertEqual(True, self.checker_use._check_affiliation_eligibility(user))

    def test_check_affiliation_eligibility_sa_ineligible(self):
        user = MCommunityUser('um999999', self.checker_use.mcommunity_app_cn, self.checker_use.mcommunity_secret)
        self.assertEqual(False, self.checker_use._check_affiliation_eligibility(user))

    def test_check_affiliation_eligibility_sa_ineligible_override_eligible_types(self):
        user = MCommunityUser('nemcardsa2', self.checker_use.mcommunity_app_cn, self.checker_use.mcommunity_secret)
        self.assertEqual(False, self.checker_use._check_affiliation_eligibility(user))  # Control
        self.checker_use.eligible_sa_types.append(2)  # Make type 2s eligible
        self.assertEqual(True, self.checker_use._check_affiliation_eligibility(user))
        self.checker_use.eligible_sa_types = [1]  # Reset

    def test_check_affiliation_eligibility_faculty_eligible(self):
        user = MCommunityUser('nemcardf', self.checker_use.mcommunity_app_cn, self.checker_use.mcommunity_secret)
        self.assertEqual(True, self.checker_use._check_affiliation_eligibility(user))

    def test_check_affiliation_eligibility_retiree_ineligible(self):
        user = MCommunityUser('nemcardr', self.checker_use.mcommunity_app_cn, self.checker_use.mcommunity_secret)
        self.assertEqual(False, self.checker_use._check_affiliation_eligibility(user))

    def test_check_affiliation_eligibility_student_override_eligible_types(self):
        user = MCommunityUser('nemcards', self.checker_use.mcommunity_app_cn, self.checker_use.mcommunity_secret)
        self.assertEqual(True, self.checker_use._check_affiliation_eligibility(user))  # Control
        self.checker_use.eligible_affiliations_minus_sa = [
            'Faculty', 'RegularStaff', 'TemporaryStaff'
        ]  # Make students ineligible
        self.assertEqual(False, self.checker_use._check_affiliation_eligibility(user))
        self.checker_use.eligible_affiliations_minus_sa = ['Faculty', 'RegularStaff', 'Student', 'TemporaryStaff']

    def test_check_eligibility_override(self):
        self.assertEqual(True, self.checker_use.check_eligibility('nemcarda', validate_affiliation=False))

    def test_use_check_eligibility_no_validation_not_eligible(self):
        self.assertEqual(False, self.checker_use.check_eligibility('nemcardr', validate_affiliation=False))

    def test_use_check_eligibility_with_validation_not_eligible(self):
        self.assertEqual(False, self.checker_use.check_eligibility('nemcardr'))

    def test_use_check_eligibility_no_validation_eligible(self):
        self.assertEqual(True, self.checker_use.check_eligibility('nemcardrs', validate_affiliation=False))

    def test_use_check_eligibility_with_validation_eligible(self):
        self.assertEqual(True, self.checker_use.check_eligibility('nemcardts'))

    def test_use_check_eligibility_with_validation_error(self):
        with self.assertRaises(RuntimeError):
            self.checker_use.check_eligibility('nemcardferr')  # No enterprise uSE, but faculty is highest affiliation

    def test_use_check_eligibility_with_validation_alum_hanging_use(self):
        # Alumni are ineligible but still has uSE to simulate alumni within 30 days post-grad--should not error
        self.assertEqual(True, self.checker_use.check_eligibility('nemcardaerr'))

    def test_use_check_eligibility_na(self):
        # check_eligibility should suppress the NameError and return False
        self.assertEqual(False, self.checker_use.check_eligibility('fake'))

    def test_affils_check_eligibility_not_eligible(self):
        self.assertEqual(False, self.checker_affils.check_eligibility('nemcardr'))

    def test_affils_check_eligibility_eligible(self):
        self.assertEqual(True, self.checker_affils.check_eligibility('nemcardrs'))

    def test_affils_check_eligibility_na(self):
        # check_eligibility should suppress the NameError and return False
        self.assertEqual(False, self.checker_affils.check_eligibility('fake'))

    def test_deprovision_account_eligible(self):
        self.assertEqual(False, self.checker_use.deprovision_account_if_ineligible('nemcardf'))

    def test_deprovision_account_ineligible(self):
        with patch.object(self.checker_use, '_deprovision', return_value=True) as magic_mock:
            self.checker_use.deprovision_account_if_ineligible('nemcardr')
            self.assertTrue(magic_mock.called)

    def test_deprovision_account_error(self):
        self.assertEqual(False, self.checker_use.deprovision_account_if_ineligible('nemcardferr'))

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

from copy import deepcopy
import logging
from unittest import main, TestCase
from unittest.mock import patch

from eligibility_checker.checker import EligibilityChecker
from mcommunity import MCommunityUser
import mcommunity.mcommunity_mocks as mocks

test_user = 'nemcardf'


class EligibilityCheckerUSETestClass(EligibilityChecker):
    service_friendly = 'Test Service with uSE'
    override_groups = ['collab-iam-admins', 'something-iam-primary']


class EligibilityCheckerAffiliationsTestClass(EligibilityChecker):
    service_friendly = 'Test Service with no uSE'
    service_entitlement = None
    override_groups = ['collab-iam-admins', 'something-iam-primary']


class EligibilityCheckerEmptyOverrideTestCase(TestCase):
    @patch('mcommunity.mcommunity_base.MCommunityBase.search')
    def test_init_raises_exception_if_empty_override_group(self, magic_mock):
        magic_mock.return_value = [('cn=collab-iam-admins,ou=User Groups,ou=Groups,dc=umich,dc=edu',
                                    {'umichGroupEmail': [b'collab.iam.admins'], 'cn': [b'collab-iam-admins']})]
        with self.assertRaises(RuntimeError):
            EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)


class EligibilityCheckerTestCase(TestCase):

    def setUp(self) -> None:
        self.patcher = patch('mcommunity.mcommunity_base.MCommunityBase.search')
        self.mock = self.patcher.start()
        self.mock.side_effect = mocks.mcomm_side_effect

    def tearDown(self) -> None:
        patch.stopall()

    def test_init_populates_override_group_members(self):
        c = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)
        self.assertCountEqual(['nemcardf', 'nemcardrs', 'nemcarda', 'nemcardts'], c.override_group_members)

    @patch('eligibility_checker.checker.EligibilityChecker._validate')
    def test_init_validates_attributes(self, magic_mock):
        EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)
        self.assertTrue(magic_mock.called)

    def test_validate_errors_if_no_admins(self):
        with self.assertRaises(RuntimeError):
            c = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)
            c.override_groups = []
            c._validate()

    def test_validate_errors_if_sa_in_affils(self):
        with self.assertRaises(RuntimeError):
            c = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)
            affils = deepcopy(c.eligible_affiliations_minus_sa).append('SponsoredAffiliate')
            c.eligible_affiliations_minus_sa = affils
            c._validate()

    def test_validate_warns_if_affils_too_short(self):
        current_eligible = EligibilityCheckerUSETestClass.eligible_affiliations_minus_sa[:3]
        with self.assertWarns(Warning):
            c = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)
            c.eligible_affiliations_minus_sa = current_eligible.copy()
            c._validate()

    def test_validate_errors_if_invalid_affil(self):
        with self.assertRaises(RuntimeError):
            c = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)
            affils = deepcopy(c.eligible_affiliations_minus_sa).append('TestAffil')
            c.eligible_affiliations_minus_sa = affils
            c._validate()

    def test_validate_errors_if_affils_empty(self):
        with self.assertRaises(RuntimeError):
            c = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)
            c.eligible_affiliations_minus_sa = []
            c._validate()

    def test_validate_errors_if_invalid_sa_type(self):
        with self.assertRaises(RuntimeError):
            c = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)
            c.eligible_sa_types = [1, 'blah', 5]
            c._validate()

    def test_validate_warn_if_sa_types_empty(self):
        with self.assertWarns(Warning):
            c = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)
            c.eligible_sa_types = []
            c._validate()

    def test_check_affiliation_eligibility_sa_eligible(self):
        user = MCommunityUser('nemcardsa1', mocks.test_app, mocks.test_secret)
        c = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)
        r = c._check_affiliation_eligibility(user)
        self.assertEqual(True, r.eligible)
        self.assertEqual('Sponsored affiliates t1 are eligible for Test Service with uSE', r.reason)
        self.assertIsInstance(r.user, MCommunityUser)
        self.assertIsNone(r.errors)

    def test_check_affiliation_eligibility_sa_ineligible(self):
        user = MCommunityUser('um999999', mocks.test_app, mocks.test_secret)
        r = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)._check_affiliation_eligibility(user)
        self.assertEqual(False, r.eligible)
        self.assertEqual('Sponsored affiliates t3 are not eligible for Test Service with uSE', r.reason)
        self.assertIsInstance(r.user, MCommunityUser)
        self.assertIsNone(r.errors)

    def test_check_affiliation_eligibility_sa_ineligible_override_eligible_types(self):
        user = MCommunityUser('nemcardsa2', mocks.test_app, mocks.test_secret)
        c = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)
        self.assertEqual(False, c._check_affiliation_eligibility(user).eligible)  # Control
        c.eligible_sa_types.append(2)  # Make type 2s eligible
        self.assertEqual(True, c._check_affiliation_eligibility(user).eligible)

    def test_check_affiliation_eligibility_faculty_eligible(self):
        user = MCommunityUser('nemcardf', mocks.test_app, mocks.test_secret)
        r = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)._check_affiliation_eligibility(user)
        self.assertEqual(True, r.eligible)
        self.assertEqual('Faculty are eligible for Test Service with uSE', r.reason)
        self.assertIsInstance(r.user, MCommunityUser)
        self.assertIsNone(r.errors)

    def test_check_affiliation_eligibility_retiree_ineligible(self):
        user = MCommunityUser('nemcardr', mocks.test_app, mocks.test_secret)
        r = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)._check_affiliation_eligibility(user)
        self.assertEqual(False, r.eligible)
        self.assertEqual('Retiree are not eligible for Test Service with uSE', r.reason)
        self.assertIsInstance(r.user, MCommunityUser)
        self.assertIsNone(r.errors)

    def test_check_affiliation_eligibility_student_override_eligible_types(self):
        user = MCommunityUser('nemcards', mocks.test_app, mocks.test_secret)
        c = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret)
        self.assertEqual(True, c._check_affiliation_eligibility(user).eligible)  # Control
        c.eligible_affiliations_minus_sa = [
            'Faculty', 'RegularStaff', 'TemporaryStaff'
        ]  # Make students ineligible
        self.assertEqual(False, c._check_affiliation_eligibility(user).eligible)

    def test_check_eligibility_override(self):
        r = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret).check_eligibility(
            'nemcarda', validate_affiliation=False)
        self.assertEqual(True, r.eligible)
        self.assertEqual('Override group member', r.reason)
        self.assertIsInstance(r.user, MCommunityUser)
        self.assertIsNone(r.errors)

    # Tests for the service entitlement (USE) version
    def test_check_eligibility_no_validation_not_eligible(self):
        r = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret).check_eligibility(
            'nemcardr', validate_affiliation=False)
        self.assertEqual(False, r.eligible)
        self.assertEqual('enterprise entitlement is False', r.reason)
        self.assertIsInstance(r.user, MCommunityUser)
        self.assertIsNone(r.errors)

    def test_check_eligibility_with_validation_not_eligible(self):
        r = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret).check_eligibility('nemcardr')
        self.assertEqual(False, r.eligible)
        self.assertEqual('enterprise entitlement is False', r.reason)
        self.assertIsInstance(r.user, MCommunityUser)
        self.assertIsNone(r.errors)

    def test_check_eligibility_no_validation_eligible(self):
        r = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret).check_eligibility(
            'nemcards', validate_affiliation=False)
        self.assertEqual(True, r.eligible)
        self.assertEqual('enterprise entitlement is True', r.reason)
        self.assertIsInstance(r.user, MCommunityUser)
        self.assertIsNone(r.errors)

    def test_check_eligibility_with_validation_eligible(self):
        r = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret).check_eligibility('nemcardsa1')
        self.assertEqual(True, r.eligible)
        self.assertEqual('enterprise entitlement is True', r.reason)
        self.assertIsInstance(r.user, MCommunityUser)
        self.assertIsNone(r.errors)

    def test_check_eligibility_with_validation_error(self):
        # No enterprise uSE, but faculty is highest affiliation
        r = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret).check_eligibility('nemcardferr')
        self.assertEqual(True, r.eligible)
        self.assertEqual(
            'Highest affiliation Faculty shows nemcardferr should have a valid enterprise entitlement but they do not',
            r.reason)
        self.assertIsInstance(r.user, MCommunityUser)
        self.assertIsInstance(r.errors, RuntimeError)

    def test_check_eligibility_with_validation_alum_hanging_use(self):
        # Alumni are ineligible but still has uSE to simulate alumni within 30 days post-grad--should not error
        r = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret).check_eligibility('nemcardaerr')
        self.assertEqual(True, r.eligible)
        self.assertEqual('enterprise entitlement is True', r.reason)
        self.assertIsInstance(r.user, MCommunityUser)
        self.assertIsNone(r.errors)

    def test_check_eligibility_na(self):
        # check_eligibility should suppress the NameError and return False
        r = EligibilityCheckerUSETestClass(mocks.test_app, mocks.test_secret).check_eligibility('fake')
        self.assertEqual(False, r.eligible)
        self.assertEqual('No user found in MCommunity for fake', r.reason)
        self.assertIsInstance(r.user, MCommunityUser)
        self.assertIsInstance(r.errors, NameError)

    # Tests for the affiliation version
    def test_affils_check_eligibility_not_eligible(self):
        r = EligibilityCheckerAffiliationsTestClass(mocks.test_app, mocks.test_secret).check_eligibility('nemcardr')
        self.assertEqual(False, r.eligible)
        self.assertEqual('Retiree are not eligible for Test Service with no uSE', r.reason)
        self.assertIsInstance(r.user, MCommunityUser)
        self.assertIsNone(r.errors)

    def test_affils_check_eligibility_eligible(self):
        r = EligibilityCheckerAffiliationsTestClass(mocks.test_app, mocks.test_secret).check_eligibility('nemcards')
        self.assertEqual(True, r.eligible)
        self.assertEqual('Student are eligible for Test Service with no uSE', r.reason)
        self.assertIsInstance(r.user, MCommunityUser)
        self.assertIsNone(r.errors)

    def test_affils_check_eligibility_na(self):
        # check_eligibility should suppress the NameError and return False
        r = EligibilityCheckerAffiliationsTestClass(mocks.test_app, mocks.test_secret).check_eligibility('fake')
        self.assertEqual(False, r.eligible)
        self.assertEqual('No user found in MCommunity for fake', r.reason)
        self.assertIsInstance(r.user, MCommunityUser)
        self.assertIsInstance(r.errors, NameError)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main(verbosity=3)

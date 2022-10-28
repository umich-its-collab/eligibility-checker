import json
import unittest
from unittest.mock import patch

from eligibility_checker.checker import CheckEligibilityResponse
from mcommunity.mcommunity_user import MCommunityUser
import mcommunity.mcommunity_mocks as mocks

test_user = 'nemcardf'


class CheckEligibilityResponseTestCase(unittest.TestCase):

    @patch('mcommunity.mcommunity_base.MCommunityBase.search')
    def setUp(self, magic_mock) -> None:
        magic_mock.side_effect = mocks.mcomm_side_effect
        self.response_valid = CheckEligibilityResponse(
            eligible=True,
            reason='reason',
            user=MCommunityUser('nemcardf', mocks.test_app, mocks.test_secret),
            errors=None
        )
        self.response_invalid = CheckEligibilityResponse(
            eligible=False,
            reason='not exists',
            user=MCommunityUser('fake', mocks.test_app, mocks.test_secret),
            errors=Exception('exception')
        )

    def test_to_dict_converts_mcommunity_user_to_dict(self):
        self.assertIsInstance(self.response_valid.to_dict()['user'], dict)

    def test_to_dict_creates_json_serializable_object_exception(self):
        self.assertEqual(self.response_invalid.to_dict()['errors'], "Exception('exception')")

    def test_to_dict_creates_json_serializable_object(self):
        with self.assertRaises(TypeError):  # Sanity check--should fail on TypeError without to_dict
            json.dumps(self.response_invalid)
        self.assertTrue(json.dumps(self.response_invalid.to_dict()))  # Now should pass since using to_dict

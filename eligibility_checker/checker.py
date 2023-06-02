import logging
from abc import ABC
from typing import Union, Optional
from warnings import warn

from mcommunity import MCommunityGroup, MCommunityUser

logger = logging.getLogger(__name__)


class CheckEligibilityResponse:
    eligible: bool
    reason: str
    user: MCommunityUser
    errors: Optional[BaseException]

    def __init__(self, eligible: bool, reason: str, user: MCommunityUser, errors: Optional[BaseException]):
        self.eligible = eligible
        self.reason = reason
        self.user = user
        self.errors = errors

        logger.info(f'{user.name} eligibility is {eligible} because {reason}.')

    def to_dict(self):
        d = self.__dict__.copy()
        d['user'] = self.user.to_dict()
        d['errors'] = self.errors.__repr__()
        return d


class EligibilityChecker(ABC):
    service_friendly: str  # Name of the service in Capital Case (ex: Google, Microsoft Teams, Slack)
    service_entitlement: Union[str, None] = 'enterprise'  # umichServiceEntitlement (uSE) to reference
    # service_entitlement should be None if this service doesn't rely on uSE and only on affiliations

    override_groups: list = ['collab-iam-admins']
    override_group_members: list = []

    eligible_affiliations_minus_sa: list = ['Faculty', 'RegularStaff', 'Student', 'TemporaryStaff']
    eligible_sa_types: list = [1]

    mcommunity_app_cn: str = ''
    mcommunity_secret: str = ''

    slack_errors_channel: str = ''

    def __init__(self, mcommunity_app_cn, mcommunity_secret):
        self.mcommunity_app_cn = mcommunity_app_cn
        self.mcommunity_secret = mcommunity_secret
        if not self.override_group_members:  # Don't overwrite if it is already populated
            for group in self.override_groups:  # Populate override_group_members
                members = MCommunityGroup(group, self.mcommunity_app_cn, self.mcommunity_secret).members
                if not members:
                    raise RuntimeError(f'Got 0 members for {group}. If the group is not being used anymore, remove it '
                                       f'from override_groups. If it is being used and has members, make sure the '
                                       f'MCommunity app {self.mcommunity_app_cn} is an owner of the MCommunity group '
                                       f'to give it access to read group membership.')
                self.override_group_members += members
        self.override_group_members = list(set(self.override_group_members))  # Remove duplicates
        self._validate()

    ##################
    # Public Methods #
    ##################
    def check_eligibility(self, uniqname: str, validate_affiliation: bool = True) -> CheckEligibilityResponse:
        """
        Check whether a given user is eligible for the service based on uSE if self.service_entitlement is set, else by
        affiliations only
        :param uniqname: the U-M username of the user to check for eligibility (i.e. before @umich.edu in their email)
        :param validate_affiliation: validate that the uSE seems aligned with the user's affiliation
        (use prior to destructive actions in case of bugs in uSE); no effect if self.service_entitlement is None
        :return: CheckEligibilityResponse object containing eligibility information
        """
        user = MCommunityUser(uniqname, self.mcommunity_app_cn, self.mcommunity_secret)
        if user.errors:
            return CheckEligibilityResponse(eligible=False, reason=str(user.errors), user=user, errors=user.errors)
        elif uniqname in self.override_group_members:
            return CheckEligibilityResponse(eligible=True, reason='Override group member', user=user, errors=None)
        else:
            if self.service_entitlement:  # This services relies on uSE for eligibility
                eligible = user.check_service_entitlement(self.service_entitlement)
                reason = f'{self.service_entitlement} entitlement is {eligible}'
                if validate_affiliation:
                    eligible_via_affiliations = self._check_affiliation_eligibility(user)
                    if not eligible and eligible_via_affiliations.eligible:
                        error = RuntimeError(
                            f'Highest affiliation {user.highest_affiliation} shows {user.name} should have a valid '
                            f'{self.service_entitlement} entitlement but they do not'
                        )
                        return CheckEligibilityResponse(eligible=True, reason=str(error), user=user, errors=error)
                    else:
                        logger.info(
                            f'{self.service_entitlement} service entitlement ({eligible}) and affiliations '
                            f'{user.highest_affiliation} validated for {user.name}.'
                        )
                        return CheckEligibilityResponse(eligible=eligible, reason=reason, user=user, errors=None)
                else:
                    return CheckEligibilityResponse(eligible=eligible, reason=reason, user=user, errors=None)
            else:  # This service does not rely on uSE for eligibility
                return self._check_affiliation_eligibility(user)  # No further validation necessary or possible

    ###################
    # Private Methods #
    ###################
    def _check_affiliation_eligibility(self, user: MCommunityUser) -> CheckEligibilityResponse:
        """
        Given an MCommunity user, check if their affiliation(s), including sponsored affiliate type if applicable,
        denote that they should be eligible for this service.
        :param user: MCommunityUser object for the user
        :return: CheckEligibilityResponse object containing eligibility information
        """
        user.populate_highest_affiliation()
        sa_type = user.check_sponsorship_type()
        if sa_type:  # This person is a sponsored affiliate type 1, 2, or 3
            if sa_type in self.eligible_sa_types:
                eligible = True
                reason = f'Sponsored affiliates t{sa_type} are eligible for {self.service_friendly}'
            else:
                eligible = False
                reason = f'Sponsored affiliates t{sa_type} are not eligible for {self.service_friendly}'
        elif user.highest_affiliation in self.eligible_affiliations_minus_sa:
            eligible = True
            reason = f'{user.highest_affiliation} are eligible for {self.service_friendly}'
        else:  # Neither sponsored affiliate type nor highest affiliation are in the eligible affiliations for service
            eligible = False
            reason = f'{user.highest_affiliation} are not eligible for {self.service_friendly}'
        return CheckEligibilityResponse(eligible=eligible, reason=reason, user=user, errors=None)

    def _validate(self) -> None:
        """
        Validate the class attributes.
        :return: Nothing
        """
        if 'collab-iam-admins' not in self.override_groups:
            raise RuntimeError(f'collab-iam-admins is missing from the override_groups: {self.override_groups}')
        if self.eligible_affiliations_minus_sa:
            if 'SponsoredAffiliate' in self.eligible_affiliations_minus_sa:
                raise RuntimeError(f'SponsoredAffiliate cannot be in eligible_affiliations_minus_sa. Eligible '
                                   f'SponsoredAffiliate type numbers go in eligible_sa_types')
            elif len(self.eligible_affiliations_minus_sa) < 4:
                warn(f'eligible_affiliations_minus_sa is unusually short: {self.eligible_affiliations_minus_sa}. '
                     f'Faculty, RegularStaff, Students, and TemporaryStaff are eligible for almost every service; are '
                     f'you sure?')
            for i in self.eligible_affiliations_minus_sa:
                if i not in ['Faculty', 'RegularStaff', 'Student', 'TemporaryStaff', 'Alumni', 'Retiree']:
                    raise RuntimeError(f'eligible_affiliations_minus_sa contains an unfamiliar affiliation {i} (should '
                                       f'be one of Faculty, RegularStaff, Student, TemporaryStaff, Alumni, Retiree')
        else:
            raise RuntimeError(f'eligible_affiliations_minus_sa cannot be empty: {self.eligible_affiliations_minus_sa}')
        if self.eligible_sa_types:
            for i in self.eligible_sa_types:
                if i not in range(1, 4):
                    raise RuntimeError(f'eligible_sa_types contains an invalid entry {i} (must be 1, 2, and/or 3)')
        else:
            warn('eligible_sa_types is empty. Are you sure that no sponsored affiliates are eligible?')

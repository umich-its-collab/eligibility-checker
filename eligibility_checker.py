import logging
from abc import ABC, abstractmethod
from typing import Union

from mcommunity.mcommunity_user import MCommunityUser
from mcommunity.mcommunity_group import MCommunityGroup

logger = logging.getLogger(__name__)


class EligibilityChecker(ABC):
    service_friendly: str  # Name of the service in Capital Case (ex: Google, Microsoft Teams, Slack)
    service_entitlement: Union[str, None] = 'enterprise'  # umichServiceEntitlement (uSE) to reference
    # service_entitlement should be None if this service_entitlement doesn't rely on uSE and only on affiliations

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
                self.override_group_members += MCommunityGroup(
                    group, self.mcommunity_app_cn, self.mcommunity_secret).members
        self._validate()

    ##################
    # Public Methods #
    ##################
    def check_eligibility(self, uniqname: str, validate_affiliation: bool = True) -> bool:
        """
        Check whether a given user is eligible for the service based on uSE if self.service_entitlement is set, else by
        affiliations only
        :param uniqname: the U-M username of the user to check for eligibility (i.e. before @umich.edu in their email)
        :param validate_affiliation: validate that the uSE seems aligned with the user's affiliation
        (use prior to destructive actions in case of bugs in uSE); no effect if self.service_entitlement is None
        :return: boolean for whether or not they are eligible
        """
        if uniqname in self.override_group_members:
            logger.info(f'{uniqname} is eligible because they are in an override group.')
            return True
        else:
            try:
                user = MCommunityUser(uniqname, self.mcommunity_app_cn, self.mcommunity_secret)
            except NameError:  # The MCommunity user doesn't exist, therefore is ineligible
                return False
            if self.service_entitlement:  # This services relies on uSE for eligibility
                eligible = user.check_service_entitlement(self.service_entitlement)
                logger.info(f'{self.service_entitlement} entitlement for {uniqname} is {eligible}.')
                if validate_affiliation:
                    eligible_affiliations = self._check_affiliation_eligibility(user)
                    if not eligible and eligible_affiliations:
                        raise RuntimeError(
                            f'Highest affiliation {user.highest_affiliation} shows {user.name} should have a valid '
                            f'{self.service_entitlement} entitlement but they do not.\n EntityID: {user.entityid}\n'
                            f'Service Entitlements: \n{user.service_entitlements}\n Affiliations: \n{user.affiliations}'
                        )
                    else:
                        logger.info(
                            f'{self.service_entitlement} service entitlement ({eligible}) and affiliations '
                            f'{user.highest_affiliation} validated for {user.name}.'
                        )
                        return eligible
                else:
                    return eligible
            else:  # This service does not rely on uSE for eligibility
                return self._check_affiliation_eligibility(user)  # No further validation necessary or possible

    def deprovision_account_if_ineligible(self, uniqname) -> bool:
        """
        Check eligibility and deprovision account if ineligible.
        :param uniqname: the U-M username of the user to check for eligibility (i.e. before @umich.edu in their email)
        :return: True if deprovisioned, False if not
        """
        try:
            eligible = self.check_eligibility(uniqname)
        except RuntimeError as e:
            logger.exception(f'LDAP data error for {uniqname}: ', exc_info=e)
            return False  # We won't deprovision them if they have a data issue
        if eligible:
            return False
        else:
            self._deprovision(uniqname)

    ###################
    # Private Methods #
    ###################
    def _check_affiliation_eligibility(self, user: MCommunityUser) -> bool:
        """
        Given an MCommunity user, check if their affiliation(s), including sponsored affiliate type if applicable,
        denote that they should be eligible for this service.
        :param user: MCommunityUser object for the user
        :return: bool True if eligible based on affiliations, False if not
        """
        user.populate_highest_affiliation()
        sa_type = user.check_sponsorship_type()
        if sa_type:  # This person is a sponsored affiliate type 1, 2, or 3
            if sa_type in self.eligible_sa_types:
                logger.info(
                    f'{user.name} ELIGIBLE: sponsored affiliates t{sa_type} are eligible for {self.service_friendly}.'
                )
                return True
            else:
                logger.info(
                    f'{user.name} NOT ELIGIBLE: sponsored affiliates t{sa_type} are not eligible for '
                    f'{self.service_friendly}.'
                )
                return False
        elif user.highest_affiliation in self.eligible_affiliations_minus_sa:
            logger.info(
                f'{user.name} ELIGIBLE: {user.highest_affiliation} are eligible for {self.service_friendly}.'
            )
            return True
        else:  # Neither sponsored affiliate type nor highest affiliation are in the eligible affiliations for service
            logger.info(
                f'{user.name} NOT ELIGIBLE: {user.highest_affiliation} are not eligible for {self.service_friendly}.'
            )
            return False

    @abstractmethod
    def _deprovision(self, uniqname) -> bool:
        """
        Deprovision the account in the service_entitlement for this user.
        :param uniqname: the U-M username of the user to check for eligibility (i.e. before @umich.edu in their email)
        :return: bool for whether deprovision was successful
        """
        pass

    def _validate(self) -> None:
        """
        Validate the class attributes.
        :return:
        """
        if 'collab-iam-admins' not in self.override_groups:
            raise RuntimeError(f'collab-iam-admins is missing from the override_groups: {self.override_groups}')
        if self.eligible_affiliations_minus_sa:
            if 'SponsoredAffiliate' in self.eligible_affiliations_minus_sa:
                raise RuntimeError(f'SponsoredAffiliate cannot be in eligible_affiliations_minus_sa. Eligible '
                                   f'SponsoredAffiliate type numbers go in eligible_sa_types')
            elif len(self.eligible_affiliations_minus_sa) < 4:
                raise UserWarning(f'eligible_affiliations_minus_sa is unusually short. Faculty, RegularStaff, '
                                  f'Students, and TemporaryStaff are eligible for almost every service; are you sure?')
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
            raise UserWarning('eligible_sa_types is empty. Are you sure that no sponsored affiliates are eligible?')

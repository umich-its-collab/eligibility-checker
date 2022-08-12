import json
import logging
import re

from mcommunity.mcommunity_base import MCommunityBase

logger = logging.getLogger(__name__)


class MCommunityUser(MCommunityBase):
    email: str = ''
    exists: bool = False
    entityid: str = ''  # a.k.a. UMID
    display_name: str = ''  # Display name, a.k.a. preferred name
    affiliations: list = []  # Populate via populate_affiliations
    highest_affiliation: str = ''  # Populate via populate_highest_affiliation
    service_entitlements: list = []  # Populate via populate_service_entitlements

    search_base: str = 'ou=People,dc=umich,dc=edu'
    ldap_attributes: list = [
        '*', 'umichServiceEntitlement', 'entityid', 'umichDisplaySN', 'umichNameOfRecord', 'displayName'
    ]

    def __init__(self, uniqname: str, mcommunity_app_cn, mcommunity_secret):
        super().__init__(mcommunity_app_cn, mcommunity_secret)
        self.name: str = uniqname
        self.query_object: str = f'uid={uniqname}'
        self.email: str = self.name + '@umich.edu'

        self.raw_result = self.search(self.search_base, self.query_object, self.ldap_attributes)

        if not self.raw_result:
            raise NameError(f'No user found in MCommunity for {self.name}.')
        else:
            self.exists = True
            self.entityid = self._decode('entityid')
            self.display_name = self._decode('displayName')

    ##################
    # Public Methods #
    ##################
    def check_service_entitlement(self, service: str = 'enterprise') -> bool:
        """
        Check whether the user is eligible for a service based on uSE; note that this does NOT take into account the
        override groups, and should be used in conjunction with override group checking at the EligibilityChecker level
        :param service: the uSE to look for in the service_entitlement list
        :return: boolean for whether or not they are eligible
        """
        eligible = False
        self.populate_service_entitlements()
        for i in self.service_entitlements:
            r = json.loads(i)
            if r.get('system') == service:
                if r.get('eligibility') in ['yes', 'yesDelay', 'yesImmed']:
                    eligible = True
                    break
        return eligible

    def check_sponsorship_type(self) -> int:
        """
        Check if sponsored affiliate is the highest role for a user; if yes, return the type of the sponsorship (1, 2,
        or 3). If not, return 0.
        :return: int representing the sponsorship type (or 0 if sponsored affiliate is not the highest role)
        """
        if not self.highest_affiliation:
            self.populate_highest_affiliation()
        if self.highest_affiliation == 'SponsoredAffiliate':
            if re.match('^um[0-9]+', self.name):
                return 3
            elif re.match('^99', self.entityid):
                return 2
            else:
                return 1
        else:
            return 0

    def populate_affiliations(self) -> None:
        """
        Populate the affiliations attribute from raw_result if it has not already been done.
        :return: None
        """
        if not self.affiliations:  # Don't overwrite if the list is not empty; it likely was already populated
            self.affiliations = self._decode('umichInstRoles', return_str_if_single_item_list=False)

    def populate_highest_affiliation(self) -> None:
        """
        Find the highest-level affiliation for the user. Levels in descending order: Faculty, RegularStaff, Student,
        TemporaryStaff, SponsoredAffiliate, Retiree, Alumni. Store it on the highest_affiliation attribute.
        :return: None
        """
        self.populate_affiliations()  # Just to make sure; it won't run again if it was already done
        role = ' '.join(self.affiliations)
        if 'Faculty' in role:
            self.highest_affiliation = 'Faculty'
        elif 'RegularStaff' in role:
            self.highest_affiliation = 'RegularStaff'
        elif 'Student' in role:
            self.highest_affiliation = 'Student'
        elif 'TemporaryStaff' in role:
            self.highest_affiliation = 'TemporaryStaff'
        elif 'SponsoredAffiliate' in role:
            self.highest_affiliation = 'SponsoredAffiliate'
        elif 'Retiree' in role:
            self.highest_affiliation = 'Retiree'
        elif 'Alumni' in role:
            self.highest_affiliation = 'Alumni'
        else:
            self.highest_affiliation = 'NA'

    def populate_service_entitlements(self) -> None:
        """
        Populate the service_entitlement entitlements attribute from raw_result if it has not already been done.
        :return: None
        """
        if not self.service_entitlements:  # Don't overwrite if the list is not empty; it likely was already populated
            self.service_entitlements = self._decode('umichServiceEntitlement', return_str_if_single_item_list=False)

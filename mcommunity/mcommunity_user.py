import json
import logging
import re
from typing import Union

import ldap

from mcommunity.mcommunity_base import ldap_connect

logger = logging.getLogger(__name__)


class MCommunityUser:
    dn: str = ''
    email: str = ''
    exists: bool = False
    entityid: str = ''  # a.k.a. UMID
    name: str = ''  # Display name, a.k.a. preferred name
    affiliations: list = []  # Populate via populate_affiliations
    highest_affiliation: str = ''  # Populate via populate_highest_affiliation
    service_entitlements: list = []  # Populate via populate_service_entitlements

    raw_user: list = []
    
    mcommunity_app_cn: str = ''
    mcommunity_secret: str = ''
    ldap_attributes: list = [
        '*', 'umichServiceEntitlement', 'entityid', 'umichDisplaySN', 'umichNameOfRecord', 'displayName'
    ]

    def __init__(self, uniqname: str, mcommunity_app_cn, mcommunity_secret):
        self.dn: str = uniqname
        self.email: str = self.dn + '@umich.edu'
        self.mcommunity_app_cn = mcommunity_app_cn
        self.mcommunity_secret = mcommunity_secret

        self.raw_user = self._populate_user_data(self.dn)

        if not self.raw_user:
            raise NameError(f'No user found in MCommunity for {self.dn}.')
        else:
            self.exists = True
            self.entityid = self._decode('entityid')
            self.name = self._decode('displayName')

    ##################
    # Public Methods #
    ##################
    def check_service_entitlement(self, service: str = 'enterprise') -> bool:
        """
        Check whether the user is eligible for a service based on service entitlement; note that this does NOT take
        into account the override groups, and should be used in conjunction with override group checking
        :param service: the service to look for in the service eligibility list
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
            if re.match('^um\d+', self.dn):
                return 3
            elif re.match('^99', self.entityid):
                return 2
            else:
                return 1
        else:
            return 0

    def populate_affiliations(self) -> None:
        """
        Populate the affiliations attribute from raw_user if it has not already been done.
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
        Populate the service entitlements attribute from raw_user if it has not already been done.
        :return: None
        """
        if not self.service_entitlements:  # Don't overwrite if the list is not empty; it likely was already populated
            self.service_entitlements = self._decode('umichServiceEntitlement', return_str_if_single_item_list=False)

    ###################
    # Private Methods #
    ###################
    def _populate_user_data(self, dn) -> list:
        """
        Called during init to get the user's data from LDAP (MCommunity) so it can be stored on self.raw_user
        :param dn: the user's uniqname
        :return: list of user data
        """
        return ldap_connect(
            self.mcommunity_app_cn,
            self.mcommunity_secret
        ).search_st('ou=People,dc=umich,dc=edu',
                    ldap.SCOPE_SUBTREE,
                    f'uid={dn}',
                    self.ldap_attributes
                    )

    def _decode(self, which_key, return_str_if_single_item_list=True) -> Union[str, list]:
        """
        Decode a bytes object or a list of bytes objects to UTF-8
        :param which_key: a string representing the key to retrieve the value of in the user data
        :param return_str_if_single_item_list: if True and the decoded item is a single-item list, return the item
        instead of the list; if False, return the list with the single item; defaults to True;
        :return: the decoded item, either a string or a list
        """
        try:
            value = self.raw_user[0][1].get(which_key, '')
        except IndexError:  # This will happen if the person doesn't exist or is not affiliated
            return ''
        if type(value) == bytes:  # Never seen this in LDAP, it is always a list even if just one item, but just in case
            return value.decode('UTF-8')
        elif type(value) == list:
            decoded = [i.decode('UTF-8') for i in value]
            if return_str_if_single_item_list and len(decoded) == 1:
                return decoded[0]
            else:
                return decoded

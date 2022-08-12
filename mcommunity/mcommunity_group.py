import logging

import ldap

from mcommunity.mcommunity_base import MCommunityBase
from mcommunity.mcommunity_user import MCommunityUser

logger = logging.getLogger(__name__)


class MCommunityGroup(MCommunityBase):
    cn: str = ''
    exists: bool = False
    members: list = []
    members_mcomm_users: list = []

    search_base: str = 'ou=User Groups,ou=Groups,dc=umich,dc=edu'

    def __init__(self, cn: str, mcommunity_app_cn: str, mcommunity_secret: str):
        """
        Get data about an M-Community group via LDAP.
        :param cn: the cname of the M-Community group (this is the NAME, not the email!)
        e.g. "ITS Collaboration Services Core Team", not "its-collab-core"
        :return: None
        """
        super().__init__(mcommunity_app_cn, mcommunity_secret)
        self.name: str = cn
        self.query_object: str = f'cn={self.name}'

        self.raw_result = self.search(self.search_base, self.query_object, self.ldap_attributes)

        if not self.raw_result:
            raise NameError(f'MCommunity group {self.name} does not exist.')
        else:
            self.exists = True
            if not self.members:
                for i in self.raw_result[0][1].get('member', []):
                    self.members.append(ldap.dn.explode_dn(i, flags=ldap.DN_FORMAT_LDAPV2)[0].split('uid=')[1])

    def populate_members_mcomm_users(self) -> list:
        """
        Add all members of the group to self.members_mcomm_users as MCommunityUser objects.
        :return: list of MCommunityUsers (self.members.mcomm_users)
        """
        if not self.members_mcomm_users:  # Don't overwrite if it has already been populated
            self.members_mcomm_users = [MCommunityUser(
                uniqname, self.mcommunity_app_cn, self.mcommunity_secret) for uniqname in self.members]
        return self.members_mcomm_users

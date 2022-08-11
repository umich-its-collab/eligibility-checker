import logging

import ldap

from mcommunity.mcommunity_base import ldap_connect
from mcommunity.mcommunity_user import MCommunityUser

logger = logging.getLogger(__name__)


class MCommunityGroup:
    cn: str = ''
    exists: bool = False
    members: list = []
    members_mcomm_users: list = []

    raw_group: list = []

    mcommunity_app_cn: str = ''
    mcommunity_secret: str = ''

    def __init__(self, cn: str, mcommunity_app_cn: str, mcommunity_secret: str):
        """
        Get data about an M-Community group via LDAP.
        :param cn: the cname of the M-Community group (this is the NAME, not the email!)
        e.g. "ITS Collaboration Services Core Team", not "its-collab-core"
        :return: None
        """
        self.cn: str = cn
        self.mcommunity_app_cn = mcommunity_app_cn
        self.mcommunity_secret = mcommunity_secret

        self.raw_group = self._populate_group_data(cn)

        if not self.raw_group:
            raise NameError(f'MCommunity group {cn} does not exist.')
        else:
            self.exists = True
            for i in self.raw_group[0][1].get('member', []):
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

    ###################
    # Private Methods #
    ###################
    def _populate_group_data(self, cn) -> list:
        """
        Called during init to get the group's data from LDAP (MCommunity) so it can be stored on self.raw_group
        :param cn: the group's cname (name, not email)
        :return: list of group data
        """
        return ldap_connect(
            self.mcommunity_app_cn,
            self.mcommunity_secret
        ).search_st('ou=User Groups,ou=Groups,dc=umich,dc=edu',
                    ldap.SCOPE_SUBTREE,
                    f'cn={cn}',
                    ['*']
                    )

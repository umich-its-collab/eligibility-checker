from time import sleep
from typing import Union

import ldap


class MCommunityBase:
    mcommunity_app_cn: str = ''
    mcommunity_secret: str = ''

    search_base: str = ''  # LDAP base to query
    ldap_attributes: list = ['*']  # Attributes to query for

    name: str = ''  # Usually a person dn or a group cn
    query_object: str = ''  # The name with the added info required for submitting an LDAP query
    raw_result: list = []  # Exactly what is returned from the query

    def __init__(self, mcommunity_app_cn: str, mcommunity_secret: str):
        """
        Base class to use for connecting to LDAP (MCommunity).
        :param mcommunity_app_cn: cname of the MCommunity app that the secret is tied to (ex: ITS-Dropbox-McDirApp001)
        :param mcommunity_secret: secret/password for that app to connect to LDAP
        """
        self.mcommunity_app_cn = mcommunity_app_cn
        self.mcommunity_secret = mcommunity_secret

    ##################
    # Public Methods #
    ##################
    def connect(self):
        """
        Get a connection to M-Community for use in querying via LDAP.
        :return: the connection
        """
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        connect = ldap.initialize('ldaps://ldap.umich.edu')
        connect.set_option(ldap.OPT_TIMEOUT, 60)
        connect.set_option(ldap.OPT_NETWORK_TIMEOUT, 60)
        ldap.OPT_SIZELIMIT = 100
        connect.set_option(ldap.OPT_REFERRALS, 0)
        # Request new ID
        connect.simple_bind_s(f'cn={self.mcommunity_app_cn},ou=Applications,o=services', self.mcommunity_secret)
        return connect

    def search(self, search_base, query_object, ldap_attributes):
        """
        Perform a basic search for a single object (user or group)
        :return: query result
        """
        for i in range(1, 4):
            try:
                return self.connect().search_st(search_base,
                                                ldap.SCOPE_SUBTREE,
                                                query_object,
                                                ldap_attributes
                                                )
            except (ldap.SERVER_DOWN, ldap.UNAVAILABLE):
                sleep(i * 5)  # Sleep longer each subsequent time if the last attempt was unsuccessful
                continue
        raise ldap.UNAVAILABLE  # If we get here, it failed 3 times and we just need to accept defeat and move on

    ###################
    # Private Methods #
    ###################
    def _decode(self, which_key, return_str_if_single_item_list=True) -> Union[str, list]:
        """
        Decode a bytes object or a list of bytes objects to UTF-8
        :param which_key: a string representing the key to retrieve the value of in the user data
        :param return_str_if_single_item_list: if True and the decoded item is a single-item list, return the item
        instead of the list; if False, return the list with the single item; defaults to True;
        :return: the decoded item, either a string or a list
        """
        try:
            value = self.raw_result[0][1].get(which_key, '')
        except IndexError:  # This will happen if the person/group doesn't exist or is not affiliated
            return ''
        if type(value) == bytes:  # Never seen this in LDAP, it is always a list even if just one item, but just in case
            return value.decode('UTF-8')
        elif type(value) == list:
            decoded = [i.decode('UTF-8') for i in value]
            if return_str_if_single_item_list and len(decoded) == 1:
                return decoded[0]
            else:
                return decoded

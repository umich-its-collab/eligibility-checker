import ldap


def ldap_connect(mcommunity_app_cn: str, mcommunity_secret: str) -> ldap.ldapobject.SimpleLDAPObject:
    """
    Get a connection to M-Community for use in querying via LDAP.
    :param mcommunity_app_cn: the cname of the M-Community app that the secret is tied to (ex: ITS-Dropbox-McDirApp001)
    :param mcommunity_secret: the secret/password for that app to connect to LDAP
    :return: the connection
    """
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
    connect = ldap.initialize('ldaps://ldap.umich.edu')
    connect.set_option(ldap.OPT_TIMEOUT, 60)
    connect.set_option(ldap.OPT_NETWORK_TIMEOUT, 60)
    ldap.OPT_SIZELIMIT = 100
    connect.set_option(ldap.OPT_REFERRALS, 0)
    # Request new ID
    connect.simple_bind_s(f'cn={mcommunity_app_cn},ou=Applications,o=services', mcommunity_secret)
    return connect

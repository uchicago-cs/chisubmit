# Needed so we can import from the global "ldap" package
from __future__ import absolute_import

import ldap
from ldap.filter import filter_format
from chisubmit.backend.webapp.auth import Auth

global conn

class LDAPAuth(Auth):
    
    def __init__(self, server, ldap_server_uri, base_dn):
        super(LDAPAuth, self).__init__(server)

        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        self.conn = ldap.initialize(ldap_server_uri)
        self.conn.protocol_version = ldap.VERSION3
        self.base_dn = base_dn
        self.server = server
        
    def check_auth(self, username, password):
        dn = self.__user_dn(username)
        try:
            self.conn.simple_bind_s(dn, password)
            return True
        except ldap.LDAPError:
            return False

    def __user_dn(self, uid):
        search_filter = filter_format("uid=%s", (uid,))
        return next(user[0]
                    for user in self.conn.search_s(self.base_dn,
                                              ldap.SCOPE_SUBTREE,
                                              search_filter, []))



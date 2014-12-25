import ldap
from chisubmit.backend.webapp.api import app
from ldap.filter import filter_format

global conn
ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
conn = ldap.initialize('ldaps://ldap.cs.uchicago.edu')
conn.protocol_version = ldap.VERSION3


def authenticate(username, password):
    dn = user_dn(username)
    app.logger.error("Authenticating username: %s dn: %s" % (username, dn))
    conn.simple_bind(dn, password)


def user_dn(uid):
    search_filter = filter_format("uid=%s", (uid,))
    return next(user[0]
                for user in conn.search_s('dc=uchicago,dc=edu',
                                          ldap.SCOPE_SUBTREE,
                                          search_filter, []))

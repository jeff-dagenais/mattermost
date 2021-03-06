#!/usr/bin/python
"""Set Mattermost admin user, password, email, and team name
Option:
    --pass=     unless provided, will ask interactively
    --email=    unless provided, will ask interactively
    --domain=   unless provided, will ask interactively
"""

import re
import sys
import getopt
import inithooks_cache

from dialog_wrapper import Dialog
from pgsqlconf import PostgreSQL
from executil import system
import bcrypt

def usage(s=None):
    if s:
        print >> sys.stderr, "Error:", s
    print >> sys.stderr, "Syntax: %s [options]" % sys.argv[0]
    print >> sys.stderr, __doc__
    sys.exit(1)

DEFAULT_DOMAIN="www.example.com"

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "h",
                                       ['help', 'pass=', 'email=', 'domain='])
    except getopt.GetoptError, e:
        usage(e)

    password = ""
    email = ""
    domain = ""

    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt == '--pass':
            password = val
        elif opt == '--email':
            email = val
        elif opt == '--domain':
            domain = val

    if not password:
        d = Dialog('TurnKey Linux - First boot configuration')
        password = d.get_password(
            "Mattermost Admin Password",
            "Enter new password for Mattermost 'admin' account.")

    if not email:
        if 'd' not in locals():
            d = Dialog('TurnKey Linux - First boot configuration')

        email = d.get_email(
            "Mattermost Administrator's Email",
            "Enter email address for Mattermost 'admin' account.",
            "admin@example.com")

    inithooks_cache.write('APP_EMAIL', email)

    if not domain:
        if 'd' not in locals():
            d = Dialog('TurnKey Linux - First boot configuration')
        domain = d.get_input(
                 "Mattermost domain",
                 "Enter domain to serve Mattermost",
                 DEFAULT_DOMAIN)

    if domain == "DEFAULT":
        domain = DEFAULT_DOMAIN

    inithooks_cache.write('APP_DOMAIN', domain)

    if not domain.startswith('https://') and not domain.startswith('http://'):
        domain = 'https://'+domain

    system('sed -i "/SiteURL/ s|\\":.*|\\": \\\"%s\\\",|" /opt/mattermost/config/config.json' % domain)

    salt = bcrypt.gensalt()
    hashpass = bcrypt.hashpw(password, salt)

    p = PostgreSQL(database='mattermost')
    p.execute('UPDATE users SET password=\'%s\', email=\'%s\' WHERE username=\'admin\';' % (hashpass, email))

if __name__ == "__main__":
    main()

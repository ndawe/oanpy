#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Print data related to all accounts.
"""

# oanda imports
from oanda import OAException, utils



def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip())
    utils.add_userpass(parser)
    opts, args = parser.parse_args()
    utils.check_userpass(parser, opts)
        
    print 'Logging in.'
    fxclient = opts.ClientClass()
    try:
        fxclient.login(opts.username, opts.password)
    except OAException, e:
        raise SystemExit("Could not login: %s" % e)

    user = fxclient.getUser()
    print user, user.profile
    for acc in user.getAccounts():
        print acc, acc.profile

    fxclient.logout()


if __name__ == '__main__':
    main()



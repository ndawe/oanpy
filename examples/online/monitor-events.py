#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Monitor account events and rate events.

This file also serves as a demo/test/program for the few different methods of
dispatching events:

- Blocking call;
- Using Twisted;
- Dispatching from a separate thread.

See implementation in oanda.dispatch for details. 
"""

# oanda imports
from oanda import *
from oanda import utils
from oanda.dispatch import *



class AccountEventsMonitor(AccountEvent):

    def __init__(self, account) :
        AccountEvent.__init__(self)
        self.account = account
        self.setTransient(False) # keeps active

    def handle(self, ei, _):
        assert ei.type == FXI_Type.FXIT_Account, ei.type
        print "AccountEvent:", self.account
        print "   ", ei.transaction
        print

class RateEventsMonitor(RateEvent):

    def __init__(self) :
        RateEvent.__init__(self)
        self.setTransient(False) # keeps active

    def handle(self, ei, _):
        assert ei.type == FXI_Type.FXIT_Rate, ei.type
        print "RateEvent:", ei.pair
        print "   ", ei.tick
        print





def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip())
    utils.add_userpass(parser)

    parser.add_option('-m', '--dispatch-method', metavar='METHOD',
                      action='store', type='choice',
                      choices=dispatching_methods.keys(), default='blocking',
                      help=("Selects method of dispatching events (%s)." %
                            ','.join(dispatching_methods.keys())))

    parser.add_option('-d', '--delay', action='store', type='int',
                      default=60,
                      help="Nb. of seconds to exit after monitoring.")

    opts, args = parser.parse_args()
    utils.check_userpass(parser, opts)

    fxclient = opts.ClientClass()
    fxclient.setWithRateThread(True)
    try:
        fxclient.login(opts.username, opts.password)
    except OAException, e:
        raise SystemExit("Could not login: %s" % e)

    # Monitor account events.
    user = fxclient.getUser()
    for acc in user.getAccounts():
        aev = AccountEventsMonitor(acc)
        acc.eventManager().add(aev)

    # Monitor a rates event.
    rev = RateEventsMonitor()
    user = fxclient.getUser()
    rt = fxclient.getRateTable()
    rt.eventManager().add(rev)

    # Dispatch events.
    dispatch_events = dispatching_methods[opts.dispatch_method]
    dispatch_events(opts.delay)

    # Cleanup and exit.
    print 'Logging out.'
    fxclient.logout()


if __name__ == '__main__':
    main()


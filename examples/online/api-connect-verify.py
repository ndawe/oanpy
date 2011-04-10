#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
A script to verify my connection to the OANDA API, as requested by OANDA:

    Your FXTrade account has been activated for API access. Please change your
    references to the FXGame class in your code to FXTrade to access this
    server.

    In order to verify that you are connecting properly, please have your API
    program execute several 1 unit trades on the FXTrade system. Send us the
    transaction logs that your program produces(including transaction ids for
    above trades), and we will verify that our records are consistent with
    yours.

    Kind regards,
    OANDA FXTrade API Team

Just send the output of this script to OANDA.
"""

# stdlib imports
import logging

# oanda imports
from oanda import *
from oanda import utils


class AccEvents(AccountEvent):

    def __init__(self):
        AccountEvent.__init__(self)
        self.events = []
    
    def handle(self, ei, __):
        self.events.append((ei.timestamp, str(ei.transaction)))


def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip())
    utils.add_userpass(parser)
    opts, args = parser.parse_args()
    utils.check_userpass(parser, opts)

    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)-8s: %(message)s')

    fxclient = opts.ClientClass()
    fxclient.setWithRateThread(True)
    fxclient.setWithKeepAliveThread(True)
    try:
        fxclient.login(opts.username, opts.password)
    except OAException, e:
        raise SystemExit("Could not login: %s" % e)

    user = fxclient.getUser()
    accounts = user.getAccounts()
    ## assert len(accounts) == 1
    acc = accounts[1]

    accevent = AccEvents()
    acc.eventManager().add(accevent)

    pairs = ('EUR/USD', 'USD/CAD', 'USD/JPY')
    ## pairs = ('EUR/USD',)
    for pair in pairs:
        order = MarketOrder()
        order.base, order.quote = pair.split('/')
        order.units = 1
        print
        print '-' * 80
        print 'Placing order:', order
        print 'Returned orders:'
        modtrades = acc.execute(order)
        for trade in modtrades:
            print
            print '  ', str(trade)
            
        while 1:
            fxevents_process_loop(1)
            if accevent.events:
                ts, txn = accevent.events.pop()
                print
                print 'AccountEventInfo:'
                print '  timestamp:', ts
                print '  transaction:', txn
                break
    
    fxclient.logout()


if __name__ == '__main__':
    main()


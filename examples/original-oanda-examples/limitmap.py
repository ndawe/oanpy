#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
* A simple program which uses the event model to match triggered limit orders
* to the market orders they created.

(Adapted from OANDA's example program with the corresponding name.)
"""

from time import sleep
from oanda import *


EUR_USD = Pair("EUR/USD")

# Simple class which stores a pair of integers

class LimitMatcher(AccountEvent):

    def __init__(self):
		AccountEvent.__init__()
		self.mapping = [] # vector<MapPair>
		self.unmapped = [] # stack<int>

    def match(self, ei):
        desc = ei.transaction.getDescription()
        print " (%s)" % (ei.transaction, desc)
        return desc in ("Sell Order Filled", "Buy Order Filled", "Order Fulfilled")

    def handle(self, ei, em):
        desc = ei.transaction.getDescription()
        if desc == "Order Fulfilled":
            while self.unmapped:
                pair = (ei.transaction.link, self.unmapped.pop())
                self.mapping.append(pair)
        else:
            self.unmapped.append(ei.transaction.transactionNumber())

	def printReport(self):
            print "Printing report"
            self.mapping.sort()
            for map_itr in self.mapping:
                print "Limit order #%s spawned market order #%s" % map_itr


def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip())
    opts, args = parser.parse_args()

    if len(args) != 2:
        parser.error("<username> <password>")

    fxclient = FXGame()
    fxclient.setWithKeepAliveThread(True)
    print "Logging in...",
    fxclient.login(*args)
    print "done!"
    user = fxclient.getUser()
    account = user.getAccounts()[0]

    print "Registering limit mapper event...",
    lm = LimitMatcher()
    account.eventManager().add(lm)
    print "done!"

    ## print "Four minutes left"
    ## sleep(60)
    ## print "Three minutes left"
    ## sleep(60)
    ## print "Two minutes left"
    ## sleep(60)
    print "One minute left"
    sleep(60)
    print "Time's up!"
    lm.printReport()

    fxclient.logout()
    print "Logging out"


if __name__ == '__main__':
    main()


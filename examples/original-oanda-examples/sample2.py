#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
(Adapted from OANDA's example program with the corresponding name.)
"""

from time import sleep
from oanda import *

def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip())
    opts, args = parser.parse_args()

    if len(args) != 3:
        parser.error("<username> <password> <withRateThread>")
    username, password, withthrd = args

    while 1:
        try:
            fxgame.login(username, password)
        except OAException, e:
            print "sample2: caught exception type=" << e.type
            print "sample2: unable to connect, retrying...."
            sleep(5)
            continue
        break

	me = fxgame.getUser()
	rt = fxgame.getRateTable()

        for i in xrange(5):
            eurusd = rt.getRate("EUR/USD")
            eurjpy = rt.getRate("EUR/JPY")
            print "EUR/USD ", eurusd
            print "EUR/JPY ", eurjpy
            sleep(5)

	accounts = me.getAccounts()
	myaccount = accounts[0]
	mytrades = myaccount.getTrades()

	print "balance is ", myaccount.balance(), " on acct "
	print myaccount.accountId()
	print "margin used is ", myaccount.marginUsed()
	print "margin available is ", myaccount.marginAvailable()
	
	print "***** my trades begin *****"
        for trade in mytres:
            print trade
	print "***** my trades end *****"

	myorders = myaccount.getOrders()
	print "***** my orders begin *****"
        for order in myorders:
            print order
	print "***** my orders end *****"

	fxgame.logout()


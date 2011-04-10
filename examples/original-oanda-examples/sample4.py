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

    fxgame = FXGame()
    while 1:
        try:
            fxgame.login(username, password)
        except OAException, e:
            print "sample4: caught exception type=" << e.type
            print "sample4: unable to connect, retrying...."
            sleep(5)
            continue
        break

	me = fxgame.getUser()
	print "sample4::have user"
	accounts = me.getAccounts()	
	print "sample4::have accounts"

	myaccount = accounts[0]
	assert myaccount

	# Make a trade

        while 1:
            neworder = MarketOrder()
            neworder.units = 100
            neworder.base = "GBP"
            neworder.quote = "CHF"
            neworder.lowPriceLimit = 0.324897
            neworder.highPriceLimit = 1000.328974
            neworder.stopLossOrder.price = 0.1029
            print "sample4::built 100 gbp/chf market order"

            try:
                newtrades = myaccount.execute(neworder)
                print "sample4::executed 100 gbp/chf market order"
            except OAException, e:
                print e.type
                print "Caught an exception!!"

            print " *** my new trades begin ***"
            for t in newtrades:
                print t
            print " *** my new trades end ***"


            sleep(4)


            neworder = MarketOrder()
            neworder.units = -100
            neworder.base = "GBP"
            neworder.quote = "CHF"
            neworder.lowPriceLimit = 0.23984723
            neworder.highPriceLimit = 1000.324897

            print "sample4::built -100 gbp/chf market order"
            try:
                newtrades = myaccount.execute(neworder)
                print "sample4::executed -100 gbp/chf market order"
            except OAException, e:
                print "Caught an exception!!"

            print " *** my new trades begin ***"
            for t in newtrades:
                print t
            print " *** my new trades end ***"


            sleep(4)

            try:
                trades = myaccount.getTrades()
            except OAException, e:
                print "Caught an exception!!"

            print " *** my trades begin ***"
            for trade in trades:
                print trade
            print " *** my trades end ***"

	fxgame.logout()
	sleep(1)


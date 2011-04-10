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
            print "sample3: caught exception type=" << e.type
            print "sample3: unable to connect, retrying...."
            sleep(5)
            continue
        break

	print "sample3:: getting user"
	me = fxgame.getUser()
	print "sample3:: getting accounts"
	accounts = me.getAccounts()	

	myaccount = accounts[0]
	assert myaccount

	print "sample3:: getting trades"
	mytrades = myaccount.getTrades()
	closedorder = MarketOrder()

	print "sample3:: closing trades"

        for trade in mytrades:
            try:
                closedorder = myaccount.close(trade)
                print "CLOSING: " << trade.ticketNumber << "   AT PRICE: " << closedorder.price
            except OAException, e:
                pass

	fxgame.logout()



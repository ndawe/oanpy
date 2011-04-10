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

    print "logged in"

    me = fxgame.getUser()
    rt = fxgame.getRateTable()

    rt.getRate("EUR/USD")

    accounts = me.getAccounts()
    myaccount = accounts[0]

    mypair = Pair("EUR/JPY")	
    interval = 5000L # 5S graph
    # interval = 60000L # 1M graph
    numTicks = 4

    print "getting first history"
    dynamic_history_old = rt.getHistory(mypair, interval, numTicks)
    print "sleeping"
    sleep(numTicks*(interval/1000L))
    print "getting second history"
    dynamic_history = rt.getHistory(mypair, interval, numTicks)

    # dump the history
    print mypair, " history"


    for h in dynamic_history_old:
            print "oh:", h
    print "should match up here"
    for h in dynamic_history:
            print "oh:", h

    fxgame.logout()


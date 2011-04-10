#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
(Adapted from OANDA's example program with the corresponding name.)
"""

from time import time, sleep
from oanda import *


def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip())
    opts, args = parser.parse_args()

    if len(args) != 3:
        parser.error("<username> <password> <withRateThread>")
    username, password, withthrd = args

    count = 0

    while 1:
        fxgame = FXGame()
        if withthread == 'thread':
            fxgame.setWithRateThread(True) # default is false
            print "creating rate thread"

        try:
            fxgame.timeout(10)
            fxgame.login(username, password)
        except OAException, e:
            print "caught an Exception type: %s  code:" % (e.type, e.code)
        except Exception:
            print "caught an exception"

        print "sample1::login successful"
        me = fxgame.getUser();
        accounts = me.getAccounts()
        myaccount = accounts[0]
        print "sample1::have account"

        ## PLACE A MARKET ORDER
        nowtime = time.time()
        neworder = LimitOrder()
        neworder.units = 1
        neworder.base = "USD" # GBP
        neworder.quote = "SAR" # CHF
        neworder.price = 5.1029
        neworder.duration = nowtime + 3800
        print "sample1::order built" 

        try:
            myaccount.execute(neworder)
            print "sample1::order executed"
        except OAException, e:
            print "Caught an exception!!" 

        fxgame.logout()
        print "sample1::logout" 
        count += 1

        if count%4 ==0:
            sleep(440)
        else:
            sleep(40)

    print "sample1::returning" 

if __name__ == '__main__':
    main()

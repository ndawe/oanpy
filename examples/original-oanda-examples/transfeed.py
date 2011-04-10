#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
(Adapted from OANDA's example program with the corresponding name.)
"""

from time import sleep
from oanda import *


class MyEvent(AccountEvent):

    def __init__(self, fxclient) :
        AccountEvent.__init__(self, "Buy Market")
        self.begin_time = fxclient.getServerTime()
        self.setTransient(False) # keeps active

    def match(self, ei):
        trace('match', ei)
        if ei.type != FXI_Type.FXIT_Account:
            return False
        return ei.transaction.timestamp >= self.begin_time

    def handle(self, ei, _):
        trace('handle', ei)
        # just print some output
        if ei.type != FXI_Type.FXIT_Account:
            print "throwing an exception"
            raise Exception()
        print "MyEvent::handle()", ei.transaction


def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip())
    opts, args = parser.parse_args()

    if len(args) != 3:
        parser.error("<username> <password> <withRateThread>")
    username, password, withthrd = args

    fxgame = FXGame()
    fxgame.setWithRateThread(withthrd == 'thread')

    while 1:
        try:
            fxgame.login(username, password)
        except OAException, e:
            print "transfeed: caught exception type=" << e.type
            print "transfeed: unable to connect, retrying...."
            sleep(5)
            continue
        break

    myevent = MyEvent(fxgame)
    user = fxgame.getUser()
    myaccount = user.getAccounts()[0]

    myaccount.eventManager().add(myevent)

    ## sleep(200)
    processFXEvents()

    fxgame.logout()


if __name__ == '__main__':
    main()


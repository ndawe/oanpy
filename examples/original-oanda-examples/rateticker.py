#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""

        Simple file to get ticks, and make sure they are
        serviced in monotonically nondecreasing order

 * Test program to print out rates as they are received, and then to print out
 * rates for EUR/USD again, because we love it so.

(Adapted from OANDA's example program with the corresponding name.)
"""

from time import sleep
from oanda import *


class RateTicker(RateEvent):

    def __init__(self, p): 
        RateEvent.__init__(self)
        self.pair = p
        self.transient = False

    def match(self, ei):
        return (self._pair is None) or (ei.pair == self.pair)

    def handle(self, ei, em):
        print ei.pair, ":", ei.tick


def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip())
    opts, args = parser.parse_args()

    if len(args) != 2:
        parser.error("<username> <password>")

    fxclient = FXClient()
    fxclient.setWithRateThread(True)
    print "Logging in...",
    fxclient.login(*args)
    ratetable = fxclient.getRateTable()

    print "done.  Registering event listeners...,"
    EUR_USD = Pair("EUR/USD")
    rt = RateTicker(EUR_USD)
    ratetable.eventManager().add(rt)
    rt2 = RateTicker(None)
    ratetable.eventManager().add(rt2)

    print "done."
    sleep(300)

    fxclient.logout()

        
if __name__ == '__main__':
    main()



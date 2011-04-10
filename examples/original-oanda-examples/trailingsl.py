#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
(Adapted from OANDA's example program with the corresponding name.)
"""

from time import sleep
from oanda import *


class TSLEvent(RateEvent):
    def __init__(self, p) :
        RateEvent.__init__(self, p)
        self.transient = False # keeps active

        self.account = None
        self.market = None
        self.delta = 0
        self.error = 0
        self.isbuy = False
        self.sl = 0

    def setWatch(self, acc, market, delta):
	self.account = acc
	self.market = market
	self.delta = delta
	self.isbuy = market.units > 0
	self.sl = market.stopLossOrder.price

    def match(self, ei):
        print "TSLEvent::match"
        if ei.type != FXI_Type.FXIT_Rate:
            print "should be throwing an exception"
            return False

        if not match_pair(ei):
            return False
        self.error = ei.tick.ask/200000
        if self.isbuy:
            cond = ei.tick.ask - self.delta - self.error > self.sl
        else:
            cond = ei.tick.bid + self.delta + self.error < self.sl
        print "tick ",
        print " time ", ei.tick.timestamp,
        print " ask ", ei.tick.ask,
        print " bid ", ei.tick.bid,
        print " matches... ", cond
        return cond


    def handle(self, ei, fxem):
        print "TSLEvent::handle\n"
        nmarket = MarketOrder()
        if self.isbuy:
            cond = ei.tick.ask - self.delta - self.error > self.sl 
        else:
            cond = ei.tick.bid + self.delta + self.error < self.sl
        if not cond: # captures repeated ticks
            return
        succ = self.account.getTradeWithId(nmarket, self.market.ticketNumber)
        if not succ:
            fxem.remove(self)
            print "dequeing event, market order no longer exists"
        else:
            print "modifying ticket ", nmarket.ticketNumber,
            print " old sl ", self.sl,
            if self.isbuy:
                self.sl = ei.tick.ask - self.delta 
            else:
                self.sl = ei.tick.bid + self.delta
            print " new sl ", self.sl
            nmarket.stopLossOrder.price(self.sl)
            self.account.modify(nmarket)


class SLEvent(AccountEvent):

    def __init__(self, tlink, event, rates) :
        AccountEvent.__init__(self, "Stop Loss")

        self.tlink = tlink
        self.event = event
        self.rates = rates
        print "watching sl on ticket ", tlink, endl
        self.transient = True

    def match(self, ei):
        print " checking ", ei.transaction
        res = match_transaction_type(ei) and \
              (ei.transaction.link == self.tlink)
        print "  result is ", res
        return res
        
    def handle(self, _, __):
        print "removing the rate tracking event"
        self.rates.eventManager().remove(self.event)


def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip())
    opts, args = parser.parse_args()

    if len(args) != 3:
        parser.error("<username> <password> <withRateThread>")
    username, password, withthrd = args

    fxgame = FXGame()
    fxgame.setWithRateThread(True) # needs thread to operate
    print "creating rate thread"
    while 1:
        try:
            fxgame.login(username, password)
        except OAException, e:
            print "sample2: caught exception type=", e.type
            print "sample2: unable to connect, retrying...."
            sleep(5)
            continue
        break

    base, quote = "GBP", "JPY"
    mypair = Pair(base, quote)

    myevent = TSLEvent(mypair)
    user = fxgame.getUser()
    myaccount = user.getAccounts()[0]
    rates = fxgame.getRateTable()

    mytick = rates.getRate(mypair)
    delta = (mytick.ask - mytick.bid)*2.2

    market = MarketOrder()
    market.units = 3
    market.base = base
    market.quote = quote
    market.price = (mytick.ask if (market.units > 0) else mytick.bid)
    market.stopLossOrder.price = (
			market.price-delta if (market.units > 0) else market.price+delta)

    myaccount.execute(market)

    slevent = SLEvent(market.ticketNumber, myevent, rates)

    myevent.setWatch(myaccount, market, delta)

    rates.eventManager().add(myevent)
    myaccount.eventManager().add(slevent)

    sleep(2000)

    fxgame.logout()


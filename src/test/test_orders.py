#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Test events and transactions.
"""

# stdlib imports
from __future__ import with_statement
import time

# oanda imports
from oanda import Pair, Tick
from oanda import InvalidDurationException
from oanda import LimitOrder, MarketOrder, StopLossOrder, TakeProfitOrder
from oanda import Position

# local imports
from testsupport import *



class TestOrder(object):

    def test_order(self):
        o = MarketOrder()
        o2 = MarketOrder()

        assert o == o2
        assert not(o < o2)
        assert isinstance(o.orderNumber, int)
        assert isinstance(o.id, int)

        o.units = 17
        assert o.units == 17

        o.price = 42.2
        assert o.price == 42.2
        
        assert isinstance(o.timestamp, int)

        o.base = "USD"
        assert o.base == "USD", o.base
        o.quote = "JPY"
        assert o.quote == "JPY", o.quote

        assert o.pair == Pair("USD/JPY")

        o.lowPriceLimit = 20.0
        assert o.lowPriceLimit == 20.0
        o.highPriceLimit = 21.0
        assert o.highPriceLimit == 21.0
        
    def test_limit(self):
        o = LimitOrder()

        assert isinstance(o.stopLossOrder, StopLossOrder)
        assert isinstance(o.takeProfitOrder, TakeProfitOrder)

        ts = long(time.time()) + 3800
        o.duration = ts
        assert o.duration == ts

    def test_market(self):
        o = MarketOrder()

        assert isinstance(o.stopLossOrder, StopLossOrder)
        assert isinstance(o.takeProfitOrder, TakeProfitOrder)

        assert isinstance(o.ticketNumber, int)
        assert isinstance(o.translink, int)

        assert isinstance(o.realizedPL(), float)
        tick = Tick(12345, 101, 102)
        assert isinstance(o.unrealizedPL(tick), float)

        # Note: Setting the side of the order is done via a sign.
        o.units = 3
        o.price = 100
        assert o.unrealizedPL(tick) == 3.0
        o.units = -3
        assert o.unrealizedPL(tick) == -6.0

    def test_stoploss(self):
        o = StopLossOrder()
        self.do_entry(o)

    def test_takeprofit(self):
        o = TakeProfitOrder()
        ## self.do_entry(o)

    def do_entry(self, o):
        ## FIXME I can't seem to find a valid timestamp... try with a
        ## connection?
        
        now = long(time.time())
        for ts in (now + 100,
                   now - 100,
                   100,
                   -100,
                   2592000,
                   2592000 + 100,
                   2592000 - 100,
                   now + 3800,
                   now + 5000,
                   now + 10000,
                   ):

            ## FIXME figure out what is a valid time, perhaps we need to connect
            ## with rate thread
            try:
                print ts,
                o.duration = ts
                assert o.duration == ts
                print 'VALID'
            except InvalidDurationException:
                print 'INVALID'


class TestPosition(object):

    def test_pos(self):
        # Constructors.
        pos = Position()
        pair = Pair("EUR/USD")
        pos = Position(pair)
        pos = Position(pair, 3000, 1.67)

        pos2 = Position(pair, 3001, 1.67)
        assert pos != pos2

        pos2 = Position(pair, 3000, 1.68)
        assert pos != pos2

        assert isinstance(pos.pair, Pair)
        assert isinstance(pos.units, int)
        assert isinstance(pos.price, float)

        tick = Tick(12345, 1.68, 1.69)
        assert round(pos.unrealizedPL(tick), 2) == 30



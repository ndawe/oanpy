#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Test the data representation objects.
"""

# stdlib imports
from __future__ import with_statement
from time import time
from decimal import Decimal

# oanda imports
from oanda import Pair, Tick, MinMaxPoint, CandlePoint, HistoryPoint
from oanda import RateTable, Instrument, INTERVAL, EventManager
from oanda import PairNotFoundException

# local imports
from testsupport import *



class TestPair(object):

    def test_pair(self):
        pair = Pair()
        ## assert not pair.isValid() -- this is a OANDA bug, not impl yet.

        try:
            pair = Pair("CAD")
            assert False
        except PairNotFoundException:
            pass

        for args in [('EUR/USD',), ('EUR', 'USD')]:
            pair = Pair(*args)
            assert pair.base == 'EUR'
            assert pair.quote == 'USD'
            assert pair.pair == 'EUR/USD'
            assert pair.pair == str(pair.pair)
            assert pair.isValid()

            assert pair.halted in (True, False)

            invpair = pair.getInverse()
            assert invpair.base == 'USD'
            assert invpair.quote == 'EUR'
            assert invpair.pair == 'USD/EUR'
            assert invpair.isValid()


class TestTick(object):

    def test_tick(self):
        tick = Tick()
        print repr(tick), tick
        tick = Tick(100, 10.0, 11.0)
        print repr(tick), tick

        ## FIXME: We need a test for __str__ conversion.

        assert tick.timestamp == 100
        tick.timestamp = 101
        assert tick.timestamp == 101

        assert tick.bid == 10.0
        tick.bid = 10.1
        assert tick.bid == 10.1

        assert tick.ask == 11.0
        tick.ask = 11.1
        assert tick.ask == 11.1

        assert tick.mean == 10.6

        invtick = Tick(0, 2, 4).getInverse()
        assert invtick.bid, invtick.ask == (0.25, 0.5)

        print tick.bid, tick.ask
        tick.fill(0, 2, 4)
        print tick.bid, tick.ask


class TestMinMaxPoint(object):

    def test_minmax(self):
        mm = MinMaxPoint()
        assert mm.min == mm.max == 0

        mm = MinMaxPoint(400, 4.0, 5.0)
        assert mm.min == 4.0
        assert mm.max == 5.0
        assert mm.getMin() == 4.0
        assert mm.getMax() == 5.0

        mm2 = MinMaxPoint(400, 4.0, 5.0)
        assert mm == mm2

        # Timestamp comparison.
        mm3 = MinMaxPoint(399, 4.0, 5.0)
        assert mm3 < mm

        mm4 = mm.clone(mm)
        assert mm == mm4

        assert mm.timestamp == 400
        mm.timestamp = 399
        assert mm.timestamp == 399

        assert mm.getTimestamp() == 399
        mm.setTimestamp(398)
        assert mm.timestamp == 398


class TestCandlePoint(object):

    def test_candle(self):
        cndl = CandlePoint()
        assert cndl.open == cndl.close == cndl.min == cndl.max == 0

        cndl = CandlePoint(400, 1, 2, 3, 4)
        assert cndl.open == 1
        assert cndl.close == 2
        assert cndl.min == 3
        assert cndl.max == 4

        assert cndl.getOpen() == 1
        assert cndl.getClose() == 2
        assert cndl.getMin() == 3
        assert cndl.getMax() == 4

        cndl2 = CandlePoint(400, 1, 2, 3, 4)
        assert cndl == cndl2

        # Timestamp comparison.
        cndl3 = CandlePoint(399, 1, 2, 3, 4)
        assert cndl3 < cndl

        cndl4 = cndl.clone(cndl)
        assert cndl == cndl4

        assert cndl.timestamp == 400
        cndl.timestamp = 399
        assert cndl.timestamp == 399

        assert cndl.getTimestamp() == 399
        cndl.setTimestamp(398)
        assert cndl.timestamp == 398


class TestHistoryPoint(object):

    def test_histpt_ctor(self):
        hp = HistoryPoint()
        hp = HistoryPoint(400, 1, 2, 3, 4, 6, 5, 8, 7)

    def test_histpt(self):
        hp = HistoryPoint(400, 1, 2, 3, 4, 6, 5, 8, 7)
        for t in hp.open, hp.getOpen():
            assert t == Tick(400, 1, 2)
        for t in hp.close, hp.getClose():
            assert t == Tick(400, 3, 4)
        for t in hp.min, hp.getMin():
            assert t == Tick(400, 5, 7)
        for t in hp.max, hp.getMax():
            assert t == Tick(400, 6, 8)

        hp2 = HistoryPoint(400, 1, 2, 3, 4, 6, 5, 8, 7)
        assert hp == hp2

        # Timestamp comparison.
        hp3 = HistoryPoint(399, 1, 2, 3, 4, 6, 5, 8, 7)
        assert hp3 < hp

        hp4 = hp.clone(hp)
        assert hp == hp4

        assert hp.timestamp == 400
        hp.timestamp = 399
        assert hp.timestamp == 399

        assert hp.getTimestamp() == 399
        hp.setTimestamp(398)
        assert hp.timestamp == 398

        cp = hp.getCandlePoint()
        assert isinstance(cp, CandlePoint)

        mm = hp.getMinMaxPoint()
        assert isinstance(mm, MinMaxPoint)


class TestInstrument(object):

    def test_instrument(self):
        with TestConnection() as cli:
            rt = cli.getRateTable()
            assert isinstance(rt, RateTable)
            inst = rt.findInstrument("EUR/USD")
            # Note: during off hours, we don't get FXInstrument instances?!?
            assert isinstance(inst, (Instrument, type(None))), inst

            if inst is not None:
                for aname in ('maxMarginRate', 'active', 'halted', 'precision',
                              'pipettes', 'id', 'valid', 'pair'):
                    assert '%s: %s' % (aname, repr(getattr(inst, aname))) is not None


class TestRateTable(object):

    def test_rtenums(self):
        assert INTERVAL.INTERVAL_5_SEC is not None
        assert INTERVAL.INTERVAL_10_SEC is not None

    def test_ratetable(self):
        with TestConnection(rateThread=1) as cli:
            rt = cli.getRateTable()
            assert isinstance(rt, RateTable)

            tick = rt.getRate(Pair('EUR/USD'))
            assert isinstance(tick, Tick)

            ticks = rt.getHistory(Pair('EUR/USD'), INTERVAL.INTERVAL_1_DAY, 30)
            assert isinstance(ticks, list)
            for tick in ticks:
                assert isinstance(tick, HistoryPoint);

            candles = rt.getCandles(Pair('EUR/USD'), INTERVAL.INTERVAL_1_MIN, 50)
            assert isinstance(candles, list)
            for cndl in candles:
                assert isinstance(cndl, CandlePoint);
            print len(candles)

            minmaxs = rt.getMinMaxs(Pair('USD/CAD'), INTERVAL.INTERVAL_1_DAY, 30)
            assert isinstance(minmaxs, list)
            for mm in minmaxs:
                assert isinstance(mm, MinMaxPoint);

            inst = rt.findInstrument("USD/CAD")
            assert isinstance(inst, Instrument)

            seq = rt.getLastStreamSequenceNumber()
            assert isinstance(seq, int)

            rates = rt.getRatesSince(seq)
            assert isinstance(rates, list)

            evmgr = rt.eventManager()
            assert isinstance(evmgr, EventManager)

    def test_datalimits(self):
        with TestConnection(rateThread=1) as cli:
            rt = cli.getRateTable()
            assert isinstance(rt, RateTable)

            BIG = 100000
            
            ticks = rt.getHistory(Pair('EUR/USD'), INTERVAL.INTERVAL_1_DAY, BIG)
            assert len(ticks) >= 365+1, "Invalid number of ticks: %d" % len(ticks)

            candles = rt.getCandles(Pair('EUR/USD'), INTERVAL.INTERVAL_1_MIN, BIG)
            assert isinstance(candles, list)
            assert len(candles) == 500+1, "Invalid number of candles."

            minmaxs = rt.getMinMaxs(Pair('EUR/USD'), INTERVAL.INTERVAL_1_MIN, BIG)
            assert isinstance(minmaxs, list)
            assert len(minmaxs) == 500+1, "Invalid number of minmax."


class TestDecimal(object):
    "Conversions between float <-> decimal objects."

    def test_decsup(self):
        tick = Tick(int(time()), float(Decimal('17.2103')), float(Decimal('42.2321')))
        print tick

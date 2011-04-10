#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Print the string conversions of all the exported objects.
"""

# stdlib imports
from __future__ import with_statement

# oanda imports
from oanda import *

# local imports
from testsupport import *



class TestRepresentations(object):

    classes = [
        FXGame,
        FXTrade,
        FXClient,
        OAException,
        Pair,
        Tick,
        CandlePoint,
        HistoryPoint,
        MinMaxPoint,
        AccountEvent,
        # Event, # abstract
        # EventInfo, # abstract
        RateEvent,
        TransactionType,
        Transaction,
        Position,
        # Order # abstract
        # EntryOrder # abstract
        LimitOrder,
        MarketOrder,
        StopLossOrder,
        TakeProfitOrder,
        ]


    def _print(self, o):
        print
        print '----------', o.__class__
        print 'str: ', repr(str(o))
        print 'repr:', repr(repr(o))
        
    def test_repns(self):

        for cls in self.classes:
            o = cls()
            self._print(o)

        with TestConnection() as cli:
            user = cli.getUser()
            self._print(user)

            acc = user.getAccounts()[0]
            self._print(acc)

            evmgr = acc.eventManager()
            self._print(evmgr)
        
            rt = cli.getRateTable()
            self._print(rt)
            
            inst = rt.findInstrument('EUR/USD')
            self._print(inst)

            aev = AccountEventInfo(Transaction())
            self._print(aev)

            rev = RateEventInfo(Pair('EUR/USD'), Tick())
            self._print(rev)



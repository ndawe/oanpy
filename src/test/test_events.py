#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Test events and transactions.
"""

# stdlib imports
from __future__ import with_statement

# oanda imports
from oanda import *

# local imports
from testsupport import *



class TestEvents(object):

    def test_evmgr(self):
        with TestConnection() as cli:
            acc = cli.getUser().getAccounts()[0]
            evmgr = acc.eventManager()
            assert isinstance(evmgr, EventManager)

            ## FIXME: test the following methods
            ## evmgr.add(  )
            ## evmgr.remove(  )
            ## evmgr.events(  )

    def test_evenums(self):
        assert FXI_Type is not None
        assert FXI_Type.FXIT_Undefined is not None
        assert FXI_Type.FXIT_Account is not None
        assert FXI_Type.FXIT_Rate is not None

    def test_evbasic(self):
        with TestConnection() as cli:
            acc = cli.getUser().getAccounts()[0]
            rtable = cli.getRateTable()

            for base, evmgr in [
                (RateEvent, rtable.eventManager()),
                (AccountEvent, acc.eventManager())
                ]:

                class MyEvent(base):
                    def match(self, evinfo):
                        trace('match %s' % evinfo)
                    def handle(self, evinfo, em ):
                        trace('handle %s %s' % (evinfo, em))

                ev = MyEvent()
                assert evmgr.events() == []
                evmgr.add(ev)
                events = evmgr.events()
                assert len(events) == 1
                evc = events[0]
                assert isinstance(evc, base)
                
                evmgr.remove(ev)
                assert evmgr.events() == []

                base.transient = False
                assert base.transient == False
                base.transient = True
                assert base.transient == True

                
    def test_txntype(self):
        tt = TransactionType()
        assert str(tt) == ''

        tt = TransactionType("Order Cancelled")
        assert str(tt) == 'Order Cancelled'

    def test_evrate(self):
        pass
        ## FIXME: test the rate events (by getting mkt data).

    def test_evaccount(self):
        pass
        ## FIXME: test the account events (by triggering a trade)

    def test_evinfo(self):
        # Test RateEventInfo
        pair = Pair("EUR/JPY")
        tick = Tick(400, 17.2, 17.4)
        rinfo = RateEventInfo(pair, tick)
        for aname in 'pair', 'tick', 'timestamp':
            assert getattr(rinfo, aname) is not None

        tick2 = Tick(401, 17.2, 17.4)
        rinfo2 = RateEventInfo(pair, tick2)
        assert rinfo.compare_less(rinfo2)
        assert not rinfo2.compare_less(rinfo)

        # Test AccountEventInfo
        txn = Transaction()
        ainfo = AccountEventInfo(txn)
        assert ainfo.timestamp is not None
        txn2 = ainfo.transaction
        assert isinstance(txn2, Transaction)

        txn2 = Transaction()
        ainfo2 = AccountEventInfo(txn)
        assert not ainfo2.compare_less(ainfo)


    def test_evinfocall(self):
        with TestConnection() as cli:
            acc = cli.getUser().getAccounts()[0]
            evmgr = acc.eventManager()
            
            class MyEvent(AccountEvent):
                def match(self, evinfo):
                    trace('match %s' % evinfo)
                def handle(self, evinfo, em ):
                    trace('handle %s %s' % (evinfo, em))
            MyEvent = AccountEvent

            ev = MyEvent()
            txn = Transaction()
            ainfo = AccountEventInfo(txn)
            # Test automatic conversion.
            ev.match(ainfo) 


class TestTransaction(object):

    def test_txn(self):
        txn = Transaction()

        assert isinstance(str(txn), str)
        assert isinstance(repr(txn), str)
        assert isinstance(txn.description, str)

        assert txn == Transaction()
        assert not txn < Transaction()

        assert isinstance(txn.transactionNumber, int)
        assert isinstance(txn.units, int)
        assert isinstance(txn.timestamp, int)

        assert isinstance(txn.base, str)
        assert isinstance(txn.quote, str)

        assert isinstance(txn.price, float)

        assert isinstance(txn.isBuy, bool)
        assert isinstance(txn.isSell, bool)
        ## assert txn.isBuy != txn.isSell

        assert isinstance(txn.link, int)
        assert isinstance(txn.diaspora, int)
        assert isinstance(txn.ccode, int)

        assert isinstance(txn.balance, float)
        assert isinstance(txn.interest, float)
        assert isinstance(txn.stop_loss, float)
        assert isinstance(txn.take_profit, float)




# Note: we could write a test with threads/timers being called during the event
# loop, something like this.

    ## def stop(t):
    ##     t.run()
    ## t = threading.Timer(0.5, stop)
    ## t.args = (t,)
    ## t.start()
    ## # Event loop and exit.
    ## try:
    ##     print 'Ready.'
    ##     fxevents_process_loop()
    ## except KeyboardInterrupt:
    ##     print 'Interrupted.'
    ## print 'Logging out.'
    ## fxclient.logout()
    ## print 'Done.'



class TestEventManager(object):

    def test_evmgrtype(self):
        """ Test that we have some safeguard in which kinds of events we can add
        to the event manager."""

        with TestConnection() as cli:
            user = cli.getUser()

            rtable = cli.getRateTable()
            accounts = user.getAccounts()
            assert len(accounts) == 1
            acc = accounts[0]

            # Try the normal cases first; these two should work.
            for EventCls, evmgr in [(RateEvent, rtable.eventManager()),
                                    (AccountEvent, acc.eventManager())]:
                ev = EventCls()
                evmgr.add(ev)


            # Try the forbidden cases; these two should barf.
            for EventCls, evmgr in [(RateEvent, acc.eventManager()),
                                    (AccountEvent, rtable.eventManager())]:
                ev = EventCls()
                try:
                    evmgr.add(ev)
                    assert False, "This should not be possible."
                except OAException:
                    pass

#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Test the basic connection to OANDA.
"""

# stdlib imports
from __future__ import with_statement
import re, tempfile
from random import random

# oanda imports
from oanda import FXGame
from oanda import Account, RateTable, EventManager

# local imports
from testsupport import *



class TestCommon(object):

    def test_common(self):
        pass
        # Note: at the moment, the implementations of the functions declared on
        # Common are simply not present in the distributed library.


class TestClient(object):

    def test_client_simple(self):
        cli = FXGame()
        cli.version
        assert re.match('FXCLIENT-.*', cli.version)

    def test_login(self):
        cli = FXGame()
        assert cli.isLoggedIn() is False
        cli.login(username, password)
        assert cli.isLoggedIn() is True
        cli.logout()
        assert cli.isLoggedIn() is False

    def test_logfile(self):
        logfn = tempfile.NamedTemporaryFile()
        cli = FXGame()
        cli.setLogfile(logfn.name)
        cli.login(username, password)
        cli.logout()
        contents = open(logfn.name).read()
        assert len(contents) > 0
        
    def test_connection_params(self):
        cli = FXGame()

        cli.setTimeout(2)

        for aname in ("withRateThread",
                      "withKeepAliveThread",
                      "withLoadableKey"):
            print aname
            mget = getattr(cli, 'getW' + aname[1:])
            mset = getattr(cli, 'setW' + aname[1:])

            val = mget()
            mset(not val)
            assert mget() is (not val)

            setattr(cli, aname, val)
            assert getattr(cli, aname)  == val

        assert cli.getServerTime() == 0

    def test_getratetable(self):
        with TestConnection() as cli:
            rt = cli.getRateTable()
            assert isinstance(rt, RateTable)

class TestUser(object):

    def test_user(self):
        with TestConnection() as cli:
            user = cli.getUser()
            print 'UserId:', repr(user.userId)
            print 'CreateDate:', repr(user.createDate)
            print 'Name:', repr(user.name)
            print 'Email:', repr(user.email)
            print 'Address:', repr(user.address)
            print 'Telephone:', repr(user.telephone)
            print 'Profile:', repr(user.profile)

            msg = str(random())
            user.profile = msg
            ## FIXME this does not work.
            ## assert user.profile == msg 

            accnts = user.getAccounts()
            assert len(accnts) > 0
            for acc in accnts:
                assert isinstance(acc, Account)

            acc = user.getAccountWithId(2161382)
            assert acc is not None
            acc = user.getAccountWithId(-1)
            assert acc is None



class TestAccount(object):
    
    def test_account(self):

        with TestConnection() as cli:
            acc = cli.getUser().getAccounts()[0]

            for aname in ('accountId',
                          'accountName',
                          'createDate',
                          'homeCurrency',
                          'marginRate',
                          'balance',
                          'profile'):
                print '%s: %s' % (aname, repr(getattr(acc, aname)))

            for aname in ('realizedPL',):
                print '%s: %s' % (aname, repr(getattr(acc, aname)()))

            rtable = cli.getRateTable()
            for aname, args in (('realizedPL', ()),
                                ('unrealizedPL', (rtable,)),
                                ('marginUsed', (rtable,)),
                                ('marginAvailable', (rtable,))):
                print '%s: %s' % (aname, repr(getattr(acc, aname)(*args)))

            evmgr = acc.eventManager()
            assert isinstance(evmgr, EventManager)
            
    def test_accstate(self):
        
        with TestConnection() as cli:
            acc = cli.getUser().getAccounts()[0]

            trades = acc.getTrades()
            assert isinstance(trades, list)
            ## print trades
            orders = acc.getOrders()
            assert isinstance(orders, list)
            ## print orders
            positions = acc.getPositions()
            assert isinstance(positions, list)
            ## print positions
            txns = acc.getTransactions()
            assert isinstance(txns, list) 
            ## print txns
            
            # FIXME: test with-id methods?



class TestTrades(object):

    def test_trades(self):

        pass ## FIXME TODO
    
        ## // Order execution.
        ## std::vector<MarketOrder> (Account::*execute_market)(MarketOrder&) = &Account::execute;
        ## void (Account::*execute_limit)(LimitOrder& anorder) = &Account::execute;
        ## account.def("execute", execute_market);
        ## account.def("execute", execute_limit);

        ## // Order close.
        ## MarketOrder (Account::*close_market)(const MarketOrder&) = &Account::close;
        ## void (Account::*close_limit)(const LimitOrder&) = &Account::close;
        ## void (Account::*close_position)(const char*) = &Account::close;
        ## account.def("close", close_market);
        ## account.def("close", close_limit);
        ## account.def("close", close_position);

        ## // Order modify.
        ## void (Account::*modify_market)(const MarketOrder&) = &Account::modify;
        ## void (Account::*modify_limit)(const LimitOrder&) = &Account::modify;
        ## account.def("modify", modify_market);
        ## account.def("modify", modify_limit);


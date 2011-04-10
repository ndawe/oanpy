# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Factory and protocol for a rates server.
"""

# stdlib imports
import logging
from collections import defaultdict

# oanda imports
from oanda import Pair
from oanda.utils import normalize_pair

# twisted imports
from twisted.internet import protocol

# local imports
from oanserv.ext.texan import TexanProtocol
from oanserv.protodef import *
from oanserv.times import sec2milli




class RateServerFactory(protocol.ServerFactory):

    # If this is set to true, we discard out-of-order rate updates
    # (note: this is done only per-instrument).
    discard_ooo = False

    def __init__(self, fxclient=None):
        self.protocol = RateServerProtocol

        # An optional connected FXClient object.
        self.fxclient = fxclient

        # A callback that is invoked to signal the presence of a new instrument
        # being monitored. Optional.
        self.cb_newinst = None

        # A dict of pair -> tick, for the latest exchange rates.
        self.xrates = SignalingDict(self.check_newinst)

        # A dict of pair -> Protocol objects to be notified on an update.
        self.subscribers = SignalingDefaultDict(self.check_newinst, set)
        self.all_subscribers = set()

        # Number of discarded OOO packets.
        self.nb_discarded = 0

    def buildProtocol(self, addr):
        p = self.protocol(self.fxclient)
        p.factory = self
        return p

    def check_newinst(self, key):
        if self.cb_newinst is not None:
            self.cb_newinst(key)

    def notify_subscribers(self, ts, venue, spair, bid, ask):
        """ Notify the subscribed clients of the new event. """
        # Note: venue is ignored for now.
        
        if self.discard_ooo:
            try:
                _ts, _, _ = self.xrates[spair]
                if ts < _ts:
                    self.nb_discarded += 1
                    return # Ignore the outdated rate.
            except KeyError:
                pass

        # Update the table.
        self.xrates[spair] = (ts, bid, ask)

        # Send messages.
        subs = set(self.subscribers.get(spair, []))
        subs.update(self.all_subscribers)
        for sub in subs:
            sub.rate(ts, spair, bid, ask)


class RateServerProtocol(TexanProtocol):

    send_protodefs = [RateProtoDef]
    recv_protodefs = [RegProtoDef]

    def __init__(self, fxclient):
        TexanProtocol.__init__(self)
        self.fxclient = fxclient

    def connectionMade(self):
        logging.info('connectionMade')
        self.transport.setTcpNoDelay(True)

    def connectionLost(self, reason):
        logging.info('connectionLost')

        # Remove all subscriptions.
        self.unsubscribe_all(nowarn=True)

    def help(self):
        self.linehelp(self.comment)

    def subscribe(self, inst):
        logging.info('subscribe %s' % inst)
        self.factory.subscribers[normalize_pair(inst)].add(self)

    def unsubscribe(self, inst):
        logging.info('unsubscribe %s' % inst)
        try:
            self.factory.subscribers[normalize_pair(inst)].remove(self)
        except KeyError:
            logging.warning("Instrument %s not subscribed." % inst)

    def subscribe_all(self):
        logging.info('subscribe_all')
        self.factory.all_subscribers.add(self)

    def unsubscribe_all(self, nowarn=False):
        logging.info('unsubscribe_all')
        try:
            self.factory.all_subscribers.remove(self)
        except KeyError:
            if not nowarn:
                logging.warning("Client not subscribed to all.")

        for subs in self.factory.subscribers.itervalues():
            if self in subs:
                subs.remove(self)

    def getrate(self, inst):
        logging.info('getrate %s' % inst)
        spair = normalize_pair(inst)
        xrates = self.factory.xrates

        venue = 'O' # FIXME: hard-coded to OANDA for now.
        if spair in xrates:
            ts, bid, ask = xrates[spair]
        elif spair:
            if self.fxclient is not None:
                # We're online, initialize and send from the live rate.
                rtable = self.fxclient.getRateTable()
                tick = rtable.getRate(Pair(spair))
                (ts, bid, ask) = xrates[spair] = (sec2milli(tick.timestamp),
                                                f2i(tick.bid),
                                                f2i(tick.ask))
            else:
                # We're offline, send 0 rate.
                self.rate(0, spair, 0, 0)
                return
        else:
            self.error("Invalid instrument %s." % repr(inst))
            return
        self.rate(ts, spair, bid, ask)

    def list_instruments(self):
        logging.info('list_instruments')
        for spair in sorted(self.factory.xrates):
            self.decl_instrument(spair)
        self.decl_instrument('')

    def list_subscriptions(self):
        logging.info('list_subcriptions')

        if self in self.factory.all_subscribers:
            self.list_instruments()
            return 
            
        for spair, protocols in self.factory.subscribers.iteritems():
            if self in protocols:
                self.decl_instrument(spair)
        self.decl_instrument('')

    def getrateall(self, txnid):
        logging.info('getrateall %d' % txnid)
        xrates = self.factory.xrates
        for spair in sorted(xrates.iterkeys()):
            (ts, bid, ask) = xrates[spair]
            self.rate(ts, spair, bid, ask)
        self.end_txn(txnid)




class SignalingDictBase(object):

    def __init__(self, cb):
        self.cb = cb

    def __contains__(self, key):
        self.cb(key)
        return super(SignalingDictBase, self).__contains__(key)

    def __getitem__(self, key):
        self.cb(key)
        return super(SignalingDictBase, self).__getitem__(key)

    def __setitem__(self, key, value):
        self.cb(key)
        return super(SignalingDictBase, self).__setitem__(key, value)

    def __detitem__(self, key):
        self.cb(key)
        return super(SignalingDictBase, self).__setitem__(key, value)

class SignalingDict(SignalingDictBase, dict):

    def __init__(self, ranmgr, *args, **kwds):
        SignalingDictBase.__init__(self, ranmgr)
        dict.__init__(self, *args, **kwds)

class SignalingDefaultDict(SignalingDictBase, defaultdict):

    def __init__(self, ranmgr, *args, **kwds):
        SignalingDictBase.__init__(self, ranmgr)
        defaultdict.__init__(self, *args, **kwds)


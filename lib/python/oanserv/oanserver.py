# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
FX exchange rates market data server.
"""

# stdlib imports
import sys, os, logging, grp
from random import randint, random
from time import time
from os.path import getsize
from datetime import datetime, timedelta

# oanda imports
import oanda
from oanda import RateEvent, Pair, OAException
from oanda import utils
from oanda.dispatch import setup_twisted_oanda
from oanda.utils import normalize_pair
from oanda.prices import f2i

# twisted imports
from twisted.internet import reactor

# local imports
from oanserv.dumpfile import getcodec, opendump_write
from oanserv.rateserv import RateServerFactory
from oanserv.times import sec2milli



#-------------------------------------------------------------------------------
# Open and close times, code to figure out if we're in the weekend.

open_hour, open_minute, open_second = (15, 0, 0) # approximately
close_hour, close_minute, close_second = (17, 0, 0)

def closing_date_from(d):
    "Compute the next opening date."
    ndays = 6 - d.weekday()
    if ndays == 0:
        opn = d.replace(
            hour=open_hour, minute=open_minute, second=open_second)
        if d.time() > opn.time():
            opn += timedelta(days=7)
    else:
        opn = (d + timedelta(days=ndays)).replace(
            hour=open_hour, minute=open_minute, second=open_second)
    return opn

def get_weekend(d):
    """Return the (close, open) datetimes for the next relevant weekend from 'd'
    (which switches over at the next open datetime)."""
    next_open = closing_date_from(d)
    close = (next_open - timedelta(days=2)).replace(
        hour=close_hour, minute=close_minute, second=close_second)
    return close, next_open
        
def timedelta_seconds(delta):
    "Return the number of equivalent seconds of the given timedelta object."
    assert isinstance(delta, timedelta)
    return delta.days * 24*60*60 + delta.seconds


#-------------------------------------------------------------------------------

VENUE = 'O'

class RateDispatch(object):
    """ An object that deals with the arrival of a new event/rate. This object
    implements the dumpfile storage and tells the server factory about the new
    event, which in turns dispatches to the clients."""

    def __init__(self, factory, dumpfile=None, codec=None):
        self.factory = factory
        self.dumpfile = dumpfile
        if self.dumpfile is not None:
            encode, decode, msgsize = getcodec(codec)
            self.encode = encode
        self.status = 0

    def event(self, ts, pair, bid, ask):

        # Store the event in the dumpfile.
        if self.dumpfile is not None:
            ntime = sec2milli(time())
            msg = self.encode(ntime, ts, VENUE, pair.pair, bid, ask)
            self.dumpfile.write(msg)

        # Notify the listeners.
        self.factory.notify_subscribers(ts, VENUE, pair.pair, bid, ask)

    def stop(self, status=0):
        self.status = status
        reactor.stop()

    def run(self):
        "Runs the reactor and return a status (int)."
        reactor.run()
        return self.status


#-------------------------------------------------------------------------------

class RatesMonitor(RateEvent):
    """ Monitor for exchange rates from the OANDA API. """

    # Delay after which if there is no activity from the network, we assume
    # we've been made offline and take some sort of action about it.
    killsecs = 600 # secs = 5 minutes

    def __init__(self, dispatch, fxclient):
        RateEvent.__init__(self)
        self.dispatch = dispatch
        self.fxclient = fxclient
        self.setTransient(False) # keeps active

        if self.killsecs:
            self.d = reactor.callLater(self.killsecs, self.on_idle)

    def on_idle(self):
        self.d = None
        logging.error("Not getting any data for %s secs already!" %
                      self.killsecs)

        now = datetime.now()
        dtclose, dtopen = get_weekend(now)
        if dtclose < now < dtopen:
            # Calculate the number of seconds to wait until mkt open.
            logging.error(
                "Oh! It's the weekend, this is normal, let's just wait and see.")
            return

        logging.error("Dump:")
        for line in oanda._oanda._dump().splitlines():
            logging.error("  %s" % line)

        self.dispatch.stop(EXIT_IDLE)

    def handle(self, ei, _):
        """ Convert the data and dispatch it to the clients. """
        tick = ei.tick
        bid, ask = f2i(tick.bid), f2i(tick.ask)
        ts = sec2milli(tick.timestamp)

        # Reschedule kill call for a later time.
        if self.killsecs:
            if self.d is not None:
                self.d.cancel()
            self.d = reactor.callLater(self.killsecs, self.on_idle)

        self.dispatch.event(ts, ei.pair, bid, ask)



#-------------------------------------------------------------------------------

class RandomGeneratorManager(dict):

    def __init__(self, dispatch):
        self.dispatch = dispatch
        self.dispatch.factory.cb_newinst = self.on_newinst  ## Urg. It's ok.

        # A dict of pair -> generator thread.
        self.generators = {}

    def on_newinst(self, key):
        if key not in self.generators:
            self.generators[key] = rangen = (
                RandomEventGenerator(self, Pair(normalize_pair(key))))
            rangen.start()

    def stop(self):
        for gen in self.generators.itervalues():
            gen.stop()

class RandomEventGenerator(object):

    tdelay = 1.0 # secs

    init_bid = 70.00
    init_ask = 70.01
    mininc = 0.01

    def __init__(self, ranmgr, pair):
        self.m = ranmgr
        self.factory = ranmgr.dispatch.factory
        self.pair = pair

        self.stopping = False
        self.d = None

    def start(self):
        reactor.callLater(random()*self.tdelay, self.gen)

    def stop(self):
        self.stopping = True
        if self.d is not None:
            self.d.cancel()

    def gen(self):
        spair = str(self.pair)
        xrates = self.factory.xrates

        ts = sec2milli(time())
        if spair in xrates:
            (_, bid, ask) = xrates[spair]
        else:
            bid, ask = f2i(self.init_bid), f2i(self.init_ask)

        delta = f2i(self.mininc) * randint(-2, +2)
        bid += delta
        ask += delta

        self.m.dispatch.event(ts, self.pair, bid, ask)

        if not self.stopping:
            reactor.callLater(random()*self.tdelay, self.gen)


EXIT_CANNOTLOGIN = 10
EXIT_IDLE = 11

def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip())
    utils.add_userpass(parser)

    parser.add_option('-c', '--codec', action='store', default=None,
                      help="Codec to use to store the messages in the dumpfile.")

    parser.add_option('-p', '--port', action='store', type='int', default=5970,
                      help="Port for the server to listen on.")

    parser.add_option('-o', '-d', '--dumpfile', action='store',
                      help="Name of a dumpfile to use to store messages.")

    parser.add_option('-g', '--group', action='store',
                      help=("Set the group for the output files "
                            "(e.g. the dumpfile)."))

    parser.add_option('--offline', action='store_false', dest='online',
                      default=True,
                      help=("Don't even try to connect, we're offline. "
                            "Generate random data."))

    opts, args = parser.parse_args()
    utils.check_userpass(parser, opts)
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(levelname)-8s]  %(message)s')

    if opts.group:
        try:
            _, _, opts.gid, _ = grp.getgrnam(opts.group)
        except KeyError:
            parser.error("Invalid group '%s'." % opts.group)

    # Log-in to the OANDA system.
    logging.info('-' * 80)
    if opts.online:
        fxclient = opts.ClientClass()
        fxclient.setWithRateThread(True)
        fxclient.setWithLoadableKey(True)
        try:
            fxclient.login(opts.username, opts.password)
        except OAException, e:
            logging.error("Could not login: %s" % e)
            return EXIT_CANNOTLOGIN
    else:
        fxclient = None

    try:
        # Open a dumpfile for writing.
        if opts.dumpfile is not None:
            # We create the dumpfiles as read-only by default, and only visible
            # to the group. Note that UNIX lets use write to the file, despite
            # us not having the right to do that once the file is closed.
            os.umask(0226)
            dfile, codec = opendump_write(opts.dumpfile)

            # Set the appropriate group for the dumpfile.
            if opts.group:
                os.chown(opts.dumpfile, -1, opts.gid)
        else:
            dfile, codec = None, None

        
        # Create a server.
        setup_twisted_oanda(reactor)
        factory = RateServerFactory(fxclient)
        reactor.listenTCP(opts.port, factory)

        # Create event monitoring/generating objects.
        dispatch = RateDispatch(factory, dfile, codec or opts.codec)
        if opts.online:
            logging.info("Enabling rate event monitoring.")
            event = RatesMonitor(dispatch, fxclient)
            rtable = fxclient.getRateTable()
            rtable.eventManager().add(event)
        else:
            logging.info("Enabling random data generator.")
            ranmgr = RandomGeneratorManager(dispatch)

        # Run the main loop.
        try:
            logging.info('Ready.')
            status = dispatch.run()
        except KeyboardInterrupt:
            logging.warning('Interrupted.')

        # Cleanup and exit.
        if opts.online:
            fxclient.logout()
        else:
            ranmgr.stop()

        return status
    finally:
        if dfile is not None:
            dfile.close()
            # Remove empty dumpfiles.
            if getsize(dfile.name) == 0:
                os.remove(dfile.name)

        
if __name__ == '__main__':
    sys.exit(main())


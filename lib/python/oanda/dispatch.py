# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Dispatching helper methods.

The code in this module is used to dispatch events using various methods (see
below).
"""

# oanda imports
from oanda import *




def dispatch_events__blocking(_):
    """ Event dispatching using a blocking call. Blocks and dispatches the
    incoming events. Call fxevents_stop_loop from an event to exit this loop."""
    try:
        fxevents_process_loop()
    except KeyboardInterrupt:
        return





def dispatch_events__twisted(delay):
    """ Event dispatching multiplexed using a Twisted event loop. Call
    reactor.stop() to exit."""
    from twisted.internet import reactor
    setup_twisted_oanda(reactor)
    reactor.callLater(delay, reactor.stop)
    try:
        reactor.run()
    except KeyboardInterrupt:
        pass

def setup_twisted_oanda(reactor):
    """ Do the necessary setup for installing a Twisted event loop."""

    from oanda import fxevents_process_pending, fxevents_set_waker_fd

    # Fixup Twisted.
    patch_wakeup_callback()

    # Tell the C module what file descriptor to notify to wake-up the reactor
    # when new events have arrived.
    fxevents_set_waker_fd(reactor.waker.o)

    # Install a wake-up callback that will process the pending OANDA events.
    reactor.wakeCb = fxevents_process_pending

def patch_wakeup_callback():
    """Gorilla-patch Twisted to allow the installation of a wake-up callback on
    reactor.wakeCb. Just write to reactor.waker.o to wake up the reactor."""

    def doRead(self):
        self.doRead_orig()
        if self.reactor.wakeCb:
            self.reactor.callLater(0, self.reactor.wakeCb)

    from twisted.internet import posixbase
    posixbase._Waker.doRead_orig = posixbase._Waker.doRead
    posixbase._Waker.doRead = doRead




def dispatch_events__thread(delay):
    """ Event dispatching multiplexed from a secondary thread. Call
    fxevents_stop_loop to exit the dispatching thread."""
    import threading
    t = threading.Thread(target=fxevents_process_loop)
    t.start()
    t2 = threading.Timer(delay, fxevents_stop_loop)
    t2.start()
    try:
        t.join()
    except KeyboardInterrupt:
        pass


# Convenient table of dispatching methods.
dispatching_methods = {
    'blocking': dispatch_events__blocking,
    'twisted': dispatch_events__twisted,
    'thread': dispatch_events__thread,
    }



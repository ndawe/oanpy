#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
A prototype program for a method to merge a producer with a Twisted reactor
(e.g. select()). The reactor is woken up with a pipe, and a special reader is
used to fetch the newly produced data (but not serialized via a pipe). This can
be used to integrate events/data produced by a C thread that is running in the
background, with a common Python Twisted reactor. The writer thread is meant to
simulate a C module that produced data via some access function (i.e., the data
to be transferred is not serialized through the pipe, the pipe is only used to
wake up the reactor's select() call).

See this for a description by Stevens of the proposed solution:
http://cr.yp.to/docs/selfpipe.html

After starting to work on this, digging into the Twisted source code, I found
out that it was already implemented by default in there; see posixbase.py.

Note: this will not work as-is under Windows, a different method is used to
write to the pipe (see twisted.internet.posixbase._Win32Waker for details), but
it is doable.
"""

# stdlib imports
import sys, os, threading
from random import random
from time import sleep

# twisted imports
from twisted.internet import reactor, posixbase


msg = """\
But the anger is real; it is powerful; and to simply wish it away, to condemn it
without understanding its roots, only serves to widen the chasm of
misunderstanding that exists between the races.
"""

class Writer(threading.Thread):

    def __init__(self, wp):
        threading.Thread.__init__(self)
        self.wp = wp

    def run(self):
        for c in msg:
            r = random()/30.
            sleep(r)

            queue.append(c)

            # Wake up the reactor.
            # Note: you cannot use reactor.wakeUp(), because this is meant
            # simulate being called from C in a thread that cannot run Python
            # (because it does not have an interpreter).
            os.write(self.wp, '@') 

        if reactor.running:
            reactor.callFromThread(reactor.stop)
        
# Queue of stuff that lives in the C code.
queue = []

# This represents a C function that can be called from Python in the main
# thread.
def processQueue():
    """ Read the messages from the queue. """
    for q in queue:
        sys.stdout.write(q)
    sys.stdout.flush()
    queue[:] = []



def patchWakeUpCallback():
    """Gorilla-patch Twisted to allow the installation of a wake-up callback on
    reactor.wakeCb."""

    def doRead(self):
        self.doRead_orig()
        if self.reactor.wakeCb:
            self.reactor.callLater(0, self.reactor.wakeCb)

    posixbase._Waker.doRead_orig = posixbase._Waker.doRead
    posixbase._Waker.doRead = doRead
    
def main():

    # Patch up the waker to process the queue everytime it wakes up from the
    # pipe.
    patchWakeUpCallback()
    reactor.wakeCb = processQueue

    # Create the writer thread that will fill up the queue.
    wt = Writer(reactor.waker.o)
    wt.start()

    # Run thread reactor.
    reactor.run()

    # Teardown.
    wt.join()


if __name__ == '__main__':
    main()


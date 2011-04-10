#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
A test program to let two threads communicate with a pipe.
"""

# stdlib imports
import sys, os, time, threading
from random import random


msg = __doc__


class Reader(threading.Thread):

    def __init__(self, rp):
        threading.Thread.__init__(self)
        self.rp = rp

    def run(self):
        while 1:
            c = os.read(self.rp, 1)
            if not c:
                break
            sys.stdout.write(c)
            sys.stdout.flush()


class Writer(threading.Thread):

    def __init__(self, wp):
        threading.Thread.__init__(self)
        self.wp = wp

    def run(self):
        for c in msg:
            r = random()/10.
            time.sleep(r)
            os.write(self.wp, c)
        os.close(self.wp)
        

def main():
    
    rp, wp = os.pipe()

    rt = Reader(rp)
    wt = Writer(wp)
    rt.start()
    wt.start()

    time.sleep(1)
    rt.join()
    wt.join()


if __name__ == '__main__':
    main()


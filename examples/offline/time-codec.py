#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Generate timings for running through a dumpfile, decoding and encoding.
"""

# stdlib imports
from time import time

# oanda imports
from oanserv.dumpfile import opendump



def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip())

    parser.add_option('-n',  action='store', type='int', default=20000,
                      help="Nb. of messages to report progress for")

    opts, args = parser.parse_args()
    if len(args) != 1:
        parser.args("You must specify some dumpfiles.")

    n, c = opts.n, 0
    t1 = time()
    for fn in args:
        dumpf = opendump(fn)
        decode, encode = dumpf.decode, dumpf.encode
        for msg in dumpf.rawiter():
            encode(*decode(msg))
            c += 1
            if c % n == 0:
                print '%.2f messages/sec' % (c/(time() - t1))
    t2 = time()
    print '%d secs' % (t2 - t1)


if __name__ == '__main__':
    main()


#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Compute the lag between the published time and the actual received time of a
rate update.
"""

# oanda imports
from oanserv.dumpfile import opendump



def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip())
    opts, args = parser.parse_args()
    if len(args) != 1:
        parser.args("You must specify a dumpfile.")
    fn = args[0]

    dumpf = opendump(fn)
    lsum, lcount = 0, 0
    for ts_actual, timestamp, venue, symbol, bid, ask in dumpf:
        lsum += timestamp - ts_actual
        lcount += 1
        if lcount % 1000 == 0:
            print lsum / float(lcount * 1000)
            lsum, lcount = 0, 0


if __name__ == '__main__':
    main()


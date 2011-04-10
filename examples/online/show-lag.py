#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
A simple example client that subscribes and listens to rate updates (from
oanserv) and that displays the time lag.
"""

# stdlib imports
import sys
from time import time

# twisted imports
from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory

# other imports
from oanserv.ext.texan import TexanProtocol
from oanserv.protodef import *



class ClientProtocol(TexanProtocol):
    
    send_protodefs = [RegProtoDef]
    recv_protodefs = [RateProtoDef]

    def connectionMade(self):
        self.transport.setTcpNoDelay(True)
        reactor.callLater(0, self.subscribe_all)

    def rate(self, timestamp, inst, bid, ask):
        print time() - timestamp/1000.0
        sys.stdout.flush()


def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip())

    parser.add_option('--host', action='store', default='localhost',
                      help="Host to connect to.")
    parser.add_option('--port', action='store', type='int', default=5970,
                      help="Port to connect to.")

    opts, args = parser.parse_args()

    factory = ClientFactory()
    factory.protocol = ClientProtocol
    reactor.connectTCP(opts.host, opts.port, factory)
    reactor.run()

    
if __name__ == '__main__':
    main()


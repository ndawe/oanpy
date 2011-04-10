# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Twisted client-side utilities.
"""

def getsomething(ProtocolClass, host='localhost', port=6000):
    """
    A function that allows us to establish a short-lived connection to a server
    via twisted, and which handles success and failure. You must provide a
    protocol class which communicates with the server, sets the return value as
    its 'payload' attribute, and stops the reactor once it is done. This
    function returns the payload attribute.
    """

    # twisted imports
    from twisted.internet import reactor
    from twisted.internet.protocol import ClientCreator

    protocols = []
    def cbsuccess(protocol):
        "Callback on success. Set the payload as a holder of return value."
        protocols.append(protocol)

    failed = []
    def cbfailed(reason):
        "Callback when failed to connect. Set a sentinel and stop."
        failed.append(reason)
        reactor.callLater(0, reactor.stop)

    clicr = ClientCreator(reactor, ProtocolClass)
    d = clicr.connectTCP(host, port, timeout=2)
    d.addCallback(cbsuccess)
    d.addErrback(cbfailed)

    reactor.run()
    if not failed:
        return protocols[0].payload
    else:
        raise IOError(failed[0])


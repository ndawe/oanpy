# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Protocol definition files.
"""

class RegProtoDef(object):
    """ Description of a simple protocol to register for streaming and querying
    rates."""

    list_instruments = ('L', "List all the supported instruments.",
                        [])

    subscribe = ('S', "Subscribe for notifications on a specific instrument.",
                 [ ('instrument', str, 8) ])

    unsubscribe = ('U', "Remove a subscription to a specific instrument.",
                   [ ('instrument', str, 8) ])

    subscribe_all = ('A', "Subscribe globally to all instruments.",
                     [])

    unsubscribe_all = ('Z', "Remove subscriptions (global and specific).",
                       [])

    list_subscriptions = ('V', "List the currently active subscriptions.",
                          [])

    getrate = ('G', "Immediately fetch a rate for a specific instrument.",
               [ ('instrument', str, 8) ])

    getrateall = ('T', "Immediately fetch rates for all supported instruments.",
                  [ ('txnid', int, 8) ])

    help = ('H', "Request user-readable help summary.", [])



class RateProtoDef(object):
    """ Description of a simple protocol that provides individual rate updates.

    Note that this protocol does not yet work across multiple venues, but it
    could easily be adapted to do so.
    """

    rate = ('R', "Rate notification.",
            [ ('timestamp', int, 16),
              ('instrument', str, 8),
              ('bid', int, 16),
              ('ask', int, 16)])

    # Note: the list ends with an empty instrument.
    decl_instrument = ('I', "Instrument declaration.",
                       [ ('instrument', str, 8) ])

    end_txn = ('X', "End transaction.",
               [ ('txnid', int, 8) ])
               
    error = ('E', "Error messages.",
             [ ('msg', str, 80) ])

    comment = ('C', "Display human-readable text.",
               [ ('comment', str, 80) ])



def find_hg_root():
    import os, os.path
    dn = os.getcwd()
    while not os.path.exists(os.path.join(dn, '.hg')):
        dn = os.path.dirname(dn)
    return dn

def gendoc():
    from os.path import join
    from ext.texan import texan2html
    doc = texan2html((RegProtoDef, RateProtoDef))
    reporoot = find_hg_root()
    open(join(reporoot, 'doc', 'protocols.html'), 'w').write(doc)
    


if __name__ == '__main__':
    gendoc()


#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Print data related to all accounts.
"""

# stdlib imports
import re
from datetime import datetime

# oanda imports
from oanda import OAException, utils
from oanda.report import report_trades, ascii_table



def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip())
    utils.add_userpass(parser)
    opts, args = parser.parse_args()
    utils.check_userpass(parser, opts)
        
    print 'Logging in.'
    fxclient = opts.ClientClass()
    try:
        fxclient.login(opts.username, opts.password)
    except OAException, e:
        raise SystemExit("Could not login: %s" % e)


    rtable = fxclient.getRateTable()
    for acc in fxclient.getUser().getAccounts():
        print
        print 'Account:'
        print '   Id/name: %s (%s)' % (acc.accountId, acc.accountName)
        print '   Balance: %s %s' % (acc.balance, acc.homeCurrency)
        print '   Margin Rate: %s:1' % int(1/acc.marginRate)
        
        head, lines = report_trades(acc, rtable)
        ascii_table(head, lines)
        continue



        print
        print '   Trades:'
        for trade in acc.getTrades():
            print '      %s' % trade

        print
        print '   Orders:'
        for  order in acc.getOrders():
            print '      %s' % order

        print
        print '   Positions:'
        for  position in acc.getPositions():
            print '     %s' % position

        print
        print '   Transactions:'
        for  txn in acc.getTransactions():
            if not re.match('Interest.*', txn.description):
                print '     [%s]  %s  %-30s %7d %s/%s  @  %s' % (
                    txn.transactionNumber,
                    datetime.fromtimestamp(txn.timestamp).isoformat(' '),
                    txn.description,
                    txn.units,
                    txn.base, txn.quote,
                    txn.price
                    )
## Note: you cannot ignore the interest here, Interest Earned entries should be created.

            else:
                print '     [%s]  %s  %-30s %s %s  for %s/%s' % (
                    txn.transactionNumber,
                    datetime.fromtimestamp(txn.timestamp).isoformat(' '),
                    txn.description,
                    txn.interest, acc.homeCurrency,
                    txn.base, txn.quote,
                    )
            ## print '         ', str(txn).strip()

## Collapse USD/USD entries for type.

    print

    # Create a rate event.
    fxclient.logout()





if __name__ == '__main__':
    main()



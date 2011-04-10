# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
The data obtained from the API differs somewhat from the data reported by the
GUI. The routines in this module are used to try to obtain the same information
as the tables reported in the GUI.
"""

def report_trades(acc, rtable):
    header = ('Long/Short Ticket Market Units Stop-Loss Take-Profit '
              'Price Current Profit(Pips)').split()

    lines = []
    for o in acc.getTrades():
        line = ['Long' if o.units >= 0 else 'Short',
                o.orderNumber,
                o.pair,
                o.units,
                o.stopLossOrder.price if o.stopLossOrder else '',
                o.takeProfitOrder.price if o.takeProfitOrder else '',
                o.price]
        tick = rtable.getRate(o.pair)
        current = tick.bid if o.units >= 0 else tick.ask
        inst = rtable.findInstrument(o.pair)
        line.extend( [current, '?'] )

        lines.append(line)

    return header, lines

def report_orders(acc):
    header = ('Long/Short Ticket Market Units Stop-Loss Take-Profit '
              'Price Current Distance Expiry').split()
    
def report_positions(acc):
    header = ('Long/Short Market Units Exposure(USD)'
              'Avg.Price Profit(Pips)').split()

def report_exposure(acc):
    header = ('Long/Short Market Units USD').split()

def report_activity(acc):
    header = ('Ticket Type Market Units Price Balance Date/Time').split()

def account_summary(acc):
    header = ('Balance', 'Unrealized P&L', 'Unrealized P&L (%)',
              'Box Resale Value', 'Net Asset Value', 'Margin Call',
              'Realized P&L', 'Margin Used', 'Margin Available',
              'Margin Percent', 'Position Value')
    


def ascii_table(header, report):
    """ Print an ascii rendition of the returned report. """

    # Check validity of input table.
    nbcols = len(header)
    for line in report:
        assert isinstance(line, (list, tuple))
        assert len(line) == nbcols, (len(line), nbcols, line)

    # Convert all report values to string.
    sreport = [[str(x) for x in line]
               for line in report]

    # Compute the output format width (adaptative to each column).
    maxis = [max(len(line[x]) for line in [header] + sreport)
             for x in xrange(nbcols)]
    print maxis
    



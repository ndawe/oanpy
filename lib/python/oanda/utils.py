# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Various utilities that are useful for working with the OANDA Python API.
"""

# stdlib imports
import sys, os, getpass, re



def normalize_pair(pairstr):
    """ Normalize and validate the pair string; if the string is invalid, return
    the empty string. This is sometimes necessary, because the C++ FXPair class
    has built-in assertions that dump core if you send it an invalid string.
    Better to check in those important cases."""
    mo = re.match('\s*([A-Z]{3})\s*/\s*([A-Z]{3})\s*', pairstr)
    if mo:
        return '%s/%s' % mo.group(1, 2)
    else:
        return ''



dbpasswd = {}

def add_userpass(parser):
    try:
        # Find out default values for the user/password.
        conncls, username, password = \
            os.environ.get('OANDA_USERPASS', ':').split(':')

        # Initialize the password database in case that this is the method
        # selected.
        dbpasswd[conncls, username] = password
    except ValueError:
        username = getpass.getuser()
        conncls = 'fxgame'

    parser.add_option('-C', '--cls', metavar='CLASS',
                      action='store', type='choice', dest='conncls',
                      choices=('fxgame', 'fxtrade'), default=conncls,
                      help="Use the given class (FXTrade or FXGame (default))")
    parser.add_option('--fxtrade', dest='conncls',
                      action='store_const', const='fxtrade',
                      help="Use FXTrade")
    parser.add_option('--fxgame', dest='conncls',
                      action='store_const', const='fxgame',
                      help="Use FXGame")

    parser.add_option('-U', '--username',
                      action='store', default=username)

    parser.add_option('-P', '--password', '--passwd',
                      action='store', default=None) # Empty on purpose.


def check_userpass(parser, opts):

    from oanda import FXGame, FXTrade
    opts.ClientClass = {
        'fxgame': FXGame,
        'fxtrade': FXTrade
        }[opts.conncls]

    if not opts.username:
        sys.stdout.write('Username: ')
        line = raw_input()
        if not line:
            parser.error("Could not get a valid username.")
        else:
            opts.username = line.strip()

    if opts.password == '-':
        # Read password for stdin.
        opts.password = sys.stdin.readline()[:-1]

    elif not opts.password:
        # Try the password database first.
        opts.password = dbpasswd.get((opts.conncls, opts.username), None)
        if not opts.password:
            opts.password = getpass.getpass('Password for %s: ' % opts.username)



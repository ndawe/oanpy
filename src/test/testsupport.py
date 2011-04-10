# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Support/common code for tests.
"""

# stdlib imports
import os

# oanda imports
from oanda import FXGame, FXTrade



def init_userpass():
    """ Initialize test connection parameters. """
    try:
        cls, username, password = os.environ.get(
            'OANDA_TEST_USERPASS', ':').split(':')
    except KeyError:
        raise SystemExit(
            "You must set OANDA_TEST_USERPASS to run automated tests.")
    
    ClientClass = {'fxgame': FXGame,
                   'fxtrade': FXTrade}[cls]
    return ClientClass, username, password

ClientClass, username, password = init_userpass()


class TestConnection(object):

    def __init__(self, rateThread=False):
        self.fxclient = None
        self.rateThread = rateThread

    def __enter__(self):
        self.fxclient = ClientClass()
        if self.rateThread:
            self.fxclient.setWithRateThread(self.rateThread)
        self.fxclient.login(username, password)
        return self.fxclient
    
    def __exit__(self, type, value, traceback):
        self.fxclient.logout()



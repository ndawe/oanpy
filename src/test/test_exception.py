#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Test exceptions.
"""

# stdlib imports
from __future__ import with_statement

# oanda imports
from oanda import OAException, SessionException
from oanda._oanda import _test_exception

# local imports
from testsupport import *;



class TestException(object):

    def test_exc(self):
        try:
            _test_exception()
            assert False, "An exception was expected."
        except SessionException, e:
            assert type(e).__bases__ == (OAException,)
            assert isinstance(e.message, str)
            assert isinstance(e.args, tuple)

        try:
            _test_exception()
            assert False, "An exception was expected."
        except OAException, e:
            pass



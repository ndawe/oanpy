# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
In OANDA's API, prices are represented as floats.
This is a bad thing, because of potential rounding errors.

However, The C API decides to provide the prices as they are presented in the
API, to avoid modifying the API, in order to present an interface as close as
possible to what they offer, and to avoid selecting an alternative
representation.

In this module we provide converters between threee alternative representations
for prices:

- A floating-point representation (forced on us by the OANDA API)

- An integer representation, scaled up to a power of 10 (lightweight and without
  errors)

- Python's standard Decimal objects

Note: in order to do rounding explicitly, we would need to know the precision of
each instrument, thus the converters would need to be initialized with an
FXClient object. (This would quite annoying, having to lug this object around.)
However, since the floating-point representation that is used internally by
Python is large enough that it will not cause errors if we just round using the
ranges of prices that we deal with, we avoid doing that.
"""

# stdlib imports
from decimal import Decimal

# oanda imports
from oanda import Pair

__all__ = 'i2f f2i i2d d2i d2f f2d ireciprocal'.split()



# Multiplier for scaled int representation.
exp = 8
DIV = 10**exp
IDIV = 10**-exp
IDIV_dec = Decimal('10')**-exp


# Scaled int <-> Float
def f2i(fprice):
    return int(round(fprice * DIV))

def i2f(iprice):
    return iprice * IDIV

L, F = f2i, i2f


# Scaled int <-> Decimal
def i2d(iprice):
    return Decimal(iprice) * IDIV_dec

def d2i(dprice):
    return int(dprice * DIV)


# float <-> Decimal
def d2f(dprice):
    return float(dprice)

def f2d(fprice):
    # Unrolled the function defs for speed.
    iprice = int(round(fprice * DIV))
    return Decimal(iprice) * IDIV_dec


# Some functions.
def ireciprocal(iprice):
    "Return the inverse of the integer price."
    return f2i(1/i2f(iprice))




def get_precision(fxclient, pair):
    """ Return the precision that a pair requires, according to the API."""
    if isinstance(pair, Pair):
        pair = pair.pair
    try:
        precision = _precisions[pair]
    except KeyError:
        rtable = fxclient.getRateTable()
        inst = rtable.findInstrument(pair)
        precision = inst.precision
        _precisions[pair] = precision
    return precision


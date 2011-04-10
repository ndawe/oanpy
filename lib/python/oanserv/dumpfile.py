# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Code to encode/decode a dumpfile of incoming market data.

We support only one type of message: rate update (bid/ask).

Notes:

- We include a field for the venue, in order to support rate data from multiple
  venues in the future (this is very likely);

- The packet format provides space for two timestamps:

  1. update timestamp: the timestamp provided to use by the data channel, and

  2. actual timestamp: time at which we actually received the packet.

  These are distinct, and the latter is used to replay the dumpfile as
  accurately as possible to the original flow of data. The actual timestamps are
  always monotonically increasing, whereas the update timestamps aren't, about
  0.5% of OANDA's updates arrive out-of-order.

"""

# stdlib imports
import sys, struct, os, logging, re
from os.path import getsize, exists
from datetime import datetime
from subprocess import *

# local imports
from collections import namedtuple
from oanserv.ext.headfile import HeadFile


__all__ = ('getcodec', 'opendump', 'opendump_stdin')


# Constants.
DEFAULT_VENUE = 'O'


# Functions to convert to/from 6-byte integer.
MAXNUM = 2**(32+16)
MAXINT = 2**32
MAXSHORT = 2**16

def int2hi(lint):
    """ Convert a long into a (short-int, int) pair that can be encoded in 6
    bytes."""
    assert lint < MAXNUM, lint
    high = lint >> 32
    assert high < MAXSHORT, high
    low = lint & 0xffffffff
    assert low < MAXINT, low
    return high, low

def hi2int(high, low):
    """ Convert a (short-int, int) pair into a Python int. """
    return (high << 32) + low



"""
raw24: Compact encoding in 24 bytes.


The data is in the following format:

  Field         Nb. Bytes       Data           Interpretation
  ------------- --------------- -------------- -----------------
  timestamp     6               int            epoch time (msecs)
  base          3               str            base instrument
  quote         3               str            quote instrument
  bid           6               int            price (scaled int)
  ask           6               int            price (scaled int)
  --------------------------------------------------------------
"""

st24 = struct.Struct('! HI 3s 3s HI HI')
assert st24.size == 24, st24.size
pack24 = st24.pack
unpack24 = st24.unpack

def encode_24(ts_actual, timestamp, venue, symbol, lbid, lask):
    # Note: 'ts_actual' and 'venue' are ignored.
    tsh, tsl = int2hi(timestamp)
    bidh, bidl = int2hi(lbid)
    askh, askl = int2hi(lask)
    base, quote = symbol.split('/')
    return pack24(tsh, tsl, base, quote, bidh, bidl, askh, askl)

def decode_24(msg):
    assert len(msg) == 24, "Truncated message: %s bytes only" % len(msg)
    tsh, tsl, base, quote, bidh, bidl, askh, askl = unpack24(msg)
    timestamp = hi2int(tsh, tsl)
    assert timestamp > 0
    symbol = '%s/%s' % (base, quote)
    ibid = hi2int(bidh, bidl)
    iask = hi2int(askh, askl)
    assert ibid > 0
    assert iask > 0
    # Note: use same timestamp to fill in.
    return RateUpdate(timestamp, timestamp, DEFAULT_VENUE, symbol, ibid, iask)




"""
raw32: Simple encoding in 32 bytes. Despite it being quite wasteful, decoding is
fast, and this support multiple venues.

The data is in the following format:

  Field         Nb. Bytes       Data           Interpretation
  ------------- --------------- -------------- -----------------
  timestamp     8               long           epoch time (msecs)
  venue         1               char           id for venue
  symbol        7               str            instrument name
  bid           8               long           price (scaled int)
  ask           8               long           price (scaled int)
  --------------------------------------------------------------
"""

st32 = struct.Struct('! q c 7s q q')
assert st32.size == 32, st32.size
pack32 = st32.pack
unpack32 = st32.unpack

def encode_32(ts_actual, timestamp, venue, symbol, lbid, lask):
    # Note: 'ts_actual' is ignored.
    return pack32(timestamp, venue, symbol, lbid, lask)

def decode_32(msg):
    assert len(msg) == 32, "Truncated message: %s bytes only" % len(msg)
    timestamp, venue, symbol, lbid, lask = unpack32(msg)
    # Note: use same timestamp to fill in.
    return RateUpdate(timestamp, timestamp, venue, symbol, lbid, lask)



"""
raw40: Full encoding, takes 40 bytes. Wasteful, for measurements only.

The data is in the following format:

  Field         Nb. Bytes       Data           Interpretation
  ------------- --------------- -------------- -----------------
  ts_actual     8               int            epoch time (msecs)
  timestamp     8               int            epoch time (msecs)
  venue         1               char           id for venue
  symbol        7               str            instrument name
  bid           8               int            price (scaled int)
  ask           8               int            price (scaled int)
  --------------------------------------------------------------
"""

st40 = struct.Struct('! q q c 7s q q')
assert st40.size == 40, st40.size
pack40 = st40.pack
unpack40 = st40.unpack

def encode_40(ts_actual, timestamp, venue, symbol, lbid, lask):
    # Note: 'ts_actual' is ignored.
    return pack40(ts_actual, timestamp, venue, symbol, lbid, lask)

def decode_40(msg):
    assert len(msg) == 40, "Truncated message: %s bytes only" % len(msg)
    ts_actual, timestamp, venue, symbol, lbid, lask = unpack40(msg)
    # Note: use same timestamp to fill in.
    return RateUpdate(ts_actual, timestamp, venue, symbol, lbid, lask)




"""
raw32n: New compact encoding, which supports venue and two timestamps.


The data is in the following format:

  Field         Nb. Bytes       Data           Interpretation
  ------------- --------------- -------------- -----------------
  ts_actual     6               int            epoch time (msecs)
  timestamp     6               int            epoch time (msecs)
  venue         1               char           id for venue
  symbol        7               str            instrument name
  bid           6               int            price (scaled int)
  ask           6               int            price (scaled int)
  --------------------------------------------------------------
"""

st32n = struct.Struct('! HI HI c 7s HI HI')
assert st32n.size == 32, st32n.size
pack32n = st32n.pack
unpack32n = st32n.unpack

def encode_32n(ts_actual, timestamp, venue, symbol, ibid, iask):
    tsah, tsal = int2hi(ts_actual)
    tsh, tsl = int2hi(timestamp)
    bidh, bidl = int2hi(ibid)
    askh, askl = int2hi(iask)
    return pack32n(tsah, tsal, tsh, tsl, venue, symbol, bidh, bidl, askh, askl)

def decode_32n(msg):
    assert len(msg) == 32, "Truncated message: %s bytes only" % len(msg)
    tsah, tsal, tsh, tsl, venue, symbol, bidh, bidl, askh, askl = unpack32n(msg)
    ts_actual = hi2int(tsah, tsal)
    assert ts_actual > 0
    timestamp = hi2int(tsh, tsl)
    assert timestamp > 0
    ibid = hi2int(bidh, bidl)
    iask = hi2int(askh, askl)
    return RateUpdate(ts_actual, timestamp, venue, symbol, ibid, iask)


__c_encoders = False
if __c_encoders:
    # An experiment writing the codec in C: for the 'raw32n' encoding, the
    # Python version provides 75k msg/seca, while the C version provides only
    # 27k msg/sec. Note that in comparison, the simpler (and incomplete) 'raw32'
    # encoding provides 181k msgs/secs. 'raw40' is only slightly slower than
    # 'raw32': 171k. In order to save space, we're paying a cost of about 2.5x
    # slower in speed, and the C code does not help.
    try:
        from oanda._oanda import _fast_encode_32n, _fast_decode_32n
        def encode_32n(*args):
            return pack32n(*_fast_encode_32n(*args))
        def decode_32n(msg):
            return RateUpdate(*_fast_decode_32n(unpack32n(msg)))
    except ImportError:
        logging.warning("Using slow version of 'raw32n' codec.")




#-------------------------------------------------------------------------------

_codecs_names = ('raw32n', 'raw32', 'raw24', 'raw40')
_codecs = {
    'raw32n': (encode_32n, decode_32n, st32n.size),
    'raw40': (encode_40, decode_40, st40.size),
    'raw32': (encode_32, decode_32, st32.size),
    'raw24': (encode_24, decode_24, st24.size)
    }

def getcodec(codecname):
    """ Return appropriate (encoder, decoder, msgsize) triple for the given
    codec."""
    if codecname is None:
        codecname = 'raw32n' # Default encoder/decoder.
    try:
        return _codecs[codecname]
    except KeyError:
        raise KeyError("Unknown codec: %s" % repr(codecname))



_tsdiff = 3600 * 3 * 1000 # less than 3 hours validates timestamps.
_tspercspread = .02

def compare_packets(msg1, msg2):
    """ Compare the values contained within the two given packets, to see if
    they are valid encodings. """
    tsa1, ts1, v1, sym1, ibid1, iask1 = msg1
    tsa2, ts2, v2, sym2, ibid2, iask2 = msg2
    if (abs(tsa2 - tsa1) > _tsdiff or abs(ts2 - ts1) > _tsdiff):
        return False
    if (abs(tsa1 - ts1) > _tsdiff or abs(tsa2 - ts2) > _tsdiff):
        return False
    if '/' not in sym1 or '/' not in sym2:
        return False
    if (iask1-ibid1)/(iask1+ibid1) > _tspercspread:
        return False
    return True

def detect_encoding(f):
    """ Automatically detect the encoding of a dumpfile, by looking at the
    beginning bytes of it. We do this by checking the distance between two
    timestamps. """

    pos = f.tell()
    minhead = 2*64 # 64 is the longest possible packet I can imagine.
    f.seek(0)
    head = f.read(minhead)
    if len(head) < minhead:
        return None
    f.seek(pos)

    for codec in _codecs_names:
        encode, decode, s = getcodec(codec)
        msg1, msg2 = decode(head[0:s]), decode(head[s:2*s])
        if compare_packets(msg1, msg2):
            return codec




# A compact and efficient tuple-wrapper class for our data.
RateUpdate = namedtuple(
    'RateUpdate',
    ('ts_actual', 'timestamp', 'venue', 'symbol', 'bid', 'ask'))


class DumpFile(object):
    """ An abstraction for a dumpfile, which allows iterating over its packets.
    It also supports limited caching for the beginning blocks of the file, so
    that we can establish the encoding even if the file is read from stdin (this
    is very convenient in order to support various file formats.)"""


    def __init__(self, f, codecname, enc, dec, sz, **kw):
        self.f = f
        self.codecname = codecname
        self.encode = enc
        self.decode = dec
        self.msgsize = sz

        # If this is true, discard out-of-order packets in the iterator code;
        # this is checked per-instrument.
        self.discard_ooo = kw.get('discard_ooo', False)
        self.discard_ts = {}

    @property
    def name(self):
        return self.f.name

    def isseekable(self):
        return (self.f is not sys.stdin and
                not isinstance(self.f, HeadFile))

    def tell(self):
        assert self.f.tell() % self.msgsize == 0, (self.f.tell() % self.msgsize)
        return self.f.tell() / self.msgsize

    def seek(self, offset, whence=os.SEEK_SET):
        self.f.seek(offset * self.msgsize, whence)
        self.discard_ts.clear()

    def rewind(self):
        self.f.seek(0, os.SEEK_SET)

    def first(self):
        """ Return just the first message, without changing the file pointer.
        This is useful for loop initializations."""
        orig = self.tell()
        try:
            self.seek(0)
            return self.next()
        finally:
            self.seek(orig)

    def last(self):
        """ Return just the last message, without changing the file pointer.
        This is useful for loop initializations."""
        orig = self.tell()
        try:
            try:
                self.seek(-1, os.SEEK_END)
            except ValueError, e:
                # If the file is zipped, we cannot seek from the end.
                if str(e) != 'Seek from end not supported': raise
                nbmessages = len(self)
                self.seek(nbmessages-1)
            return self.next()
        finally:
            self.seek(orig)

    def findtime(self, timestamp):
        """ Find msg xindex to a specific timestamp. We binary search is
        performed to find the closest message. """

        orig = self.tell()
        try:
            # Check against the beginning and ends of the file.
            self.seek(0)
            pbegin = self.first()
            nmax = len(self)
            self.seek(nmax-1)
            pend = self.next()

            if timestamp < pbegin.ts_actual:
                return 0
            elif timestamp >= pend.ts_actual:
                return nmax
            else:
                # At this point we know that our point in time lies within the file.
                return self._findtime(timestamp,
                                      0, pbegin.ts_actual,
                                      nmax, pend.ts_actual)
        finally:
            self.seek(orig)

    def _findtime(self, t, nmin, tmin, nmax, tmax):
        if (nmax - nmin) <= 1:
            return nmin

        nmid = (nmax + nmin)/2
        ## Our binary search could use the hypothesis that there is a uniform
        ## distribution of messages over time in order to speed up its search.
        ##
        ## frac = float(t - tmin) / (tmax - tmin)
        ## nmid =  int(frac * (nmax - nmin) + nmin)

        # Note: we could save and use the indexes that we calculate from time to
        # time.
        assert nmin < nmid < nmax, (nmin, nmid, nmax)
        self.seek(nmid)
        pmid = self.next()
        tmid = pmid.ts_actual

        if t <= tmid:
            return self._findtime(t, nmin, tmin, nmid, tmid)
        else:
            return self._findtime(t, nmid, tmid, nmax, tmax)

    # Decoding iterator.

    def __iter__(self):
        return self

    def next(self):
        if self.discard_ooo:
            while 1:
                r = self.f.read(self.msgsize)
                if not r:
                    raise StopIteration
                e = self.decode(r)
                try:
                    ts, sym = e.timestamp, e.symbol
                    pts = self.discard_ts[e.symbol]
                    if ts < pts:
                        continue
                    else:
                        self.discard_ts[sym] = ts
                except KeyError:
                    self.discard_ts[sym] = ts
                return e
        else:
            r = self.f.read(self.msgsize)
            if not r:
                raise StopIteration
            return self.decode(r)

    # Raw iterator.
    def rawiter(self):
        return self.RawIter(self)

    def __len__(self):
        if re.match('.*\.(gz|bz2)', self.f.name, re.I):
            # We have to parse it using the C lib (via external process).
            p = Popen(('gzip', '-l', self.f.name), shell=False, stdout=PIPE)
            out, _ = p.communicate()
            mo = re.match('[ \t]*(\d+)[ \t]+(\d+)[ \t]+', out.splitlines()[1])
            sz = int(mo.group(2))
        else:
            sz = getsize(self.f.name)
        return sz / self.msgsize

    class RawIter(object):

        def __init__(self, dumpf):
            self.dumpf = dumpf
            self.msgsize = dumpf.msgsize

        def __iter__(self):
            return self

        def next(self):
            # IMPORTANT: The raw iterator does not filter OOO packets.
            r = self.dumpf.f.read(self.msgsize)
            if not r:
                raise StopIteration
            return r

    def getextents(self):
        """ Return the (start, end) timestamps. """
        msg1 = self.first()
        msg2 = self.last()
        return (msg1.timestamp, msg2.timestamp)


def opendumpf(f, **kw):
    codec = detect_encoding(f)
    encode, decode, msgsize = getcodec(codec)
    return DumpFile(f, codec, encode, decode, msgsize, **kw)

def opendump(fn, **kw):
    """ Open a dumpfile, automatically detecting its encoding. """
    if fn == '-':
        return opendump_stdin(**kw)
    elif fn.endswith('.gz'):
        import gzip
        f = gzip.open(fn)
    elif fn.endswith('.bz2'):
        import bzip2
        f = bzip2.open(fn)
    else:
        f = open(fn, 'rb')
    return opendumpf(f, **kw)

def opendump_stdin(**kw):
    """ Open stdin as a dumpfile, automatically detecting its encoding. """
    return opendumpf(HeadFile(sys.stdin, 512), **kw)


def opendump_write(fn):
    """ Open a dumpfile for writing, returns (file, detected-codec). 'codec' is
    None if the file did not exist before calling this function."""
    if exists(fn):
        f = open(fn, 'rb')
        codec = detect_encoding(f)
        f.close()
        _, _, msgsize = getcodec(codec)
    else:
        codec = None

    dfile = file(fn, 'ab', 0)

    if codec:
        dfilesz = getsize(fn)
        remain = dfilesz % msgsize
        if remain != 0:
            logging.warning("Truncated data present in dumpfile; truncating.")
            dfile.seek(dfilesz / msgsize)

    return dfile, codec





#-------------------------------------------------------------------------------

def test():
    """ A basic test that creates and encodes dumpfiles in all supported
    encodings, and decodes them and compares the output."""

    from time import time
    from oanda.prices import f2i
    from itertools import izip

    def ntime(): return int(time()*1000)

    messages = [
        (ntime(), ntime(), 'O', 'EUR/USD', f2i(1.47019), f2i(1.47020)),
        (ntime(), ntime(), 'O', 'USD/CAD', f2i(1.0602), f2i(1.0606)),
        (ntime(), ntime(), 'O', 'XAU/USD', f2i(804.03), f2i(804.24)),
        (ntime(), ntime(), 'O', 'EUR/USD', f2i(1.47010), f2i(1.47012)),
        (ntime(), ntime(), 'O', 'EUR/USD', f2i(1.47009), f2i(1.47012)),
        ]

    for codec in sorted(_codecs):
        print 'Testing: %s' % codec
        fn = '/tmp/testdump.%s' % codec

        # Open a new file and create some material in the specific encoding.
        f = open(fn, 'wb')
        encode, decode, msgsize = getcodec(codec)
        for data in messages:
            packet = encode(*data)
            ## trace(len(packet))
            f.write(packet)
        f.close()

        dumpf = opendump(fn)
        assert dumpf.codecname == codec
        for msg, u in izip(messages, dumpf):
            assert tuple(u) == msg, u

if __name__ == '__main__':
    test()


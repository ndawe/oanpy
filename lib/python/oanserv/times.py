# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Generic time parsing and conversion utilities.
"""

# stdlib imports
import re
from time import mktime
from datetime import datetime



def sec2milli(ts):
    "Convert timestamp in secs to an int in milliseconds."
    return int(ts * 1000)

def milli2sec(millis):
    "Convert int timestamp in milliseconds to a float in seconds."
    return millis / 1000


# Insert a valid timerange way under
_minsecs = mktime(datetime(2000, 1, 1).timetuple())
_maxsecs = mktime(datetime(2020, 1, 1).timetuple())

def issecs(ts):
    """ Given a timestamp (millis) or time-since-epoch (seconds), return True if
    the time range is in seconds."""
    return _minsecs < ts < _maxsecs

def ismillis(ts):
    return not (_minsecs < ts < _maxsecs)


complete_re = re.compile("""
   ^
   (?P<year>\d\d\d\d)
   [-/]
   (?P<mth>\d\d)
   [-/]
   (?P<day>\d\d)
   ([T.]|\s+)
   (?P<hour>\d\d)
   [:h]?
   ((?P<min>\d\d)
    ([:m]?
     (?P<sec>\d\d))?)?
   (,(?P<milli>\d+))?
   $
""", re.VERBOSE)


def parse_time(timestr):
    """ Parse a time string and return a timestamp (with 1000ths). """
    if timestr is None: # Support for simpler client-side code.
        return None

    timestr = timestr.strip()

    mo = complete_re.match(timestr)
    if mo is None:
        return None
    year, mth, day, hour = mo.group('year', 'mth', 'day', 'hour')
    min, sec, milli = mo.group('min', 'sec', 'milli')
    if min is None:
        min = 0
    if sec is None:
        sec = 0
    if milli is None:
        milli = 0
    milli = int(milli) * 1000
    dt = datetime(*map(int, (year, mth, day, hour, min, sec, milli)))
    return dt

        
def test():
    print parse_time('2008-09-09 13:07:56,652')
    print parse_time('2008-09-09 13:07:56')
    print parse_time('2008-09-09 13:07')
    print parse_time('2008-09-09 13h')
    print parse_time('2008-09-09   13:07:56,652')
    print parse_time('2008-09-09T13:07:56,652')
    print parse_time('2008-09-09.13:07:56')
    print parse_time('2008-09-09.130756')

if __name__ == '__main__':
    test()

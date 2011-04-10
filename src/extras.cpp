//*****************************************************************************/
// Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
// Licensed under the terms of the GNU Lesser General Public License, version 3.
// See http://furius.ca/oanpy/LICENSE for details.
//*****************************************************************************/

// Include precompiled header for Boost.
#include "pchboost.h"

// C headers.
#include <cstring>

// stdc++ headers.
#include <iostream>

// Python headers.
#include "Python.h"

using namespace boost::python;
using namespace std;


namespace OanPy {

// This file contains code that is not really needed for wrapping the OANDA API
// to Python, but that we use in the rate server.

// Conversion to/from 6-byte integers

const uint64_t HI_MAXNUM = uint64_t(1) << 48;
const uint HI_MAXSHORT = 1 << 16;


void int2hi( uint64_t lint, uint& high, uint& low )
{
    assert(lint < HI_MAXNUM);

    high = lint >> 32;
    assert(high < HI_MAXSHORT);

    low = lint & 0xffffffff;
}

tuple int2hi_( uint64_t lint )
{
    uint high, low;
    int2hi(lint, high, low);
    return make_tuple(high, low);
}

uint64_t hi2int( uint high, uint low )
{
    return ((uint64_t)high << 32) + low;
}



// Faster encoding of a full packet in 32 bits.
tuple encode_32n(
    uint64_t ts_actual, 
    uint64_t timestamp, 
    const char* venue, 
    const char* symbol, 
    uint64_t ibid, 
    uint64_t iask
) 
{
    uint tsah, tsal;
    int2hi(ts_actual, tsah, tsal);

    uint tsh, tsl;
    int2hi(timestamp, tsh, tsl);

    uint bidh, bidl;
    int2hi(ibid, bidh, bidl);

    uint askh, askl;
    int2hi(iask, askh, askl);

    return make_tuple(tsah, tsal, tsh, tsl,
                      venue, symbol,
                      bidh, bidl, askh, askl);
}

// Faster decoding of a full packet in 32 bits.
tuple decode_32n( const tuple& t ) 
{
    uint tsah = extract<uint>(t[0]);
    uint tsal = extract<uint>(t[1]);
    uint tsh = extract<uint>(t[2]);
    uint tsl = extract<uint>(t[3]);
    char venue = extract<char>(t[4]);
    const char* symbol = extract<const char*>(t[5]);
    uint bidh = extract<uint>(t[6]);
    uint bidl = extract<uint>(t[7]);
    uint askh = extract<uint>(t[8]);
    uint askl = extract<uint>(t[9]);

    uint64_t ts_actual = hi2int(tsah, tsal);
    assert(ts_actual >= 0);

    uint64_t timestamp = hi2int(tsh, tsl);
    assert(timestamp >= 0);

    uint64_t ibid = hi2int(bidh, bidl);
    uint64_t iask = hi2int(askh, askl);

    return make_tuple(ts_actual, timestamp,
                      venue, symbol,
                      ibid, iask);
}


// Export event-related stuff.
void export_extras()
{
    def("_fast_encode_32n", encode_32n);
    def("_fast_decode_32n", decode_32n);
    def("_int2hi", int2hi_);
    def("_hi2int", hi2int);
}

}


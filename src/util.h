//*****************************************************************************/
// Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
// Licensed under the terms of the GNU Lesser General Public License, version 3.
// See http://furius.ca/oanpy/LICENSE for details.
//*****************************************************************************/

#ifndef OANPY_UTIL_H
#define OANPY_UTIL_H

// Include precompiled header for Boost.
#include "pchboost.h"

// stdc++ headers.
#include <string>
#include <sstream>


namespace OanPy {

// Utility function to expose the string conversion operators as Python strings.
template <class T>
boost::python::str to_string(T& o)
{
    std::ostringstream oss;
    oss << o;
    return boost::python::str(oss.str());
}

}

#endif // OANPY_UTIL_H

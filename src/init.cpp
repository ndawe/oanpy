//*****************************************************************************/
// Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
// Licensed under the terms of the GNU Lesser General Public License, version 3.
// See http://furius.ca/oanpy/LICENSE for details.
//*****************************************************************************/

// Include precompiled header for Boost.
#include "pchboost.h"

// stdc++ headers.
#include <sstream>

// Python headers.
#include "Python.h"

// Local headers.
#include "events.h"


namespace {

const char* docstring = "Python interface to the OANDA C++ API.";

std::string dump()
{
    using namespace std;
    using namespace OanPy;
    ostringstream oss;
    oss << dump_events();
    return oss.str();
}

}


namespace OanPy {

void export_exception();
void export_connect();
void export_data();
void export_events();
void export_orders();
void export_extras();

}


BOOST_PYTHON_MODULE( _oanda )
{
    using namespace boost::python;
    using namespace OanPy;

    export_exception();
    export_connect();
    export_data();
    export_events();
    export_orders();
    export_extras();

    // Module debugging.
    def("_dump", dump);

    // Module help.
    scope().attr( "__doc__" ) = docstring;
}


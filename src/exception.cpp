//*****************************************************************************/
// Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
// Licensed under the terms of the GNU Lesser General Public License, version 3.
// See http://furius.ca/oanpy/LICENSE for details.
//*****************************************************************************/

// Include precompiled header for Boost.
#include "pchboost.h"

// Python headers.
#include "Python.h"

// stdc++ headers.
#include <string>
#include <sstream>

// OANDA headers.
#include <OAException.h>
#include <RateTable.h>
#include <Account.h>
#include <EntryOrder.h>
#include <Order.h>
#include <RateTable.h>


using namespace boost::python;
using namespace Oanda;

namespace {

template <class E>
struct translate_exception
{
    static object exctype;

    template <class F>
    translate_exception(
        const std::string& module,
        const std::string& name,
        F*
    )
    {
        translate_exception(module, name, translate_exception<F>::exctype.ptr());
    }

    translate_exception(
        const std::string& module,
        const std::string& name,
        PyObject* base
    )
    {
        // Create a new Python exception type for this class.
        const std::string fullname = module + std::string(".") + name;
        exctype = object(
            handle<>(
                PyErr_NewException(const_cast<char*>(fullname.c_str()), base, NULL)
            ));

        assert(exctype.ptr() != 0);

        // Register an exception translator for this.
        register_exception_translator<E>(handler);

        // Add the new exception to the module namespace.
        PyObject* moduleDict = PyModule_GetDict( scope().ptr() );
        if ( moduleDict == NULL ) {
            Py_FatalError("Cannot get module dictionary.");
        }
        if ( PyDict_SetItemString( moduleDict, name.c_str(), exctype.ptr() ) ) {
            Py_FatalError("Module dictionary insertion problem.");
        }
    }

    static void handler( E const& e )
    {
        std::stringstream oss;
        oss << e.type() << " (" << e.code() << ")" << std::ends;
        PyErr_SetString(exctype.ptr(),
                        oss.str().c_str());
    };

};

// Template instantiations.
template <class T> object translate_exception<T>::exctype;



// Raise some exception from C++ (for test usage).
void test_exception()
{
    throw SessionException();
}

}



#define TRANSLATE_EXC(C, B) translate_exception<C>("oanda", #C, (B*)0);

namespace OanPy {

// Export exceptions and register translators.
void export_exception()
{
    // We cannot use the normal Boost mechanism to expose exceptions classes,
    // because we need to derive from the Python Exception class (or a derived
    // one) and this is not a C++ type, but rather a PyObject instance.
    // Therefore, we need to use a home-cooked PyErr_NewException mechanism
    // instead. However, note that a few people have tried to do the same
    // (search mailing-list) and have come pretty close, and it is believed to
    // be doable.

    // OAException.h
    translate_exception<OAException>("oanda", "OAException", 
                                     PyExc_RuntimeError);
    
    TRANSLATE_EXC(SessionException, OAException);
    TRANSLATE_EXC(InvalidUserException, SessionException);
    TRANSLATE_EXC(InvalidPasswordException, SessionException);
    TRANSLATE_EXC(UserLockedException, SessionException);
    TRANSLATE_EXC(SessionTimeoutException, SessionException);
    TRANSLATE_EXC(SessionDisconnectedException, SessionException);
    TRANSLATE_EXC(SessionErrorException, SessionException);
    TRANSLATE_EXC(UnknownErrorException, SessionException);

    // Account.h
    TRANSLATE_EXC(AccountException, OAException);
    TRANSLATE_EXC(CurrencyException, AccountException);
    TRANSLATE_EXC(NSFException, AccountException);
    TRANSLATE_EXC(InvalidOrderException, AccountException);
    TRANSLATE_EXC(AccountBusyException, SessionException);

    // Order.h
    TRANSLATE_EXC(OrderException, OAException);
    TRANSLATE_EXC(InvalidLimitsException, OrderException);
    TRANSLATE_EXC(InvalidUnitsException, OrderException);
    TRANSLATE_EXC(InvalidPriceException, OrderException);

    // EntryOrder.h
    TRANSLATE_EXC(InvalidDurationException, OrderException);

    // RateTable.h
    TRANSLATE_EXC(RateTableException, OAException);
    TRANSLATE_EXC(PairNotFoundException, RateTableException);

    def("_test_exception", test_exception);
}

}


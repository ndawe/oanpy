//*****************************************************************************/
// Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
// Licensed under the terms of the GNU Lesser General Public License, version 3.
// See http://furius.ca/oanpy/LICENSE for details.
//*****************************************************************************/

// Include precompiled header for Boost.
#include "pchboost.h"

// System headers.
#include <signal.h>

// stdc++ headers.
#include <stdexcept>
#include <deque>
#include <memory>
#include <sstream>

// Python headers.
#include "Python.h"

// OANDA headers.
#include <Transaction.h>
#include <FXEvent.h>
#include <Account.h>
#include <RateTable.h>

// Local headers.
#include "events.h"
#include "util.h"


using namespace boost::python;
using namespace Oanda;

namespace {

// *** IMPORTANT ***
//
// Because the event callbacks occur in separate C threads (i.e., not Python
// interpreter threads), we cannot call back into Python from them. Our solution
// to this involves queuing the calls and providing a C function that can be
// called from Python in order to dispatch the events to callbacks in the main
// thread (from something like an event loop). We use a condition variable to
// signal that a new message has arrived.


// Wrap an event to be dispatched to the main thread.
struct QueuedEvent {

    FXEvent* _ev;
    PyObject* _evowner; // Python owner of the FXEvent object.
    boost::shared_ptr<const FXEventInfo> _ei;
    FXEventManager* _em;

    QueuedEvent( FXEvent* ev,
                 PyObject* evowner,
                 const boost::shared_ptr<const FXEventInfo>& ei,
                 FXEventManager* em ) :
        _ev(ev),
        _evowner(evowner),
        _ei(ei),
        _em(em)
    {
        if ( _evowner != 0 ) {
            incref(_evowner);
        }
    }

    virtual ~QueuedEvent()
    {
        if ( _evowner != 0 ) {
            decref(_evowner);
        }
    }

private:
    QueuedEvent( const QueuedEvent& other );
    QueuedEvent& operator=( const QueuedEvent& other );

};

// The queue of events to be dispatched in the Python thread, and objects for
// its concurrent access.
std::deque< boost::shared_ptr<QueuedEvent> > evqueue;

// Timestamp/real time, at which the last event was pushed.
time_t evqueue_last_timestamp = -1;
time_t evqueue_last_realtime = -1;

// Mutex and condition variable to communicate with the queue.
boost::condition evqueue_var;
boost::recursive_mutex evqueue_mutex;

// True if we're currently dispatching events from process_loop.
bool evqueue_dispatching = false;

// File descriptor used to wake-up a select() call when we receive an event.
int evqueue_waker_fd = -1;



int process_pending( int );

template <class event_type, class evinfo_type, typename init_type>
struct EventWrap : event_type, wrapper<event_type>
{
    // Required in order to let get_override be called.
    friend int process_pending( int );

    EventWrap(const init_type* init = NULL) :
        event_type(init),
        wrapper<event_type>()
    {}

    // Note: copy constructor required for return a list of these objects.
    EventWrap(const event_type& copy) :
        event_type(copy),
        wrapper<event_type>()
    {}

    // bool match( const FXEventInfo* ei ) {
    //     // std::cout << "match" << std::endl << std::flush;
    //     return true; // Let Python override do all the work?
    // }

    void handle( const FXEventInfo* ei, FXEventManager* em );

};

template <class event_type, class evinfo_type, typename init_type>
void EventWrap<event_type, evinfo_type, init_type>::handle(
    const FXEventInfo* ei, FXEventManager* em
)
{
    // std::cout << "C handle" << std::endl << std::flush;

    // Queue the information required to dispatch the event later.
    assert( ei != 0 );
    const evinfo_type* dei = dynamic_cast<const evinfo_type*>(ei);
    assert( dei != 0 );

    // Make a copy that will survive this call.
    boost::shared_ptr<const FXEventInfo> eicopy( new evinfo_type(*dei) );
    {
        boost::recursive_mutex::scoped_lock lock(evqueue_mutex);

        // IMPORTANT: There was a potential problem here: we're passing the
        // 'this' ptr to be copied in the QueueEvent object, and this means
        // 'this' has to survive until the pending events are processed, but
        // there is no guarantee that this was going to be the case because
        // Python owns the object and manages its lifespan itself. We thus need
        // to be able to hold a reference with the Python mechanism; that's why
        // we need to dig into the wrapper and provide PyObject* owner directly.
        boost::shared_ptr<QueuedEvent> ev(
            new QueuedEvent(this, detail::wrapper_base_::get_owner(*this),
                            eicopy, em)
        );
        evqueue.push_front(ev);

        // Set the last times for debugging.
        evqueue_last_realtime = time(0);
        evqueue_last_timestamp = ei->timestamp();

        if ( evqueue_waker_fd != -1 ) {
            // Write a byte to a pipe to wake up a select() loop.
            static char buf[2] = "@";
            write(evqueue_waker_fd, buf, 1);
        }
    }
    evqueue_var.notify_one();
}


// Explicit template instantiation.
template class EventWrap<FXRateEvent, FXRateEventInfo, FXPair>;
typedef EventWrap<FXRateEvent, FXRateEventInfo, FXPair> FXRateEventWrap;

template class EventWrap<FXAccountEvent, FXAccountEventInfo, char>;
typedef EventWrap<FXAccountEvent, FXAccountEventInfo, char> FXAccountEventWrap;



// Process the pending events (to be called from the main thread)
// and return the number of events dispatched.
int process_pending( int max_events = 0 )
{
    int nb_events = 0;

    // Protect the queue.
    boost::recursive_mutex::scoped_lock lock(evqueue_mutex);

    while ( evqueue.size() > 0 ) {
        if ( max_events > 0 && nb_events >= max_events ) {
            break; // Break if we hit the max allowed nb. of events to dispatch.
        }

        // Pop the next message to dispatch.
        boost::shared_ptr<QueuedEvent> ev = evqueue.back();
        evqueue.pop_back();
        nb_events++;

        // Cast to its appropriate OANDA interface type, "Rate" or "Account" event.
        const FXRateEventInfo* rei =
            dynamic_cast<const FXRateEventInfo*>(ev->_ei.get());
        if ( rei != 0 ) {
            // std::cout << "Dispatching rate event." << std::endl;

            FXRateEventWrap* rev = dynamic_cast<FXRateEventWrap*>(ev->_ev);
            assert(rev != 0);
            override fmatch = rev->get_override("match");

            if ( fmatch.ptr() == Py_None || fmatch(ptr(rei)) ) {
                override fhandle = rev->get_override("handle");
                if ( fhandle.ptr() == Py_None ) {
                    throw std::runtime_error(
                        "You need to override handle() of FXEvent.");
                }
                else {
                    boost::shared_ptr<OanPy::FXEventManagerWrap> em(
                        new OanPy::FXEventManagerWrap(ev->_em, FXIT_Rate)
                    );
                    // Note: we have a choice for how to wrap EventInfo here:
                    // use the already created event-info instance (faster), or
                    // wrap a static copy of it. The first approach does not
                    // allow us to keep a copy later on because it is owned by
                    // the OANDA client lib.
                    fhandle(*rei, em);
                }
            }
        }
        else {
            const FXAccountEventInfo* aei =
                dynamic_cast<const FXAccountEventInfo*>(ev->_ei.get());
            if ( aei != 0 ) {
                // std::cout << "Dispatching account event." << std::endl;

                FXAccountEventWrap* aev = dynamic_cast<FXAccountEventWrap*>(ev->_ev);
                assert(aev != 0);
                override fmatch = aev->get_override("match");
                if ( fmatch.ptr() == Py_None || fmatch(ptr(aei)) ) {
                    override fhandle = aev->get_override("handle");
                    if ( fhandle.ptr() == Py_None ) {
                        throw std::runtime_error(
                            "You need to override handle() of FXEvent.");
                    }
                    else {
                        boost::shared_ptr<OanPy::FXEventManagerWrap> em(
                            new OanPy::FXEventManagerWrap(ev->_em, FXIT_Account)
                        );
                        // (Same note as above for rei.)
                        fhandle(*aei, em);
                    }
                }
                else {
                    throw std::runtime_error("Invalid event info type");
                }
            }
        }
    }
    return nb_events;
}

BOOST_PYTHON_FUNCTION_OVERLOADS(
    process_pending__overloads, process_pending, 0, 1)


// Blocking call that processes the events and
// returns the number of events dispatched.
int process_loop( int timeout = 0, int max_events = 0 )
{
    int nb_events = 0;

    // Calculate the time to exit.
    boost::xtime t;
    if ( timeout != 0  ) {
        boost::xtime_get(&t, boost::TIME_UTC);
        t.sec += timeout;
    }

    boost::recursive_mutex::scoped_lock lock(evqueue_mutex);
    if ( evqueue_dispatching == true ) {
        throw std::runtime_error(
            "You cannot call two FX event loops at the same time.");
    }
    evqueue_dispatching = true;

    while ( evqueue_dispatching ) {

        nb_events += process_pending(max_events);

        // Check for event processing limit.
        if ( max_events > 0 && nb_events >= max_events ) {
            assert( nb_events == max_events );
            evqueue_dispatching = false;
            break;
        }

        Py_BEGIN_ALLOW_THREADS;
        if ( timeout == 0 ) {
            evqueue_var.wait(lock);
        }
        else {
            if ( evqueue_var.timed_wait(lock, t) == false ) {
                evqueue_dispatching = false;

                Py_BLOCK_THREADS;
                break;
            }
        }

        Py_END_ALLOW_THREADS;
    }

    assert(evqueue_dispatching == false);
    return nb_events;
}

BOOST_PYTHON_FUNCTION_OVERLOADS(
    process_loop__overloads, process_loop, 0, 2)


// Block until one event shows up, process it and return.
void process_one( int timeout = 0 )
{
    process_loop(timeout, 1);
}

BOOST_PYTHON_FUNCTION_OVERLOADS(
    process_one__overloads, process_one, 0, 1)


// Signal that the blocking process loop should be stopped and exit.
void stop_loop()
{
    boost::recursive_mutex::scoped_lock lock(evqueue_mutex);
    evqueue_dispatching = false;
    evqueue_var.notify_one();
}

// Set the file descriptor to be used (optionally) for select() based
// dispatching.
void set_waker_fd( int fd )
{
    boost::recursive_mutex::scoped_lock lock(evqueue_mutex);
    evqueue_waker_fd = fd;
}



// Wrappers for functions which return pointers. Not great... there may be a way
// to create a Boost.Python return_value_policy ResultConverterGenerator that
// does that for us.

const FXPair& FXRateEvent__key( const FXRateEvent& e )
{
    return *e.key();
}

const FXTransactionType& FXAccountEvent__key( const FXAccountEvent& e )
{
    return *e.key();
}

const FXPair& FXRateEventInfo__pair( const FXRateEventInfo& einfo )
{
    return *einfo.pair();
}

const FXTick& FXRateEventInfo__tick( const FXRateEventInfo& einfo )
{
    return *einfo.tick();
}

const Transaction& FXAccountEventInfo__transaction( const FXAccountEventInfo& einfo )
{
    return *einfo.transaction();
}



// Stop the loop when an interrupt is signaled.
void sigint_handler( int sig_num )
{
    PyErr_SetInterrupt();
    stop_loop();
}

// Setup to make sure that we can interrupt our processes.
void setup_signal_handlers()
{
    signal(SIGINT, sigint_handler);
}

}



namespace OanPy {

FXEventManagerWrap::FXEventManagerWrap( FXEventManager* evmgr, FXI_Type type ) :
    _evmgr(evmgr),
    _type(type)
{
    assert(evmgr != 0);
    assert(type != FXIT_Undefined);
}

// Check that this wrapper is being provided with the appropriate event type
// (check for internal errors in usage).
void FXEventManagerWrap::checkEventType( FXEvent* ev )
{
    // Blow up if an inappropriate type of event is added.
    if ( _type == FXIT_Account ) {
        FXAccountEvent* aev = dynamic_cast<FXAccountEvent*>(ev);
        if ( aev == 0 ) {
            std::cout << "Account error " << aev << std::endl << std::flush;
            throw AccountException();
        }
    }
    else if ( _type == FXIT_Rate ) {
        FXRateEvent* rev = dynamic_cast<FXRateEvent*>(ev);
        if ( rev == 0 ) {
            throw RateTableException();
        }
    }
    else {
        throw std::runtime_error(
            "Internal error: Undefined FXEventManagerWrap.");
    }
}

bool FXEventManagerWrap::add( FXEvent* ev )
{
    checkEventType(ev);
    _evmgr->add(ev);
}

bool FXEventManagerWrap::remove( FXEvent* ev )
{
    checkEventType(ev);
    _evmgr->remove(ev);
}

// Convert the events to Python and return a list of them.
list FXEventManagerWrap__events( FXEventManagerWrap& self )
{
    // Note: Unfortunately Boost.Python does not have a analogue to Python's
    // 'set' object, so we use a list instaed.
    list s;
    std::set<FXEvent*> result = self._evmgr->events();
    for ( std::set<FXEvent*>::const_iterator it = result.begin();
          it != result.end();
          ++it ) {
        FXEvent* ev = *it;

        // Important note: we *could* create exposed classes without wrappers,
        // so that we are able to avoid downcasting here and instead access the
        // events without a copy.
        FXRateEvent* rev = dynamic_cast<FXRateEvent*>(ev);
        if ( rev != 0 ) {
            s.append( *rev );
        }
        else {
            FXAccountEvent* aev = dynamic_cast<FXAccountEvent*>(ev);
            if ( aev != 0 ) {
                s.append(aev);
            }
            else {
                throw std::runtime_error("Invalid event type");
            }
        }
    }
    return s;
}

// Create event manager wrappers.
boost::shared_ptr<FXEventManagerWrap> RateTable__eventManager( RateTable& rtable )
{
    return boost::shared_ptr<FXEventManagerWrap>(
        new FXEventManagerWrap(rtable.eventManager(), FXIT_Rate)
    );
}

boost::shared_ptr<FXEventManagerWrap> Account__eventManager( Account& rtable )
{
    return boost::shared_ptr<FXEventManagerWrap>(
        new FXEventManagerWrap(rtable.eventManager(), FXIT_Account)
    );
}

// Print some debug output.
std::string dump_events()
{
    using namespace std;
    ostringstream oss;
    boost::recursive_mutex::scoped_lock lock(evqueue_mutex);
    {
        oss << "evqueue_last_timestamp: " << evqueue_last_timestamp << endl;
        oss << "evqueue_last_realtime: " << evqueue_last_realtime << endl;
        oss << "size of evqueue: " << evqueue.size() << endl;
    }
    return oss.str();
}



// Export all the event-related stuff.
void export_events()
{
    // Event manager.
    class_<FXEventManagerWrap,
        boost::shared_ptr<FXEventManagerWrap>,
        boost::noncopyable> eventmgr("EventManager", no_init);
    scope().attr("FXEventManager") = eventmgr;
    {
        eventmgr.def("add", &FXEventManagerWrap::add);
        eventmgr.def("remove", &FXEventManagerWrap::remove);
        eventmgr.def("events", &FXEventManagerWrap__events);
    }

    // Base class for rate and account events.
    class_<FXEvent, boost::noncopyable> event("Event", no_init);
    scope().attr("FXEvent") = event;
    {
        event.def("match", (&FXEvent::match));
        event.def("handle", (&FXEvent::handle));
        // event.def("isNull", (&FXEvent::isNull));

        bool(FXEvent::*fxevent_gettransient)() = &FXEvent::transient;
        void(FXEvent::*fxevent_settransient)(bool) = &FXEvent::transient;
        event.add_property("transient", fxevent_gettransient, fxevent_settransient);
        event.def("setTransient", fxevent_settransient);
    }

    enum_<FXI_Type>("FXI_Type")
        .value("FXIT_Undefined", FXIT_Undefined)
        .value("FXIT_Account", FXIT_Account)
        .value("FXIT_Rate", FXIT_Rate);


    // Wrappers for rate and account events.
    class_<FXRateEventWrap, bases<FXEvent> > revent(
        "RateEvent", init<>());
    scope().attr("FXRateEvent") = revent;
    {
        revent.def(init<const FXPair*>());
        revent.add_property(
            "key", make_function(&FXRateEvent__key,
                                 return_value_policy<copy_const_reference>()));
        revent.def("match", &FXRateEvent::match);
        revent.def("match_pair", &FXRateEvent::match_pair);
        // revent.def("isNull",
        //            &FXRateEvent::isNull,
        //            &FXRateEventWrap::default_isNull);
    }

    class_<FXAccountEventWrap, bases<FXEvent> > aevent(
        "AccountEvent", init<>());
    scope().attr("FXAccountEvent") = aevent;
    {
        aevent.def(init<const char*>());
        aevent.add_property(
            "key", make_function(&FXAccountEvent__key,
                                 return_value_policy<copy_const_reference>()));
        aevent.def("match", &FXAccountEvent::match);
        aevent.def("match_transaction_type", &FXAccountEvent::match_transaction_type);
        // aevent.def("isNull",
        //            &FXAccountEvent::isNull,
        //            &FXAccountEventWrap::default_isNull);
    }


    // A class used by FXAccountEvent for transaction types.
    class_<FXTransactionType> transtype("TransactionType", init<>());
    scope().attr("FXTransactionType") = transtype;
    {
        transtype.def(init<const char*>());

        transtype.def("__str__", &to_string<FXTransactionType>);
        // transtype.def("__str__", &FXTransactionType::c_str);

        transtype.def("__eq__", &FXTransactionType::operator==);
        transtype.def("__lt__", &FXTransactionType::operator<);
        // FIXME: Add the other comparison operators.
    }


    // "Info" descriptor classes for rate and account events.
    class_<FXEventInfo, boost::noncopyable> info("EventInfo", no_init);
    scope().attr("FXEventInfo") = info;
    {
        FXI_Type(FXEventInfo::*info_type)() const = &FXEventInfo::type;
        info.add_property("type", info_type);
        info.add_property("timestamp", &FXEventInfo::timestamp);
        info.def("__eq__", &FXEventInfo::operator==);
        info.def("__lt__", &FXEventInfo::operator<);
    }

    class_<FXRateEventInfo, bases<FXEventInfo> > rateinfo(
        "RateEventInfo", init<const FXPair&, const FXTick&>());
    scope().attr("FXRateEventInfo") = rateinfo;
    {
        rateinfo.add_property(
            "pair", make_function(&FXRateEventInfo__pair,
                                  return_value_policy<copy_const_reference>()));
        rateinfo.add_property(
            "tick", make_function(&FXRateEventInfo__tick,
                                  return_value_policy<copy_const_reference>()));
        rateinfo.add_property("timestamp", &FXRateEventInfo::timestamp);
        rateinfo.def("compare_less", &FXRateEventInfo::compare_less);
    }

    class_<FXAccountEventInfo, bases<FXEventInfo> > accountinfo(
        "AccountEventInfo", init<const Transaction&>());
    scope().attr("FXAccountEventInfo") = accountinfo;
    {
        accountinfo.add_property(
            "transaction", make_function(&FXAccountEventInfo__transaction,
                                         return_value_policy<copy_const_reference>()));

        accountinfo.add_property("timestamp", &FXAccountEventInfo::timestamp);
        accountinfo.def("compare_less", &FXAccountEventInfo::compare_less);
    }


    // The descriptor of a transaction.
    class_<Transaction> trans("Transaction", init<>());
    {
        trans.def("__str__", &to_string<Transaction>);

        trans.def("__eq__", &Transaction::operator==);
        trans.def("__lt__", &Transaction::operator<);
        // FIXME: Add the other comparison operators.

        trans.add_property("transactionNumber", &Transaction::transactionNumber);

        int(Transaction::*trans_units)() const = &Transaction::units;
        trans.add_property("units", trans_units);

        time_t(Transaction::*trans_timestamp)() const = &Transaction::timestamp;
        trans.add_property("timestamp", trans_timestamp);

        const char*(Transaction::*trans_base)() const = &Transaction::base;
        const char*(Transaction::*trans_quote)() const = &Transaction::quote;
        trans.add_property("base", trans_base);
        trans.add_property("quote", trans_quote);

        double(Transaction::*trans_price)() const = &Transaction::price;
        trans.add_property("price", trans_price);

        bool(Transaction::*trans_isBuy)() const = &Transaction::isBuy;
        bool(Transaction::*trans_isSell)() const = &Transaction::isSell;
        trans.add_property("isBuy", trans_isBuy);
        trans.add_property("isSell", trans_isSell);

        int(Transaction::*trans_link)() const = &Transaction::link;
        trans.add_property("link", trans_link);

        int(Transaction::*trans_diaspora)() const = &Transaction::diaspora;
        trans.add_property("diaspora", trans_diaspora);

        int(Transaction::*trans_ccode)() const = &Transaction::ccode;
        trans.add_property("ccode", trans_ccode);

        double(Transaction::*trans_balance)() const = &Transaction::balance;
        trans.add_property("balance", trans_balance);

        double(Transaction::*trans_interest)() const = &Transaction::interest;
        trans.add_property("interest", trans_interest);

        double(Transaction::*trans_stop_loss)() const = &Transaction::stop_loss;
        trans.add_property("stop_loss", trans_stop_loss);

        double(Transaction::*trans_take_profit)() const = &Transaction::take_profit;
        trans.add_property("take_profit", trans_take_profit);

        trans.def("getDescription", &Transaction::getDescription);
        trans.add_property("description", &Transaction::getDescription);
    }

    def("fxevents_process_loop",
        process_loop, process_loop__overloads());
    def("fxevents_process_one",
        process_one, process_one__overloads());

    def("fxevents_process_pending",
        process_pending, process_pending__overloads());

    def("fxevents_stop_loop", stop_loop);

    def("fxevents_set_waker_fd", set_waker_fd);

    setup_signal_handlers();
}

}


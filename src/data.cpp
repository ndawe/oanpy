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
#include <vector>

// OANDA headers.
#include <MinMaxPoint.h>
#include <CandlePoint.h>
#include <FXTick.h>
#include <FXPair.h>
#include <FXInstrument.h>
#include <FXHistoryPoint.h>
#include <RateTable.h>

// Local headers.
#include "util.h"
#include "events.h"



using namespace boost::python;
using namespace Oanda;


namespace {

str FXTick__repr__( const FXTick& o )
{
    static PyObject* format = PyString_FromString("<oanda.FXTick bid=%f ask=%f>");
    tuple t = make_tuple(o.bid(), o.ask());
    return str(handle<>( PyString_Format(format, t.ptr()) ));
}

str MinMaxPoint__repr__( const MinMaxPoint& o )
{
    static PyObject* format = PyString_FromString("<oanda.MinMaxPoint min=%f max=%f>");
    tuple t = make_tuple(o.getMin(), o.getMax());
    return str(handle<>(PyString_Format(format, t.ptr())));
}

str CandlePoint__repr__( const CandlePoint& o )
{
    static PyObject* format = PyString_FromString("<oanda.CandlePoint open=%f close=%f min=%f max=%f>");
    tuple t = make_tuple(o.getOpen(), o.getClose(), o.getMin(), o.getMax());
    return str(handle<>(PyString_Format(format, t.ptr())));
}

str FXHistoryPoint__repr__( const FXHistoryPoint& o )
{
    static PyObject* format = PyString_FromString("<oanda.FXHistoryPoint open=%s close=%s min=%s max=%s>");
    tuple t = make_tuple(o.getOpenConst(), o.getCloseConst(), o.getMinConst(), o.getMaxConst());
    return str(handle<>(PyString_Format(format, t.ptr())));
}

list RateTable__getHistory( RateTable& rtable,
                            const FXPair& pair,
                            long interval,
                            int numTicks =_RATE_HISTORY_MAXTICKS )
{
    list l;
    std::vector<FXHistoryPoint> result;
    // std::cout << "getHistory " << pair << "  " << interval << std::endl;
    rtable.getHistory(result, pair, interval, numTicks);
    // std::cout << "COUNT " << result.size() << std::endl;
    for ( std::vector<FXHistoryPoint>::const_iterator it = result.begin();
          it != result.end();
          ++it ) {
        l.append( *it );
    }

    return l;
}

list RateTable__getHistory2( RateTable& rtable,
                             const FXPair& pair,
                             long interval )
{
    return RateTable__getHistory(rtable, pair, interval);
}

// Note: we could turn some of these into templates at some point.
list RateTable__getCandles( RateTable& rtable,
                            const FXPair& pair,
                            long interval,
                            int numTicks =_RATE_HISTORY_MAXTICKS )
{
    list l;
    std::vector<CandlePoint> result(numTicks);
    rtable.getCandles(result, pair, interval, numTicks);
    for ( std::vector<CandlePoint>::const_iterator it = result.begin();
          it != result.end();
          ++it ) {
        l.append( *it );
    }
    return l;
}

list RateTable__getMinMaxs( RateTable& rtable,
                            const FXPair& pair,
                            long interval,
                            int numTicks =_RATE_HISTORY_MAXTICKS )
{
    list l;
    std::vector<MinMaxPoint> result(numTicks);
    rtable.getMinMaxs(result, pair, interval, numTicks);
    for ( std::vector<MinMaxPoint>::const_iterator it = result.begin();
          it != result.end();
          ++it ) {
        l.append( *it );
    }
    return l;
}

list RateTable__getRatesSince( RateTable& rtable, int seqnum )
{
    list l;
    std::vector<FXPairTick> result;
    rtable.getRatesSince(result, seqnum);
    for ( std::vector<FXPairTick>::const_iterator it = result.begin();
          it != result.end();
          ++it ) {
        l.append( *it );
    }
    return l;
}

// Just a convenience to avoid having to convert the pair into a string
// everytime.
const FXInstrument& RateTable__findInstrument1(
    RateTable& rtable, const char* pair
)
{
    return *rtable.findInstrument(pair);
}

const FXInstrument& RateTable__findInstrument2(
    RateTable& rtable, const FXPair& pair
)
{
    return RateTable__findInstrument1(rtable, pair.pair());
}

// Add extra validation for the Pair string initializers.
std::auto_ptr<FXPair> FXPair__init1_safe( const char* spair )
{
    if ( spair != 0 and strchr(spair, '/') == 0 ) {
        throw PairNotFoundException();
    }
    return std::auto_ptr<FXPair>( new FXPair(spair) );
}

}


namespace OanPy {

// Export event-related stuff.
void export_data()
{
    class_<FXPair> pair("Pair", init<>());
    scope().attr("FXPair") = pair;
    {
        pair.def(init<const char*, const char*>());
        // pair.def(init<const char*>());
        pair.def("__init__", make_constructor(FXPair__init1_safe));

        pair.def("__str__", &to_string<FXPair>);

        pair.def("__eq__", &FXPair::operator==);
        pair.def("__lt__", &FXPair::operator<);

        pair.add_property("base", &FXPair::base);
        pair.add_property("quote", &FXPair::quote);

        const char*(FXPair::*fxpair_getpair)() const = &FXPair::pair;
        void(FXPair::*fxpair_setpair1)(const char*) = &FXPair::pair;
        pair.add_property("pair", fxpair_getpair, fxpair_setpair1);

        void(FXPair::*fxpair_setpair2)(const char*, const char*) = &FXPair::pair;
        pair.def("set", fxpair_setpair2);

        pair.def("getInverse", &FXPair::getInverse);
        pair.def("isValid", &FXPair::isValid);
        pair.add_property("valid", &FXPair::isValid); // extra
        pair.add_property("halted", &FXPair::halted);
    }

    class_<FXTick> tick("Tick", init<>());
    scope().attr("FXTick") = tick;
    {
        tick.def(init<const time_t, const double, const double>());
        tick.def("__str__", &to_string<FXTick>);
        tick.def("__repr__", FXTick__repr__);

        tick.def("__eq__", &FXTick::operator==);

        time_t(FXTick::*fxtick_gettimestamp)() const = &FXTick::timestamp;
        void(FXTick::*fxtick_settimestamp)(time_t) = &FXTick::timestamp;
        tick.add_property("timestamp", fxtick_gettimestamp, fxtick_settimestamp);

        double(FXTick::*fxtick_getbid)() const = &FXTick::bid;
        void(FXTick::*fxtick_setbid)(double) = &FXTick::bid;
        tick.add_property("bid", fxtick_getbid, fxtick_setbid);

        double(FXTick::*fxtick_getask)() const = &FXTick::ask;
        void(FXTick::*fxtick_setask)(double) = &FXTick::ask;
        tick.add_property("ask", fxtick_getask, fxtick_setask);

        tick.add_property("mean", &FXTick::mean);

        tick.def("getInverse", &FXTick::getInverse);

        // This really means "set values".
        tick.def("fill", &FXTick::fill);
    }

    class_<MinMaxPoint> minmax("MinMaxPoint", init<>());
    {
        minmax.def(init<time_t, double, double>());
        minmax.def("__str__", &to_string<MinMaxPoint>);
        minmax.def("__repr__", MinMaxPoint__repr__);

        minmax.def("clone", &MinMaxPoint::clone,
                   return_value_policy<copy_non_const_reference>());

        minmax.def("getMin", &MinMaxPoint::getMin);
        minmax.def("getMax", &MinMaxPoint::getMax);
        minmax.add_property("min", &MinMaxPoint::getMin);
        minmax.add_property("max", &MinMaxPoint::getMax);

        minmax.def("getTimestamp", &MinMaxPoint::getTimestamp);
        minmax.def("setTimestamp", &MinMaxPoint::setTimestamp);
        minmax.add_property("timestamp",
                            &MinMaxPoint::getTimestamp,
                            &MinMaxPoint::setTimestamp);

        minmax.def("__eq__", &MinMaxPoint::operator==);
        minmax.def("__lt__", &MinMaxPoint::operator<);
        // FIXME: Add the other comparison operators.
    }

    class_<CandlePoint> candle("CandlePoint", init<>());
    {
        candle.def(init<time_t, double, double, double, double>());
        candle.def("__str__", &to_string<CandlePoint>);
        candle.def("__repr__", CandlePoint__repr__);

        candle.def("clone", &CandlePoint::clone,
                   return_value_policy<copy_non_const_reference>());

        candle.def("getOpen", &CandlePoint::getOpen);
        candle.add_property("open", &CandlePoint::getOpen);
        candle.def("getClose", &CandlePoint::getClose);
        candle.add_property("close", &CandlePoint::getClose);
        candle.def("getMin", &CandlePoint::getMin);
        candle.add_property("min", &CandlePoint::getMin);
        candle.def("getMax", &CandlePoint::getMax);
        candle.add_property("max", &CandlePoint::getMax);

        candle.def("getTimestamp", &CandlePoint::getTimestamp);
        candle.def("setTimestamp", &CandlePoint::setTimestamp);
        candle.add_property("timestamp",
                            &CandlePoint::getTimestamp,
                            &CandlePoint::setTimestamp);

        candle.def("__eq__", &CandlePoint::operator==);
        candle.def("__lt__", &CandlePoint::operator<);
        // FIXME: Add the other comparison operators.
    }

    class_<FXHistoryPoint> histpt("HistoryPoint", init<>());
    scope().attr("FXHistoryPoint") = histpt;
    {
        // Strange constructor (openBid, openAsk, closeBid, closeAsk, maxBix,
        // minBid, maxAsk, minAsk).
        histpt.def(init<time_t,
                   double, double, double, double,
                   double, double, double, double>());

        histpt.def("__str__", &to_string<FXHistoryPoint>);
        histpt.def("__repr__", FXHistoryPoint__repr__);

        // histpt.def(init<String>()); ... we can't access OANDA's String class?
        histpt.def("clone", &FXHistoryPoint::clone,
                   return_value_policy<copy_non_const_reference>());

        histpt.def("__eq__", &FXHistoryPoint::operator==);
        histpt.def("__lt__", &FXHistoryPoint::operator<);
        // FIXME: Add the other comparison operators.

        return_value_policy<copy_const_reference> rvp;
        histpt.def("getOpen", &FXHistoryPoint::getOpenConst, rvp);
        histpt.add_property("open",
                            make_function(&FXHistoryPoint::getOpenConst, rvp));

        histpt.def("getClose", &FXHistoryPoint::getCloseConst, rvp);
        histpt.add_property("close",
                            make_function(&FXHistoryPoint::getCloseConst, rvp));

        histpt.def("getMin", &FXHistoryPoint::getMinConst, rvp);
        histpt.add_property("min",
                            make_function(&FXHistoryPoint::getMinConst, rvp));

        histpt.def("getMax", &FXHistoryPoint::getMaxConst, rvp);
        histpt.add_property("max",
                            make_function(&FXHistoryPoint::getMaxConst, rvp));

        histpt.def("getTimestamp", &FXHistoryPoint::getTimestamp);
        histpt.def("setTimestamp", &FXHistoryPoint::setTimestamp);
        histpt.add_property("timestamp",
                            &FXHistoryPoint::getTimestamp,
                            &FXHistoryPoint::setTimestamp);

        histpt.def("getCandlePoint", &FXHistoryPoint::getCandlePoint);
        histpt.def("getMinMaxPoint", &FXHistoryPoint::getMinMaxPoint);
    }

    class_<FXInstrument> instrument("Instrument", no_init);
    scope().attr("FXInstrument") = instrument;
    {
	// bool operator<<(char *); What is this for?
        instrument.add_property("maxMarginRate", &FXInstrument::maxMarginRate);
        instrument.add_property(
            "pair", make_function(&FXInstrument::pair,
                                  return_value_policy<copy_const_reference>()));
        instrument.add_property("active", &FXInstrument::active);
        instrument.add_property("halted", &FXInstrument::halted);
        instrument.add_property("precision", &FXInstrument::precision);
        instrument.add_property("pipettes", &FXInstrument::pipettes);
        instrument.add_property("id", &FXInstrument::id);
        instrument.add_property("valid", &FXInstrument::valid);
    }

    enum_<long>("INTERVAL")
        .value("INTERVAL_5_SEC",  INTERVAL_5_SEC)
        .value("INTERVAL_10_SEC", INTERVAL_10_SEC)
        .value("INTERVAL_30_SEC", INTERVAL_30_SEC)
        .value("INTERVAL_1_MIN",  INTERVAL_1_MIN)
        .value("INTERVAL_5_MIN",  INTERVAL_5_MIN)
        .value("INTERVAL_15_MIN", INTERVAL_15_MIN)
        .value("INTERVAL_30_MIN", INTERVAL_30_MIN)
        .value("INTERVAL_1_HOUR", INTERVAL_1_HOUR)
        .value("INTERVAL_3_HOUR", INTERVAL_3_HOUR)
        .value("INTERVAL_1_DAY",  INTERVAL_1_DAY);

    class_<RateTable> ratetable("RateTable", no_init);
    {
        ratetable.def("getRate", &RateTable::getRate);

        ratetable.def("getHistory", RateTable__getHistory);
        ratetable.def("getHistory", RateTable__getHistory2);
        // ratetable.def("getHistoryOld", &RateTable::getHistoryOld);

        ratetable.def("getCandles", RateTable__getCandles);

        ratetable.def("getMinMaxs", RateTable__getMinMaxs);

        ratetable.def("findInstrument", RateTable__findInstrument1,
                      return_value_policy<copy_const_reference>());
        ratetable.def("findInstrument", RateTable__findInstrument2,
                      return_value_policy<copy_const_reference>());

        ratetable.def("getLastStreamSequenceNumber",
                      &RateTable::getLastStreamSequenceNumber);

        ratetable.def("getRatesSince", RateTable__getRatesSince);

        ratetable.def("eventManager", &OanPy::RateTable__eventManager);
                      //return_value_policy<manage_new_object>());
    }

}

}

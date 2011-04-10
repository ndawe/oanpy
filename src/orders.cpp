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

// OANDA headers.
#include <Order.h>
#include <EntryOrder.h>
#include <LimitOrder.h>
#include <MarketOrder.h>
#include <StopLossOrder.h>
#include <TakeProfitOrder.h>
#include <Position.h>

// Local headers.
#include "util.h"


using namespace boost::python;
using namespace Oanda;

namespace OanPy {

// Export event-related stuff.
void export_orders()
{
    class_<Order, boost::noncopyable> order("Order", no_init);
    {
        order.def("__eq__", &Order::operator==);
        order.def("__lt__", &Order::operator<);

        order.add_property("orderNumber", &Order::orderNumber);

        int(Order::*order_id)() const = &Order::id;
        order.add_property("id", order_id);

        int(Order::*order_getunits)() const = &Order::units;
        void(Order::*order_setunits)(const int) = &Order::units;
        order.add_property("units", order_getunits, order_setunits);

        double(Order::*order_getprice)() const = &Order::price;
        void(Order::*order_setprice)(const double price) = &Order::price;
        order.add_property("price", order_getprice, order_setprice);

        time_t(Order::*order_gettimestamp)() const = &Order::timestamp;
        order.add_property("timestamp", order_gettimestamp);

        const char*(Order::*order_getbase)() const = &Order::base;
        void(Order::*order_setbase)(const char* base) = &Order::base;
        order.add_property("base", order_getbase, order_setbase);

        const char*(Order::*order_getquote)() const = &Order::quote;
        void(Order::*order_setquote)(const char* quote) = &Order::quote;
        order.add_property("quote", order_getquote, order_setquote);

        order.add_property("pair", &Order::pair);

        double(Order::*order_getlowPriceLimit)() const = &Order::lowPriceLimit;
        void(Order::*order_setlowPriceLimit)(const double lowPriceLimit) = &Order::lowPriceLimit;
        order.add_property("lowPriceLimit", order_getlowPriceLimit, order_setlowPriceLimit);

        double(Order::*order_gethighPriceLimit)() const = &Order::highPriceLimit;
        void(Order::*order_sethighPriceLimit)(const double highPriceLimit) = &Order::highPriceLimit;
        order.add_property("highPriceLimit", order_gethighPriceLimit, order_sethighPriceLimit);
    }


    class_<EntryOrder, bases<Order>, boost::noncopyable> entryorder("EntryOrder", no_init);
    {
        time_t(EntryOrder::*entryorder_getduration)() const = &EntryOrder::duration;
        void(EntryOrder::*entryorder_setduration)(const time_t duration) = &EntryOrder::duration;
        entryorder.add_property("duration", entryorder_getduration, entryorder_setduration);
    }


    class_<LimitOrder, bases<Order> > limitorder("LimitOrder");
    {
        limitorder.def("__str__", &to_string<LimitOrder>);

        limitorder.def_readonly("stopLossOrder", &LimitOrder::stopLossOrder);
        limitorder.def_readonly("takeProfitOrder", &LimitOrder::takeProfitOrder);

        time_t(LimitOrder::*limitorder_getduration)() const = &LimitOrder::duration;
        void(LimitOrder::*limitorder_setduration)(const time_t) = &LimitOrder::duration;
        limitorder.add_property("duration", limitorder_getduration, limitorder_setduration);
    }


    class_<MarketOrder, bases<Order> > marketorder("MarketOrder");
    {
        marketorder.def("__str__", &to_string<MarketOrder>);

        marketorder.def_readonly("stopLossOrder", &MarketOrder::stopLossOrder);
        marketorder.def_readonly("takeProfitOrder", &MarketOrder::takeProfitOrder);

        marketorder.add_property("ticketNumber", &MarketOrder::ticketNumber);
        marketorder.add_property("translink", &MarketOrder::translink);
        marketorder.def("unrealizedPL", &MarketOrder::unrealizedPL);
        marketorder.def("realizedPL", &MarketOrder::realizedPL);

    }


    class_<StopLossOrder, bases<EntryOrder> > slorder("StopLossOrder");
    {
        time_t(StopLossOrder::*slorder_getduration)() const = &StopLossOrder::duration;
        void(StopLossOrder::*slorder_setduration)(const time_t) = &StopLossOrder::duration;
        slorder.add_property("duration", slorder_getduration, slorder_setduration);
    }


    class_<TakeProfitOrder, bases<EntryOrder> > tporder("TakeProfitOrder");
    {
        time_t(TakeProfitOrder::*tporder_getduration)() const = &TakeProfitOrder::duration;
        void(TakeProfitOrder::*tporder_setduration)(const time_t) = &TakeProfitOrder::duration;
        tporder.add_property("duration", tporder_getduration, tporder_setduration);
    }


    class_<Position> position("Position", init<>());
    {
        position.def("__str__", &to_string<Position>);

        position.def(init<const FXPair&>());
        position.def(init<const FXPair&, long, double>());
        position.def("__eq__", &Position::operator==);
        position.def("__lt__", &Position::operator<);

        position.add_property("pair", &Position::pair);
        position.add_property("units", &Position::units);
        position.add_property("price", &Position::price);
        position.def("unrealizedPL", &Position::unrealizedPL);
    }
}

}

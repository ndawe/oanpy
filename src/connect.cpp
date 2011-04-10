//*****************************************************************************/
// Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
// Licensed under the terms of the GNU Lesser General Public License, version 3.
// See http://furius.ca/oanpy/LICENSE for details.
//*****************************************************************************/

// Include precompiled header for Boost.
#include "pchboost.h"

// stdc++ headers.
#include <vector>

// Python headers.
#include "Python.h"

// OANDA headers.
#include <Common.h>
#include <Account.h>
#include <User.h>
#include <FXClient.h>
#include <FXGame.h>
#include <FXTrade.h>

// Local headers.
#include "util.h"
#include "events.h"


using namespace boost::python;
using namespace Oanda;


namespace {

list User__getAccounts( const User& user )
{
    // Note: this is truly inefficient, first copying the std::vector, and then
    // the list.
    std::vector<Account*> accnts = user.getAccounts();
    list res;

    // Converter to create a wrapper without ownership.
    reference_existing_object::apply<Account*>::type conv;

    for (std::vector<Account*>::const_iterator it = accnts.begin();
         it != accnts.end();
         ++it) {
        res.append(handle<>(conv(*it)));
    }
    return res;
}


// This method to circumvent the constness problem with Account::profile().
const char* Account__profile( Account& account )
{
    return const_cast<const char*>(account.profile());
}

// A method that renders and account in a readable way.
std::string Account__str__( Account& acc )
{
    using namespace std;
    ostringstream oss;
    oss << "<Account" 
        << " id=" << acc.accountId() 
        << " name=\"" << acc.accountName() << "\""
        << ">" << ends;
    return oss.str();
}



// typedef void (*LogFunction)(char*, ...);
// 
// template <LogFunction T>
// void simplify_log_function( const char* msg ) {
//     T( const_cast<char*>(msg) );
// }



template <class T>
list vector_to_list( const std::vector<T>& vec ) 
{
    list res;
    typename std::vector<T>::const_iterator it;
    for ( it = vec.begin(); it != vec.end(); ++it ) {
        res.append(*it);
    }
    return res;
}

list Account__getTrades( Account& acc ) 
{
    return vector_to_list( acc.getTrades() );
}

list Account__getOrders( Account& acc ) 
{
    return vector_to_list( acc.getOrders() );
}

list Account__getPositions( Account& acc ) 
{
    return vector_to_list( acc.getPositions() );
}

list Account__getTransactions( Account& acc ) 
{
    return vector_to_list( acc.getTransactions() );
}

list Account__execute_market( Account& acc, MarketOrder& order )
{
    return vector_to_list( acc.execute(order) );
}

}



namespace OanPy {

// Export connection-related stuff.
void export_connect()
{
    enum_<LOGMODE>("LOGMODE")
        .value("NONE", NONE)
        .value("SCREEN", SCREEN)
        .value("DISK", DISK)
        .value("SYSLOG", SYSLOG);

    // class_<Common, boost::noncopyable> common("Common", no_init);
    {
        // common.def("logError", &simplify_log_function<Common::logError>);
        // common.def("logInfo", &simplify_log_function<Common::logInfo>);
        // common.def("logDebug", &simplify_log_function<Common::logDebug>);
        // common.def("logWarning", &simplify_log_function<Common::logWarning>);
        // common.def("log", &Common::log);
        // common.def("setLogMode", &Common::setLogMode);
        // common.def("setLogFilename", &Common::setLogFilename);
    }

    class_<FXClient> client("FXClient");
    {
        client.add_property("version", &FXClient::version);

        client.def("login", &FXClient::login);
        client.def("logout", &FXClient::logout);
        client.def("isLoggedIn", &FXClient::isLoggedIn);

        client.def("setTimeout", &FXClient::setTimeout);
        // client.add_property("timeout", &FXClient::timeout); 
        // (Removed because redundant and confusing.)

        client.def("setLogfile", &FXClient::setLogfile);

        client.def("getWithRateThread", &FXClient::getWithRateThread);
        client.def("setWithRateThread", &FXClient::setWithRateThread);
        client.add_property("withRateThread",
                            &FXClient::getWithRateThread,
                            &FXClient::setWithRateThread);

        client.def("getWithKeepAliveThread", &FXClient::getWithKeepAliveThread);
        client.def("setWithKeepAliveThread", &FXClient::setWithKeepAliveThread);
        client.add_property("withKeepAliveThread",
                            &FXClient::getWithKeepAliveThread,
                            &FXClient::setWithKeepAliveThread);

        client.def("getWithLoadableKey", &FXClient::getWithLoadableKey);
        client.def("setWithLoadableKey", &FXClient::setWithLoadableKey);
        client.add_property("withLoadableKey",
                            &FXClient::getWithLoadableKey,
                            &FXClient::setWithLoadableKey);

        client.def("getServerTime", &FXClient::getServerTime);

        // Note: I'm assuming that we don't have to manage the lifespan of the
        // returned user object here.
        client.def("getUser", &FXClient::getUser,
                   return_value_policy<reference_existing_object>());

        client.def("getRateTable", &FXClient::getRateTable,
                   return_value_policy<reference_existing_object>());

        // We don't need to export this, there are several substitute elsewhere.
        // static DateString timestampToString(time_t stamp)
    }

    class_<FXGame, bases<FXClient> > game("FXGame");
    class_<FXTrade, bases<FXClient> > trade("FXTrade");


    class_<User> user("User", no_init);
    {
        user.add_property("userId", &User::userId);
        user.add_property("createDate", &User::createDate);
        user.add_property("name", &User::name);
        user.add_property("email", &User::email);
        user.add_property("address", &User::address);
        user.add_property("telephone", &User::telephone);

        const char*(User::*user_getprofile)() const = &User::profile;
        void(User::*user_setprofile)(char*) = &User::profile;
        user.add_property("profile", user_getprofile, user_setprofile);

        user.def("getAccounts", User__getAccounts);
        user.def("getAccountWithId", &User::getAccountWithId,
                 return_value_policy<reference_existing_object>());
    }

    class_<Account> account("Account", no_init);
    {
        account.def("__str__", &Account__str__);

        account.add_property("accountId", &Account::accountId);
        account.add_property("accountName", &Account::accountName);
        account.add_property("createDate", &Account::createDate);
        account.add_property("homeCurrency", &Account::homeCurrency);
        account.add_property("marginRate", &Account::marginRate);

        account.add_property("balance", &Account::balance);
        account.def("realizedPL", &Account::realizedPL);
        account.def("unrealizedPL", &Account::unrealizedPL);

        account.def("marginUsed", &Account::marginUsed);
        account.def("marginAvailable", &Account::marginAvailable);

        account.add_property("profile", Account__profile);

        account.def("eventManager", &OanPy::Account__eventManager);
                    // return_value_policy<manage_new_object>());

        // Order execution.
        void (Account::*execute_limit)(LimitOrder& anorder) = &Account::execute;
        account.def("execute", Account__execute_market);
        account.def("execute", execute_limit);

        // Order close.
        MarketOrder (Account::*close_market)(const MarketOrder&) = &Account::close;
        void (Account::*close_limit)(const LimitOrder&) = &Account::close;
        void (Account::*close_position)(const char*) = &Account::close;
        account.def("close", close_market);
        account.def("close", close_limit);
        account.def("close", close_position);

        // Order modify.
        void (Account::*modify_market)(const MarketOrder&) = &Account::modify;
        void (Account::*modify_limit)(const LimitOrder&) = &Account::modify;
        account.def("modify", modify_market);
        account.def("modify", modify_limit);

        // Access to orders and positions.
        account.def("getTrades", Account__getTrades);
        account.def("getTradeWithId", &Account::getTradeWithId);
        
        account.def("getOrders", Account__getOrders);
        account.def("getOrderWithId", &Account::getOrderWithId);

        account.def("getPositions", Account__getPositions);
        account.def("getPosition", &Account::getPosition);

        account.def("getTransactions", Account__getTransactions);
        account.def("getTransactionWithId", &Account::getTransactionWithId);
    }
}

}


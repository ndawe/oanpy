//*****************************************************************************/
// Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
// Licensed under the terms of the GNU Lesser General Public License, version 3.
// See http://furius.ca/oanpy/LICENSE for details.
//*****************************************************************************/

#ifndef OANPY_EVENTS_H
#define OANPY_EVENTS_H

#include <FXEvent.h>
#include <RateTable.h>
#include <Account.h>


namespace OanPy {

using namespace Oanda;

// Use a special custom-wrapper class in order to differentiate between
// account-event-manager and rate-event-manager. This class only exists to allow
// us to check which kind of EventManager instance this is and to throw an
// appropriate exception to help pinpoint the error to the user. If OANDA
// decides to add this improvement to their code (or provide declarations for
// the derived classes derived from FXEventManager) we could do without this and
// expose FXEventManager directly.

struct FXEventManagerWrap 
{
    friend boost::python::list FXEventManagerWrap__events( FXEventManagerWrap& );

    FXEventManagerWrap( FXEventManager* evmgr, FXI_Type type );
    bool add( FXEvent* ev );
    bool remove( FXEvent* ev );

private:
    void checkEventType( FXEvent* ev );

    FXEventManager* _evmgr; // Not owning.
    FXI_Type _type;

};

boost::shared_ptr<FXEventManagerWrap> RateTable__eventManager( RateTable& rtable );
boost::shared_ptr<FXEventManagerWrap> Account__eventManager( Account& rtable );

std::string dump_events();

}

#endif // OANPY_EVENTS_H

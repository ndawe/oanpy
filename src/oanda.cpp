//*****************************************************************************/
// Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
// Licensed under the terms of the GNU Lesser General Public License, version 3.
// See http://furius.ca/oanpy/LICENSE for details.
//*****************************************************************************/

#include <stdlib.h>
#include <python2.5/pyport.h>

PyMODINIT_FUNC init_oanda();

// This function refers to a symbol in our library and thus forces linkage. 
void __tugboat() 
{
    init_oanda();
}


# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
#
# Simple makefile to link together the extension module.

# Replace this variable by the directory where you placed the OANDA API Linux
# C++ libraries which you received from OANDA.
OANDA_API = $(HOME)/q.oanda/oanda-api/cpp-linux


SOURCES = oanda.cpp
TARGET = _oanda.so
TARGETDIR = ../lib/python/oanda
LIBPATH = -L$(OANDA_API) -L.
SYSLIBS = -lnsl -lm -lc -lpthread -ldl -lz -lcrypto -lrt -lexpat -lboost_python -lboost_thread
OURLIBS = -loanpy -lfxclient

default: install

install: $(TARGETDIR)/$(TARGET)

$(TARGET):
	g++ -shared $(SOURCES) $(LIBPATH) $(SYSLIBS) $(OURLIBS) -o $@

$(TARGETDIR)/$(TARGET): $(TARGET)
	cp $< $@

quicktest:
	python -c 'import _oanda'

clean:
	rm -f $(TARGET)
	rm -f $(TARGETDIR)/$(TARGET)

tests:
	py.test

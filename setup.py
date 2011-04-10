#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Script to install oanpy into the standard Python package directory.
"""

import os
from os.path import *
from distutils.core import setup, Extension


# You need to set the path to the directory where you unpacked the API from
# OANDA or set OANDA_API.
##OANDA_API = '/path/to/unpacked/oanda/api/directory'
OANDA_API = os.environ.get('OANDA_API', None)
if not OANDA_API:
    raise RuntimeError("You need to set OANDA_API or configure this file.")


# Install all scripts under bin.
scripts = filter(isfile, [join('bin', x) for x in os.listdir('bin')])

def read_version():
    try:
        return open('VERSION', 'r').readline().strip()
    except IOError, e:
        return '0'


# Include all files without having to create MANIFEST.in
def add_all_files(fun):
    import os, os.path
    from os.path import abspath, dirname, join
    def f(self):
        for root, dirs, files in os.walk('.'):
            if '.hg' in dirs: dirs.remove('.hg')
            self.filelist.extend(join(root[2:], fn) for fn in files
                                 if not fn.endswith('.pyc'))
        return fun(self)
    return f
from distutils.command.sdist import sdist
sdist.add_defaults = add_all_files(sdist.add_defaults)


extmod = Extension('oanda._oanda',
                   ['src/oanda.cpp'],
                   language="c++",
                   library_dirs=['src', OANDA_API],
                   libraries=['nsl', 'm', 'c', 'pthread', 'dl', 'z', 'crypto',
                              'rt', 'expat', 'boost_python', 'boost_thread',
                              'oanpy', 'fxclient'],
                   )

setup(name="oanpy",
      version=read_version(),
      description=\
      "Python bindings for OANDA API",
      long_description="""
Python bindings for the OANDA C++ API.
""",
      license="GNU LGPLv3",
      author="Martin Blais",
      author_email="blais@furius.ca",
      url="http://furius.ca/oanpy",
      package_dir = {'': 'lib/python'},
      packages = ['oanda', 'oanserv'],
      scripts=scripts,
      ext_modules=[extmod]
     )



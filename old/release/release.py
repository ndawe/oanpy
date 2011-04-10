#!/usr/bin/env python
# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Release the OANDA API into a tarball for clients.
There are basically three sensible ways to invoke this script:

  release.py           : Creates a shippable tarball.
  release.py --full    : Creates the tarball and installs the files.
  release.py --partial : Installs the that are present files.

Note: In order to do a proper release, the static library needs to have been
built. This script won't build it.
"""

import os, tempfile, shutil, re, grp
from os.path import *
from subprocess import *
from datetime import datetime
from stat import *



def create_tarball(allow_missing=False):
    """
    Create a tar file of the released files.
    """

    tmpdir = tempfile.mkdtemp(prefix='oanpy.')
    version = datetime.now().strftime('%Y%m%d%H%M')
    base = 'oanpy-%s' % version
    outfn = join(os.environ['HOME'], 'tmp', '%s.tar.gz' % base)
    try:
        outdir = join(tmpdir, base)
        os.mkdir(outdir)
        filelist = [x.strip() for x in open('MANIFEST').xreadlines()
                    if x.strip()]
        copy_filelist(dirname(__file__), outdir, filelist, allow_missing)

        # Clean up garbage files.
        for root, dirs, files in os.walk(outdir):
            for fn in files:
                if re.match('.*\.py[co]$', fn):
                    os.remove(join(root, fn))

        # Generate version number file.
        f = open(join(outdir, 'VERSION'), 'w')
        f.write('%s\n' % version)
        f.close()

        # Make sure the scripts are executable.
        mode = S_IRWXU|S_IRGRP|S_IXGRP|S_IROTH|S_IXOTH
        for exedir in [join(outdir, 'bin')]:
            for fn in os.listdir(exedir):
                os.chmod(join(exedir, fn), mode)

        cmd = ('tar', 'zpcf', outfn, '-C', tmpdir, base)
        print ' '.join(cmd)
        call(cmd, shell=False)
        return outfn
    finally:
        assert tmpdir
        assert exists(tmpdir)
        shutil.rmtree(tmpdir)


def unpack_tarball(fn):
    """
    Create a temporary directory and unpack the tarball in it. Return the name
    of the unpacked directory.
    """
    tmpparent = tempfile.mkdtemp(prefix='oanpytest.')
    call(('tar', 'zpxf', fn), cwd=tmpparent)
    tmpdir = join(tmpparent, os.listdir(tmpparent)[0])
    return tmpdir


def link(dn):
    """
    Link the release files with the OANDA library to produce the .so.
    """
    oanda_api = os.environ.get(
        'OANDA_API', '/home/blais/q.oanda/oanda-api/cpp-linux')
    if not exists(oanda_api):
        raise SystemExit(
            "You need to make the OANDA API visible in order to build.")

    r = call(('make',), cwd=join(dn, 'src'))
    assert r == 0, r
    r = call(('make', 'quicktest'), cwd=join(dn, 'src'))
    assert r == 0, r


def clear_tree_branches(dn, exceptions=[]):
    """
    Remove all the files UNDER directory 'dn', with exceptions.
    """
    for fn in os.listdir(dn):
        if fn in exceptions:
            continue
        else:
            afn = join(dn, fn)
            if isdir(afn):
                shutil.rmtree(afn)
            else:
                os.remove(afn)

    for fn in os.listdir(dn):
        if fn not in exceptions:
            raise RuntimeError(
                "Could not remove all the files in install dir %s." % dn)



def copy_filelist(fromdir, todir, filelist, allow_missing=False):
    """ Copy the list of relative filenames from 'filelist' from 'fromdir' into
    'todir', which is assumed to be an empty tree of files."""
    assert exists(todir)

    for fn in filelist:
        if not fn or isabs(fn):
            continue
        if not exists(fn):
            if allow_missing:
                continue
            else:
                raise SystemExit("Cannot release: file '%s' is missing." % fn)

        srcfn = join(fromdir, fn)
        destfn = join(todir, fn)
        if isdir(srcfn):
            shutil.copytree(srcfn, destfn)
        else:
            dn = dirname(destfn)
            if not exists(dn):
                os.makedirs(dn)
            shutil.copyfile(srcfn, destfn)

def copy_files(fromdir, todir, gid=None):
    """
    Copy all files and directories of 'fromdir' to 'todir', whether or not the
    destination files exist. This simply overwrites the files when necessary,
    and does not delete files which are already there.
    """
    assert exists(fromdir), fromdir
    if not exists(todir):
        os.makedirs(todir)

    for root, dirs, files in os.walk(fromdir):
        relroot = root[len(fromdir)+1:]

        # Make sure the destination exists.
        destdir = join(todir, relroot)
        if not exists(destdir):
            os.makedirs(destdir)

        # Make all subdirectories at the destination.
        for dn in dirs:
            adn = join(destdir, dn)
            if not exists(adn):
                os.makedirs(adn)
                if gid is not None:
                    os.chown(adn, -1, gid)

        for fn in files:
            afn = join(destdir, fn)
            shutil.copyfile(join(root, fn), afn)
            if gid is not None:
                os.chown(afn, -1, gid)




def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip())

    parser.add_option('-d', '--install-directory', action='store',
                      default='/data/fx/oanpy-release',
                      help="The location of the installation directory.")

    parser.add_option('-g', '--group', action='store', dest='gid',
                      help="Group for destination files.")

    parser.add_option('-k', '--allow-missing', action='store_true',
                      help="When creating the package, don't stop on missing files.")

    parser.add_option('-b', '--build', '--link', action='store_true',
                      help="Build the release and run the basic tests.")

    parser.add_option('-c', '--clean', action='store_true',
                      help="Eradicate the previous installation before copying the new files over it.")

    parser.add_option('-i', '--install', '--update', action='store_true',
                      help="Copy the unpackged files in the installation directory.")

    parser.add_option('-x', '--delete', action='store_true',
                      help="Remove the tarball after we're done.")

    parser.add_option('--full', action='store_true',
                      help="Same as -b -c -i")

    parser.add_option('--partial', action='store_true',
                      help="Same as -k -i -x")

    opts, args = parser.parse_args()


    # Process shortcut options.
    if opts.partial and opts.full:
        parser.error("You cannot specify --partial and --full.")
    if opts.partial:
        opts.allow_missing = opts.install = opts.delete = True
    elif opts.full:
        opts.build = opts.clean = opts.install = True

    # Get the group-id.
    if opts.install:
        if opts.gid:
            try:
                _, _, opts.gid, _ = grp.getgrnam(opts.gid)
            except KeyError:
                parser.error("Invalid group name '%s'." % opts.gid)
        else:
            st = os.stat(opts.install_directory)
            opts.gid = st.st_gid

    # Always create a tarball, whether complete or incomplete.
    outfn = create_tarball(allow_missing=opts.allow_missing)
    print
    print
    print "  Package file is in:   %s" % outfn
    print
    print

    if opts.build or opts.install:
        try:
            print 'Unpacking files.'
            tmpdir = unpack_tarball(outfn)

            # Build and link the dso if requested.
            if opts.build:
                print 'Linking.'
                link(tmpdir)

            # If we're doing a full install, we want to make sure we delete the
            # previous files that were present.
            if opts.clean:
                print 'Deleting previous installation.'
                clear_tree_branches(opts.install_directory, '.hg')

            # Copy the new files over the previous hierarchy.
            if opts.install:
                print 'Copying unpacked files.'
                copy_files(tmpdir, opts.install_directory, opts.gid)

        finally:
            print 'Cleaning up.'
            shutil.rmtree(tmpdir)

    if opts.delete:
        print 'Removing tarball.'
        os.remove(outfn)


if __name__ == '__main__':
    main()


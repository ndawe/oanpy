# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
A file object that allows us to seek within the first few blocks of itself. This
is used to process files from stdin without special cases, for example, to
inspect the header and automatically detect the format of a file from stdin.
"""

# stdlib imports
import sys, os


class HeadFile(object):

    def __init__(self, f, headsize=1024):
        self.f = f
        self.headsize = headsize

        # A cache of the beginning bytes of the file.
        self.head = ''
        self.pos = self.realpos = 0

    def __getattr__(self, key):
        return getattr(self.f, key)

    def tell(self):
        return self.pos

    def realread(self, nbytes):
        assert self.realpos < self.headsize, (self.realpos, self.headsize)
        r = self.f.read(nbytes)
        rbytes = len(r)
        ldiff = len(self.head) + rbytes - self.headsize
        self.head += (r[:-ldiff] if ldiff > 0 else r)
        self.realpos += rbytes
        if self.realpos >= self.headsize:
            self.realread = self.realread_nocache
        return r

    def realread_nocache(self, nbytes):
        r = self.f.read(nbytes)
        self.realpos += len(r)
        return r

    def read(self, nbytes):
        lenhead = len(self.head)
        assert self.realpos >= lenhead, "Invariant failed."
        if self.pos == self.realpos:
            r = self.realread(nbytes)
            self.pos += len(r)
        else:
            assert self.pos < self.realpos, (self.pos, self.realpos)
            beg = self.pos
            end = beg + nbytes
            if end > self.headsize:
                raise OSError("Head overflow of non-seekable file.")
            if end > lenhead:
                # Make sure we read all needed unread bytes.
                ebytes = lenhead - end
                self.realread(ebytes)
            # Return the part of the cache we need to read.
            r = self.head[beg:end]
            self.pos += len(r)
        return r

    def seek(self, offset, whence=os.SEEK_SET):
        if (whence != os.SEEK_SET or
            (offset > len(self.head) and offset != self.realpos)): 
            trace(offset, len(self.head), self.realpos)
            raise OSError("File is not seekable.")
        else:
            assert offset <= len(self.head) or offset == self.realpos
            self.pos = offset



def test():
    "Cat a file larger than 2048 bytes in stdin and this should succeed."

    f = HeadFile(sys.stdin, 1024)

    f.seek(0)
    b1 = f.read(128)
    f.seek(0)
    b2 = f.read(128)
    assert b1 == b2, (b1, b2)
    f.read(2048)
    f.seek(1000)
    f.seek(2048+128)
    f.read(128)
    f.seek(1024)
    f.read(10)
    

if __name__ == '__main__':
    test()



# Copyright (C) 2009  Furius Enterprise / 6114750 Canada Inc.
# Licensed under the terms of the GNU Lesser General Public License, version 3.
# See http://furius.ca/oanpy/LICENSE for details.
"""
Support for encoding/decoding simple line-based Twisted protocols.

This module provides a base class for protocols with methods that can be called
to encode and send specific messages (on the client) and code that automatically
decodes and dispatches the received messages (on the server). A description for
the protocol format is provided in the form of a class with attributes, to
describe the set of messages that can be transmitted from client to server and
the layout on the line (see test program below for examples).

(P.S. This module is named 'texan' in honor of Raymond Hettinger.)
"""

# stdlib imports
import sys, re, logging, StringIO

# twisted imports
from twisted.protocols.basic import LineOnlyReceiver



class TexanError(RuntimeError):
    "Error in encoding of the protocol messages."


def get_protodef_messages(protodef):
    "Yield the list of messages defined on a protocol definition class."
    assert isinstance(protodef, object), repr(protodef)
    for aname, avalue in protodef.__dict__.iteritems():
        if re.match('^__.*__$', aname):
            continue
        yield aname, avalue


def convert_unicode(args, encoding='ascii'):
    "Convert all the unicode objects in a list to encoded strings."
    nargs = []
    for arg in args:
        if isinstance(arg, unicode):
            arg = str(arg)
        nargs.append(arg)
    if isinstance(args, tuple):
        nargs = tuple(nargs)
    return nargs


class TexanSendFunction(object):

    def __init__(self, proto, fname, sdata):
        self.proto = proto
        self.fname = fname
        self.pat, self.nbargs, self.slen = sdata

    def __call__(self, *args):
        if len(args) != self.nbargs:
            raise TypeError("%s() takes exactly %d arguments (%d given)" %
                            (self.fname, self.nbargs, len(args)))

        # Don't allow unicode strings for now, convert to strings on-the-fly.
        args = convert_unicode(args)
            
        try:
            msg = self.pat % args
            if len(msg) != self.slen+1:
                print >> sys.stderr, msg, len(msg), self.slen, repr(self.pat)
                raise OverflowError("%s() could not be encoded in %s bytes: %s." %
                                    (self.fname, self.slen, repr(msg)))
            self.proto.sendLine(msg)
        except TypeError, e:
            raise TypeError('%s. pattern = %s, args = %s' % (e, self.pat, args))


class TexanProtocol(LineOnlyReceiver, object):

    __conform__ = None

    delimiter = '\n'

    # A list of class protocol definitions that we can call from this object.
    send_protodefs = []

    # A list of class protocol definitions that get dispatched from this object.
    recv_protodefs = []

    def __init__(self):
        self.send_table = {}
        self.recv_table = {}

        msgnames = set()
        for protodef in self.send_protodefs:
            for aname, (acode, doc, adesc) in get_protodef_messages(protodef):

                if aname in msgnames:
                    raise TexanError("Collision in protocol names: %s" % aname)

                # Initialize an encoding pattern.
                patlist = [acode]
                totlen = 0
                for varname, vartype, varlen in adesc:
                    totlen += varlen
                    if vartype is str:
                        patlist.append('%%-%ds' % varlen)
                    elif vartype is int:
                        patlist.append('%%%dd' % varlen)
                pat = ''.join(patlist)

                self.send_table[aname] = pat, len(adesc), totlen

        msgnames = set(self.send_table.iterkeys())
        for protodef in self.recv_protodefs:
            for aname, (acode, doc, adesc) in get_protodef_messages(protodef):
                totlen = sum(x[2] for x in adesc) + 1
                self.recv_table[ord(acode)] = (aname, adesc, totlen)

                if aname in msgnames:
                    raise TexanError("Collision in protocol names: %s" % aname)

    def __getattr__(self, key):
        try:
            sdata = self.send_table[key]
        except KeyError:
            raise
        else:
            return TexanSendFunction(self, key, sdata)

    def lineReceived(self, line):
        line = line.rstrip('\r\n') # For possible \r with telnet.
        if not line:
            logging.warning("Ignoring empty line.")
            return

        c = 0
        try:
            msgname, msgdef, msglen = self.recv_table[ord(line[c])]
            c += 1
        except KeyError:
            logging.error("Unknown message: %s" % repr(line))
            return
        if len(line) < msglen:
            logging.warning("Invalid message length, expecting %s, got %s: %s; padding." %
                            (msglen, len(line), repr(line)))
            line = line + ' '*(msglen-len(line))
        elif len(line) > msglen:
            logging.error("Invalid message length, expecting %s, got %s: %s; failing." %
                            (msglen, len(line), repr(line)))
            return
        
        args = []
        for varname, vartype, varlen in msgdef:
            r = line[c:c+varlen]
            if r == '':
                logging.error("Incomplete message: %s" % repr(line))
                return
            c += varlen

            if vartype is str:
                pass
            elif vartype is int:
                r = int(r)
            args.append(r)
        args = tuple(args)

        do_default = 0
        if do_default:
            try:
                meth = getattr(self.__class__, msgname)
                meth(self, *args)
            except AttributeError, e:
                self.default(msgname, args)
        else:
            meth = getattr(self.__class__, msgname)
            meth(self, *args)


    def default(self, msgname, args):
        raise NotImplementedError('Method %s not implemented on %s.' %
                                  (msgname, self.__class__))

    def linehelp(self, linefun):
        """ Generate online help for the accepted protocol by calling the
        function 'linefun' to output each line to the client."""
        for proto in self.recv_protodefs:
            for line in gen_linehelp(proto):
                linefun(line)


def gen_linehelp(proto):
    """ Return a user-printable protocol reference that is meant to be
    printed at the telnet protocol, a list of str lines, each less than 80
    chars in length."""
    lines = []
    lines.append(" Protocol: %s" % proto.__name__)
    lines.append("")
    for aname, (acode, doc, adesc) in get_protodef_messages(proto):
        m = [acode]
        for pname, ptype, plen in adesc:
            m.append('<%s>' % pname)
        lines.append("   '%s'" % ' '.join(m))
        lines.append('       %s: %s' % (aname, doc))
        lines.append('')
    return lines



_html_pre = '''\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html>
  <head>
    <title>Protocol: %s</title>
    <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
    <style>

table {
  border-collapse: collapse;
  width: 100%%;
}

th {
  background-color: #EEE;
}

td {
  border: thin solid black;
  padding-left: 1em;
  padding-right: 1em;
}

td.code {
  font-weight: bold;
}

td.empty {
  background-color: #CCC;
}
    </style>
  </head>
  <body>

'''

_html_post = '''
  </body>
</html>
'''

def texan2html(protodefs):
    """ Generate HTML output (a string) to document the given protocol
    definition. This function can be used to generate documentation for
    protocols."""
    assert isinstance(protodefs, (tuple, list))
    out = StringIO.StringIO()
    wri = lambda x: out.write(x + '\n')
    
    if len(protodefs) == 1:
        title = protodefs[0].__name__
    else:
        title = "Protocols"
    wri(_html_pre % title)

    for protodef in protodefs:
        wri('<h1>%s</h1>' % 'Protocol %s' % protodef.__name__) 
        if protodef.__doc__:
            wri('<p>%s</p>' % protodef.__doc__)

        wri('<table>')
        wri('<thead><tr>')
        wri('<th class="name">%s</th>' % 'Message')
        wri('<th class="code">%s</th>' % 'Code')
        wri('<th class="format">%s</th>' % 'Description/Arguments')
        ## wri('<th class="doc">%s</th>' % 'Description')
        wri('</tr></thead>')

        for aname, (acode, doc, adesc) in get_protodef_messages(protodef):
            desc = []
            for pname, ptype, plen in adesc:
                desc.append('<span class="param"><b>%s%d</b> %s</span>' %
                            (ptype.__name__, plen, pname))
            wri('<tr>')
            wri('<td class="name">%s</td>' % aname)
            wri('<td class="code">%s</td>' % acode)
            wri('<td class="doc">%s</td>' % str(doc))
            wri('</tr>')
            wri('<tr>')
            wri('<td colspan="2" class="empty"></td>')
            wri('<td class="format">( %s )</td>' % ', '.join(desc))
            wri('</tr>')

        wri('</table>')

    wri(_html_post)
    return out.getvalue()



def test():

    import time

    class RegProtoDef(object):
        """ A simple protocol to register for rates streaming. """

        subscribe = ('S', "Subscribe for notifications on a specific instrument.",
                     [ ('instrument', str, 8) ])

        unsubscribe = ('U', "Remove a subscription to a specific instrument.",
                       [ ('instrument', str, 8) ])

        subscribe_all = ('A', "Susbcribe globally to all instruments.",
                         [])

        unsubscribe_all = ('Z', "Remove subscriptions (global and specific).",
                           [])

    class TickProtoDef(object):
        """ A simple protocol that provides updates for specific instruments. """

        rate = ('R', "Rate notification.",
                [ ('instrument', str, 8),
                  ('bid', int, 12),
                  ('ask', int, 12),
                  ('timestamp', int, 12)])

    class FakeProtocol(object):
        "A kludge to avoid using the network while testing."

        def sendLine(self, line):
            print 'DATA: %s' % line
            self.other.lineReceived(line)

        def default(self, msgname, args):
            print 'Callback: %s%s' % (msgname, args)

    class TestReceiver(FakeProtocol, TexanProtocol):

        send_protodefs = [TickProtoDef]
        recv_protodefs = [RegProtoDef]

        def subscribe(self, instrument):
            trace('subscribe instrument', instrument)

    class TestSender(FakeProtocol, TexanProtocol):

        send_protodefs = [RegProtoDef]
        recv_protodefs = [TickProtoDef]

    # Create protocols and connect them together.
    receiver = TestReceiver()
    sender = TestSender()
    receiver.other = sender
    sender.other = receiver

    # Call some methods on the sender.
    sender.subscribe('XAU/USD')
    sender.unsubscribe('XAU/USD')

    # Call some methods on the receiver.
    DIV = 10**8
    receiver.rate('XAU/USD', 17.1 * DIV, 17.2 * DIV, time.time())


    doc = texan2html(TickProtoDef)
    open('/tmp/texan.html', 'w').write(doc)
    print doc

if __name__ == '__main__':
    test()


#! /usr/bin/env python

import sys
import types
import string
import socket
import getopt


import erl_term
import erl_node
import erl_opts
import erl_common
import erl_eventhandler


mb = None

def __TestMBoxCallback(msg, *k, **kw):
    global mb
    print "Incoming msg=%s (k=%s, kw=%s)" % (`msg`, `k`, `kw`)
    if type(msg) == types.TupleType:
        if len(msg) == 2:
            if erl_term.IsErlPid(msg[0]):
                dest = msg[0]
                print "Sending it back to %s" % (dest,)
                mb.Send(dest, msg)
                


def main(argv):
    global mb
    
    try:
        opts, args = getopt.getopt(argv[1:], "?dn:c:")
    except getopt.error, info:
        print info
        sys.exit(1)

    hostName = "localhost"
    ownNodeName = "py_interface_test"
    cookie = "cookie"
    doDebug = 0

    for (optchar, optarg) in opts:
        if optchar == "-?":
            print "Usage: %s erlnode" % argv[0]
            sys.exit(1)
        elif optchar == "-c":
            cookie = optarg
        elif optchar == "-d":
            doDebug = 1
        elif optchar == "-n":
            ownNodeName = optarg


    if doDebug:
        erl_common.DebugOnAll()

    print "Creating node..."
    n = erl_node.ErlNode(ownNodeName, erl_opts.ErlNodeOpts(cookie=cookie))
    print "Publishing node..."
    n.Publish()
    print "Creating mbox..."
    mb = n.CreateMBox(None)
    m = n.CreateMBox(__TestMBoxCallback)
    print "Registering mbox as p..."
    m.RegisterName("p")

    print "Looping..."
    evhand = erl_eventhandler.GetEventHandler()
    evhand.Loop()

try:
    main(sys.argv)
except KeyboardInterrupt:
    print "Interrupted. Exiting."
    sys.exit(1)

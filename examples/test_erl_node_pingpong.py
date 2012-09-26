#! /usr/bin/env python

## A test case for testing packing/unpacking of erlang-terms:
##
## See run_test_erl_node_pingpong.sh for how to run it.
##
## A message is sent from an erlang node to a python node.
## That message is echoed back to the erlang node, which checks
## if the received message matches the original message.
##

import sys
import types
import string
import socket
import getopt


from py_interface import erl_term
from py_interface import erl_node
from py_interface import erl_opts
from py_interface import erl_common
from py_interface import erl_eventhandler

mb = None
quiet = False

def ExprRebuildAtoms(expr):
    if type(expr) == types.StringType:
        if len(expr) >= 2 and expr[0] == expr[-1] == "'":
            atomText = expr[1:-1]
            return erl_term.ErlAtom(atomText)
        else:
            return expr
    elif type(expr) == types.ListType:
        rebuiltList = []
        for elem in expr:
            rebuiltElem = ExprRebuildAtoms(elem)
            rebuiltList.append(rebuiltElem)
        return rebuiltList
    elif type(expr) == types.TupleType:
        rebuiltList = []
        for elem in list(expr):
            rebuiltElem = ExprRebuildAtoms(elem)
            rebuiltList.append(rebuiltElem)
        return tuple(rebuiltList)
    else:
        return expr

def _TestMBoxRPCResponse(msg):
    print "RPC answer: %s" % `msg`

def process_protocol(data,node,socket_id):
    print data,node,socket_id
    fargs = [node,socket_id,data]
    global mb
    mb.SendRPC(node, "ss_socket_agent", 'forward', map(lambda x: ExprRebuildAtoms(x),fargs), _TestMBoxRPCResponse)


    
def __TestMBoxCallback(msg, *k, **kw):
    global mb, quiet
    if not quiet:
        print "Incoming msg=%s (k=%s, kw=%s)" % (`msg`, `k`, `kw`)
    data = msg[0].contents
    node = msg[1].atomText
    socket_id = msg[2].contents

    process_protocol(data,node,socket_id)

     

    if type(msg) == types.TupleType:
        if len(msg) == 2:
            if erl_term.IsErlPid(msg[0]):
                dest = msg[0]
                if not quiet:
                    print "Sending it back to %s" % (dest,)
                mb.Send(dest, msg)
                


def main(argv):
    global mb, quiet
    
    try:
        opts, args = getopt.getopt(argv[1:], "?dn:c:q")
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
        elif optchar == "-q":
            quiet = 1
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

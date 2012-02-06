#!/usr/bin/env python
import sys, os, select
from hashlib import *
from socket import *
readable=select.select

hubsocket=(sys.argv[1])
os.chdir(sys.argv[2])

peersock=str(os.getpid())
peer=socket(AF_UNIX,SOCK_DGRAM)

try:
    os.remove(peersock)
except:
    pass

peer.bind(peersock)
peer.setblocking(0)
peer.connect(hubsocket)
peerfd=peer.fileno()

while 1:
    read_this=readable([6,peerfd],[],[],1)[0]
    if read_this!=[]:
        if 6 in read_this:
            peer_packet=os.read(6,65536)
            if not peer_packet:
                break
            peer.sendto(peer_packet,hubsocket)
        if peerfd in read_this:
            hub_packet=peer.recv(65536)
            if not hub_packet:
                break
            os.write(7,hub_packet)

os.remove(peersock)

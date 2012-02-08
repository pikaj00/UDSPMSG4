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
peer.connect(hubsocket)
peerfd=peer.fileno()

while 1:
    proto_error=0
    read_this=readable([6,peerfd],[],[],1)[0]
    if read_this!=[]:
        if 6 in read_this:
            try:
                peer_packet=os.read(6,2)
                packet_length=(ord(peer_packet[:1:])*256)+ord(peer_packet[1:2:])
                while peer_packet!=packet_length:
                    peer_packet+=os.read(6,packet_length-peer_packet)
                    if not peer_packet:
                        os.remove(peersock)
                        break
            except:
                os.write(2,'error: udpmsg4 protocol error\n')
                proto_error=1

            if proto_error==0:
                if not peer_packet:
                    os.remove(peersock)
                    break
                packet_length=len(peer_packet)
                try:
                    write_length=peer.sendto(peer_packet,hubsocket)
                    if write_length!=packet_length:
                        os.write(2,'error: write_length == '+str(write_length)+', packet_length == '+str(packet_length)+'\n')
                except:
                    os.write(2,'error: cannot write to '+hubsocket+'\n')

        if peerfd in read_this:
            hub_packet=peer.recv(65536)
            hub_packet=chr(int(round(len(hub_packet)/256)))+chr(int(round(len(hub_packet)%256)))+hub_packet
            if not hub_packet:
                os.remove(peersock)
                break
            packet_length=len(hub_packet)
            try:
                write_length=os.write(7,hub_packet)
                if write_length!=packet_length:
                    os.write(2,'error: write_length == '+str(write_length)+', packet_length == '+str(packet_length)+'\n')
            except:
                os.write(2,'error: cannot write to '+peersock+'\n')

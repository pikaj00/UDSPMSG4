#!/usr/bin/env python
import sys, os, select
from hashlib import *
#from socket import *
import socket
readable=select.select

hubsocket=(sys.argv[1])
pid=str(os.getpid())
peersock=sys.argv[2]+'/'+pid
peer=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)

try:
    os.remove(peersock)
except:
    pass

peer.bind(peersock)
#peer.connect(hubsocket)
peerfd=peer.fileno()

toremote=''
while 1:
    os.write(2,'peer.py '+pid+' toremote length == '+str(len(toremote))+'\n')
#    sockets=readable([6,peerfd],[7,peerfd],[],1)
#    read_this=sockets[0]
#    write_this=sockets[1]
    read_this=readable([6,peerfd],[],[])[0]
    write_this=readable([],[7,peerfd],[])[1]
    if read_this!=[]:
        if 6 in read_this:
            try:
                peer_packet=os.read(6,2)
                packet_length=(ord(peer_packet[:1:])*256)+ord(peer_packet[1:2:])
                peer_packet=''
                while len(peer_packet)!=packet_length:
                    peer_packet+=os.read(6,packet_length-len(peer_packet))
                    if not peer_packet:
                        os.remove(peersock)
                        break
            except:
                os.write(2,'error: udpmsg4 protocol error\n')
                os.remove(peersock)
                break

            if not peer_packet:
                os.remove(peersock)
                break
            try:
                write_length=0
                packet_length=len(peer_packet)
#                write_this=readable([],[7,peerfd],[])[1]
#                if peerfd in write_this:
                write_length=peer.sendto(peer_packet[write_length::],hubsocket)
            except socket.error, ex:
                os.write(2,'peer.py '+pid+' error: cannot write to '+hubsocket+' '+str(ex.errno)+'\n')

        if peerfd in read_this:
            hub_packet=peer.recv(65536)
            hub_packet=chr(int(round(len(hub_packet)/256)))+chr(int(round(len(hub_packet)%256)))+hub_packet
            if not hub_packet:
                os.remove(peersock)
                break
            try:
                toremote+=hub_packet
                write_length=0
                packet_length=len(toremote)
                while write_length!=packet_length:
                    write_this=readable([],[7],[])[1]
                    if 7 in write_this:
                        try:
                            write_length=os.write(7,toremote)
                        except socket.error, ex:
                            if ex.errno == 104:
                                os.remove(peersock)
                                break
                        if write_length>0:
                            toremote=toremote[write_length::]
                            packet_length=len(toremote)
            except socket.error, ex:
                os.write(2,'peer.py '+pid+' error: cannot write to '+peersock+' '+str(ex.errno)+'\n')
                os.remove(peersock)
                break
    os.write(2,'peer.py '+pid+' reads '+str(len(read_this))+' writes '+str(len(write_this))+'\n')

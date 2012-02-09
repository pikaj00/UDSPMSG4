#!/usr/bin/env python
import sys, os, select
from hashlib import *
#from socket import *
import socket
readable=select.select

pathhub=(sys.argv[1])
pid=str(os.getpid())
os.write(2,'stream.py '+pid+' starting\n')
pathclient=sys.argv[2]+'/'+pid
client=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)

try:
    os.remove(pathclient)
except:
    pass

client.bind(pathclient)
#client.connect(pathhub)
clientfd=client.fileno()

toremote=''
fromremote=''
while 1:
    os.write(2,'stream.py '+pid+' toremote length == '+str(len(toremote))+'\n')
#    sockets=readable([6,peerfd],[7,clientfd],[],1)
#    read_this=sockets[0]
#    write_this=sockets[1]
    read_this=readable([0,clientfd],[],[],1)[0]
    write_this=readable([],[1,clientfd],[],1)[1]
    os.write(2,'stream.py '+pid+' start loop reads '+str(len(read_this))+' writes '+str(len(write_this))+'\n')
    if read_this!=[]:
        if 0 in read_this:
            try:
                client_packet=os.read(0,4096)
                if not client_packet:
                    os.remove(pathclient)
                    break
                fromremote+=client_packet
            except:
                os.write(2,'error: udpmsg4 protocol error\n')
                os.remove(pathclient)
                break
            packet_length=(ord(fromremote[:1:])*256)+ord(fromremote[1:2:])
            while len(fromremote)>=2+packet_length:
                fromremote=fromremote[2::]
                client_packet=fromremote[:packet_length:]
                fromremote=fromremote[packet_length::]
                try:
                    packet_length=len(client_packet)
                    write_length=client.sendto(client_packet,pathhub)
                except socket.error, ex:
                    os.write(2,'client.py '+pid+' error: cannot write to '+pathhub+' '+str(ex.errno)+'\n')
                packet_length=(ord(fromremote[:1:])*256)+ord(fromremote[1:2:])

        if clientfd in read_this:
            hub_packet=client.recv(65536)
            hub_packet=chr(int(round(len(hub_packet)/256)))+chr(int(round(len(hub_packet)%256)))+hub_packet
            if not hub_packet:
                os.remove(pathclient)
                break
            try:
                toremote+=hub_packet
                write_length=0
                packet_length=len(toremote)
                while write_length!=packet_length:
                    write_this=readable([],[1],[])[1]
                    if 1 in write_this:
                        try:
                            write_length=os.write(1,toremote)
                        except socket.error, ex:
                            if ex.errno == 104:
                                os.remove(pathclient)
                                break
                        if write_length>0:
                            toremote=toremote[write_length::]
                            packet_length=len(toremote)
            except socket.error, ex:
                os.write(2,'stream.py '+pid+' error: cannot write to '+pathclient+' '+str(ex.errno)+'\n')
                os.remove(pathclient)
                break
    os.write(2,'peer.py '+pid+' end loop reads '+str(len(read_this))+' writes '+str(len(write_this))+'\n')

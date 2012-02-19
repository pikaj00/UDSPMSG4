#!/usr/bin/env python
import sys, os, select
from hashlib import *
#from socket import *
import socket
readable=select.select

pathhub=(sys.argv[1])
pid=str(os.getpid())
os.write(2,'stream.py '+pid+' starting '+os.getenv('TCPREMOTEIP')+':'+os.getenv('TCPREMOTEPORT')+'\n')
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
    os.write(2,'stream.py '+pid+' start poll for read\n')
    read_this=readable([0,clientfd],[],[],1)[0]
    readables=''
    for readabless in read_this:
        readables+=str(readabless)+','
    os.write(2,'stream.py '+pid+' end poll for read '+str(len(readables))+'['+readables+']\n')
    os.write(2,'stream.py '+pid+' start poll for write\n')
    write_this=readable([],[1,clientfd],[],0)[1]
    os.write(2,'stream.py '+pid+' end poll for write\n')
    os.write(2,'stream.py '+pid+' start loop reads '+str(len(read_this))+' writes '+str(len(write_this))+'\n')
    if read_this!=[]:
        if clientfd in read_this:
            os.write(2,'stream.py '+pid+' reading from clientfd\n')
            hub_packet=client.recv(65536)
            hub_packet=chr(int(round(len(hub_packet)/256)))+chr(int(round(len(hub_packet)%256)))+hub_packet
            if not hub_packet:
                os.write(2,'stream.py '+pid+' connection closed from remote\n')
                os.remove(pathclient)
                break

            toremote+=hub_packet
            write_length=0
            packet_length=len(toremote)
            if packet_length==0:
                os.write(2,'stream.py '+pid+' connection closed from remote\n')
                os.remove(pathclient)
                break
            try:
                while write_length!=packet_length:
                    os.write(2,'stream.py '+pid+' try to write '+str(packet_length)+'\n')
                    os.write(2,'stream.py '+pid+' in loop start poll for write\n')
                    write_this=readable([],[1],[],0)[1]
                    os.write(2,'stream.py '+pid+' in loop end poll for write '+str(len(write_this))+' writables\n')
                    if len(write_this)==0:
                        os.write(2,'stream.py '+pid+' in loop end poll no writables\n')
                        break
                    if 1 in write_this:
                        try:
                            os.write(2,'stream.py '+pid+' in loop start write\n')
                            write_length=os.write(1,toremote)
                            os.write(2,'stream.py '+pid+' in loop end write\n')
                        except os.error, ex:
                            if ex.errno == 104:
                                os.write(2,'stream.py '+pid+' connection closed from remote\n')
                                os.remove(pathclient)
                                break
                        if write_length>0:
                            toremote=toremote[write_length::]
                            packet_length=len(toremote)
                        else:
                            if len(toremote)>0:
                                os.write(2,'stream.py '+pid+' zero length write\n')
                                os.remove(pathclient)
                                break
            except socket.error, ex:
                os.write(2,'stream.py '+pid+' error: cannot write to '+pathclient+' '+str(ex.errno)+'\n')
                os.remove(pathclient)
                break

        if 0 in read_this:
            os.write(2,'stream.py '+pid+' reading from stdin\n')
            try:
                os.write(2,'stream.py '+pid+' start read\n')
                client_packet=os.read(0,4096)
                os.write(2,'stream.py '+pid+' end read\n')
                if not client_packet:
                    os.remove(pathclient)
                    break
                fromremote+=client_packet
            except os.error, ex:
                os.write(2,'stream.py '+pid+' error: udpmsg4 protocol error '+str(ex.errno)+'\n')
                try:
                    os.remove(pathclient)
                except:
                    break
                break
            if len(fromremote)>=2:
                packet_length=(ord(fromremote[:1:])*256)+ord(fromremote[1:2:])
            else:
                packet_length=0
            while len(fromremote)>=2+packet_length:
                fromremote=fromremote[2::]
                client_packet=fromremote[:packet_length:]
                fromremote=fromremote[packet_length::]
                try:
                    packet_length=len(client_packet)
                    os.write(2,'stream.py '+pid+' start write to hub\n')
                    write_length=client.sendto(client_packet,pathhub)
                    os.write(2,'stream.py '+pid+' end write to hub\n')
                except socket.error, ex:
                    os.write(2,'client.py '+pid+' error: cannot write to '+pathhub+' '+str(ex.errno)+'\n')
                if len(fromremote)>=2:
                    packet_length=(ord(fromremote[:1:])*256)+ord(fromremote[1:2:])
                else:
                    packet_length=0
    os.write(2,'stream.py '+pid+' end loop reads '+str(len(read_this))+' writes '+str(len(write_this))+'\n')

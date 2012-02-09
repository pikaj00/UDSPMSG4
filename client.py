#!/usr/bin/env python
import sys, os, select
from hashlib import *
#from socket import *
import socket
readable=select.select

hubsocket=(sys.argv[1])
#os.chdir(sys.argv[2])

pid=str(os.getpid())
os.write(2,'client.py '+pid+' starting\n')
clientsock=sys.argv[2]+'/'+pid
client=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)

try:
    os.remove(clientsock)
except:
    pass

client.bind(clientsock)
#client.connect(hubsocket)
clientfd=client.fileno()

toremote=''
while 1:
    os.write(2,'client.py '+pid+' toremote length == '+str(len(toremote))+'\n')
    proto_error=0
#    read_this=readable([0,clientfd],[],[],1)[0]
    read_this=readable([0,clientfd],[],[],1)[0]
    write_this=readable([],[1,clientfd],[],1)[1]
    os.write(2,'client.py '+pid+' reads '+str(len(read_this))+' writes '+str(len(write_this))+'\n')
    if read_this!=[]:

        if 0 in read_this:
            try:
                client_packet=os.read(0,2)
                packet_length=(ord(client_packet[:1:])*256)+ord(client_packet[1:2:])
                client_packet=''
                while len(client_packet)!=packet_length:
                    client_packet+=os.read(0,packet_length-len(client_packet))
                    if not client_packet:
                        os.remove(clientsock)
                        break
            except:
                os.write(2,'error: udpmsg4 protocol error\n')
                proto_error=1
                os.remove(clientsock)
                break

            if proto_error==0:
                if not client_packet:
                    os.remove(clientsock)
                    break
                try:
                    write_length=0
                    packet_length=len(client_packet)
                    if clientfd in write_this:
                        while write_length!=packet_length:
                            write_length=client.sendto(client_packet[write_length::],hubsocket)
                except socket.error, ex:
                    os.write(2,'client.py '+pid+' error: cannot write to '+hubsocket+' '+str(ex.errno)+'\n')

        if clientfd in read_this:
            hub_packet=client.recv(65536)
            hub_packet=chr(int(round(len(hub_packet)/256)))+chr(int(round(len(hub_packet)%256)))+hub_packet
            if not hub_packet:
                os.remove(clientsock)
                break
            try:
                toremote+=hub_packet
                write_length=0
                packet_length=len(toremote)
                while write_length!=packet_length:
                    if 1 in write_this:
                        write_length=os.write(1,toremote)
                        if write_length>0:
                            toremote=toremote[write_length::]
                            packet_length=len(toremote)
            except socket.error, ex:
                os.write(2,'client.py '+pid+' error: cannot write to '+clientsock+' '+str(ex.errno)+'\n')
                os.remove(clientsock)
                break

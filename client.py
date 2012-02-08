#!/usr/bin/env python
import sys, os, select
from hashlib import *
from socket import *
readable=select.select

hubsocket=(sys.argv[1])
os.chdir(sys.argv[2])

clientsock=str(os.getpid())
client=socket(AF_UNIX,SOCK_DGRAM)

try:
    os.remove(clientsock)
except:
    pass

client.bind(clientsock)
client.connect(hubsocket)
clientfd=client.fileno()

while 1:
    proto_error=0
    read_this=readable([0,clientfd],[],[],1)[0]
    if read_this!=[]:

        if 0 in read_this:
            try:
                client_packet=os.read(0,2)
                packet_length=(ord(client_packet[:1:])*256)+ord(client_packet[1:2:])
                while client_packet!=packet_length:
                    client_packet+=os.read(0,packet_length-client_packet)
                    if not client_packet:
                        os.remove(clientsock)
                        break
            except:
                os.write(2,'error: udpmsg4 protocol error\n')
                proto_error=1

            if proto_error==0:
                if not client_packet:
                    os.remove(clientsock)
                    break
                packet_length=len(client_packet)
                try:
                    write_length=client.sendto(client_packet,hubsocket)
                    if write_length!=packet_length:
                        os.write(2,'error: write_length == '+str(write_length)+', packet_length == '+str(packet_length)+'\n')
                except:
                    os.write(2,'error: cannot write to '+hubsocket+'\n')

        if clientfd in read_this:
            hub_packet=client.recv(65536)
            hub_packet=chr(int(round(len(hub_packet)/256)))+chr(int(round(len(hub_packet)%256)))+hub_packet
            if not hub_packet:
                os.remove(clientsock)
                break
            packet_length=len(hub_packet)
            try:
                write_length=os.write(1,hub_packet)
                if write_length!=packet_length:
                    os.write(2,'error: write_length == '+str(write_length)+', packet_length == '+str(packet_length)+'\n')
            except:
                os.write(2,'error: cannot write to '+clientsock+'\n')

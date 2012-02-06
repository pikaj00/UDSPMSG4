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
client.setblocking(0)
client.connect(hubsocket)
clientfd=client.fileno()

while 1:
    read_this=readable([0,clientfd],[],[],1)[0]
    if read_this!=[]:
        if 0 in read_this:
            client_packet=os.read(0,65536)
            if not client_packet:
                break
            client.sendto(client_packet,hubsocket)
        if clientfd in read_this:
            hub_packet=client.recv(65536)
            if not hub_packet:
                break
            os.write(1,hub_packet)

os.remove(clientsock)

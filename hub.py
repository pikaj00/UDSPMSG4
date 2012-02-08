#!/usr/bin/env python
import sys, os, select
from hashlib import *
from socket import *
readable=select.select

sys.dont_write_bytecode=True
import udpmsg4

hubsock=(sys.argv[1])
remotesockdir=sys.argv[2]
hub=socket(AF_UNIX,SOCK_DGRAM)
try:
    hub.bind(hubsock)
except:
    os.remove(hubsock)
    hub.bind(hubsock)
hub.setblocking(0)
hubfd=hub.fileno()

md5cache=[]
while 1:
    read_this=readable([hubfd],[],[],1)[0]
    if hubfd in read_this:

        this_packet,this_client=hub.recvfrom(65536)
        sha512sum=sha512(this_packet).digest()

        if not sha512sum in sha512cache:
            if len(sha512cache)==65536:
                sha512cache=md5cache[1::]
            sha512cache+=[sha512sum]
            packet_length=len(this_packet)
            for this_socket in os.listdir(remotesockdir):
                if this_socket!=this_client:
                    try:
                        write_length=hub.sendto(this_packet,remotesockdir+'/'+this_socket)
                        if write_length!=packet_length:
                            os.write(2,'error: write_length == '+str(write_length)+', packet_length == '+str(packet_length))
                    except:
                        os.write(2,'error: cannot write to '+remotesockdir+'/'+this_socket)

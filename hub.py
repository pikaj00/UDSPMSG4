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
        md5sum=md5(this_packet).digest()

        if not md5sum in md5cache:
            if len(md5cache)==65536:
                md5cache=md5cache[1::]
            md5cache+=[md5sum]
            for this_socket in os.listdir(remotesockdir):
                if this_socket!=this_client:
                    try:
                        hub.sendto(this_packet,remotesockdir+'/'+this_socket)
                    except:
                        os.remove(remotesockdir+'/'+this_socket)

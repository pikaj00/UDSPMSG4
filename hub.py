#!/usr/bin/env python
import sys, os, collections
from hashlib import *
from socket import *

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

md5cache=[]
md5cache=collections.deque(maxlen=16384)
switch={}

while 1:
    this_packet,this_client=hub.recvfrom(65536)
    these_KVPs=udpmsg4.unframe(this_packet)
    md5sum=md5(this_packet).digest()

    if not md5sum in md5cache:
        md5cache+=[md5sum]

        if these_KVPs!=0:
            if 'CMD' in these_KVPs:
                for this_socket in os.listdir(remotesockdir):
                    if this_socket!=this_client:
                        try:
                            hub.sendto(this_packet,remotesockdir+'/'+this_socket)
                        except:
                            pass

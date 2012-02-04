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

md5cache=collections.deque(maxlen=4096)
md5cache=[]
switch={}

while 1:
    this_packet,this_client=hub.recvfrom(65536)
    md5sum=md5(this_packet).digest()

    if not md5sum in md5cache:
        these_KVPs=udpmsg4.unframe(this_packet)
        if these_KVPs!=0:
            md5cache+=[md5sum]

            if 'SRCKEY' in these_KVPs:
                if these_KVPs['SRCKEY'] in switch:
                    switch[these_KVPs['SRCKEY']]+=[this_client]
                    switch[these_KVPs['SRCKEY']]=list(set(switch[these_KVPs['SRCKEY']]))
                else:
                    switch[these_KVPs['SRCKEY']]=[this_client]

            if 'DSTKEY' in these_KVPs:
                if these_KVPs['DSTKEY'] in switch:
                    if these_KVPs['DSTKEY']==switch[these_KVPs['DSTKEY']]:
                        for this_socket in switch[these_KVPs['DSTKEY']]:
                            if this_socket!=this_client:
                                try:
                                    hub.sendto(this_packet,remotesockdir+'/'+this_socket)
                                except:
                                    switch[these_KVPs['DSTKEY']].remove(this_socket)
                                    if switch[these_KVPs['DSTKEY']]==[]:
                                        del switch[these_KVPs['DSTKEY']]

            else:
                for this_socket in os.listdir(remotesockdir):
                    if this_socket!=this_client:
                        try:
                            hub.sendto(this_packet,remotesockdir+'/'+this_socket)
                        except:
                            pass

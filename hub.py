#!/usr/bin/env python
import sys, os, select
from hashlib import *
#from socket import *
import socket
readable=select.select

sys.dont_write_bytecode=True
import udpmsg4

hubsock=(sys.argv[1])
remotesockdir=sys.argv[2]
os.write(2,'hub.py start '+remotesockdir+'\n')
hub=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
try:
    hub.bind(hubsock)
except:
    os.remove(hubsock)
    hub.bind(hubsock)
hub.setblocking(0)
hubfd=hub.fileno()

eagain=[]
success=[]
sha512cache=[]
while 1:
    message=''
    message+='hub.py SUCCESS ['
    for this_socket in success:
        message+=this_socket+','
    message+=']'
    success=[]
    message+=' EAGAIN ['
    for this_socket in eagain:
        message+=this_socket+','
    message+=']\n'
    os.write(2,message+'\n')
    eagain=[]
    read_this=readable([hubfd],[],[],1)[0]
    if hubfd in read_this:

        this_packet,this_client=hub.recvfrom(65536)
        os.write(2,'hub.py received from '+this_client+'\n')
        sha512sum=sha512(this_packet).digest()

        if not sha512sum in sha512cache:
            if len(sha512cache)==65536:
                sha512cache=sha512cache[1::]
            sha512cache+=[sha512sum]
            packet_length=len(this_packet)
            for this_socket in os.listdir(remotesockdir):
#                os.write(2,'hub.py test '+remotesockdir+'/'+this_socket+'!='+this_client+'\n')
                if remotesockdir+'/'+this_socket!=this_client:
                    try:
                        write_length=hub.sendto(this_packet,remotesockdir+'/'+this_socket)
                        if write_length!=packet_length:
                            os.write(2,'hub.py error: write_length == '+str(write_length)+', packet_length == '+str(packet_length)+'\n')
                        success+=[this_socket]
                    except socket.error, ex:
                        if ex.errno == 111:
                            os.write(2,'hub.py socket dead '+remotesockdir+'/'+this_socket+'\n')
                            os.remove(remotesockdir+'/'+this_socket)
                        if ex.errno != 11:
                            os.write(2,'hub.py error: cannot write to '+remotesockdir+'/'+this_socket+' '+str(ex.errno)+'\n')
                        if ex.errno == 11:
                            eagain+=[this_socket]
                else:
                    os.write(2,'hub.py received from '+this_socket+'\n')

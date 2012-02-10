#!/usr/bin/env python
import sys, os, select, collections
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

success=[]
eagain=[]
queue=dict()
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
    message+=']'
    eagain=[]
    message+=' QUEUE ['
    for key in queue.keys():
        message+=os.path.basename(key)+'='+str(len(queue[key]))
        if not key in clientsocketpaths:
            del queue[key]
            message+='D'
        message+=','
    message+=']\n'
    os.write(2,message+'\n')
    for key in queue.keys():
        if len(queue[key])>0:
            try:
                write_length=hub.sendto(queue[key][0],key)
                if write_length!=len(queue[key][0]):
                    os.write(2,'hub.py error: write_length == '+str(write_length)+', packet_length == '+str(len(queue[key][0]))+'\n')
                queue[key].popleft()
                os.write(2,'hub.py extra send success '+key+' (still '+str(len(queue[key]))+')\n')
            except socket.error, ex:
                if ex.errno == 111:
                    os.write(2,'hub.py socket dead '+key+'('+str(len(queue[key]))+')\n')
                    os.remove(key)
                if ex.errno != 11:
                    os.write(2,'hub.py error: cannot write to '+key+' '+str(ex.errno)+'\n')
                if ex.errno == 11:
                    os.write(2,'hub.py error: try again write to '+key+' (still '+str(len(queue[key]))+')\n')
    read_this=readable([hubfd],[],[],1)[0]
    clientsocketpaths=os.listdir(remotesockdir)
    message=''
    for key in clientsocketpaths:
        if not key in queue:
            queue[key]=collections.deque([],128)
            message+=os.path.basename(key)+','
    if len(message)>0:
        message='hub.py NEW ['+message+']\n'
        os.write(2,message+'\n')
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
                if remotesockdir+'/'+this_socket!=this_client:
                    if len(queue[this_socket])==0:
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
                                queue[this_socket].append(this_packet)
                    else:
                        queue[this_socket].append(this_packet)
                else:
                    os.write(2,'hub.py received from '+this_socket+'\n')

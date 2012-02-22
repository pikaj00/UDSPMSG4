#!/usr/bin/env python
import sys, os, select, collections
from hashlib import *
#from socket import *
import socket
readable=select.select
cacheq=select.select

sys.dont_write_bytecode=True
import config, udpmsg4
config.mtime=os.path.getmtime('config.py')

def filter(kvps):
    if kvps==0:
        os.write(2,'hub.py: '+PID+' rejected protocol error\n')
        return 0
    if config.accept!={}:
        for key in config.accept.keys():
            if config.accept[key]==None:
                if not key in kvps.keys():
                    for this_key in kvps.keys():
                        if not this_key in config.accept:
                            os.write(2,'hub.py: '+PID+' KEY ['+this_key+'] NOT IN ACCEPT\n')
                            return 0
            if config.accept[key]!=None:
                if key in kvps:
                    if config.accept[key]!=kvps[key]:
                        os.write(2,'hub.py: '+PID+' KEY/VALUE ['+key+'='+config.accept[key]+'] != ['+key+'='+kvps[key]+']\n')
                        return 0
        if None in config.accept.keys():
            if not config.accept[None] in kvps.values():
                os.write(2,'hub.py: '+PID+' VALUE ['+config.accept[None]+'] NOT IN PACKET\n')
                return 0

    if config.reject!={}:
        for key in config.reject.keys():
            if config.reject[key]==None:
                if key in kvps.keys():
                    os.write(2,'hub.py: '+PID+' KEY ['+key+'] IN REJECT\n')
                    return 0
            if config.reject[key]!=None:
                if key in kvps.keys():
                    if config.reject[key]==kvps[key]:
                        os.write(2,'hub.py: '+PID+' KEY/VALUE ['+key+'='+config.reject[key]+'] == ['+key+'='+kvps[key]+']\n')
                        return 0
        if None in config.reject.keys():
            if config.reject[None] in kvps.values():
                os.write(2,'hub.py: '+PID+' VALUE ['+config.reject[None]+'] IN PACKET\n')
                return 0
    return kvps

hubsock=(sys.argv[1])
remotesockdir=sys.argv[2]
PID=str(os.getpid())
os.write(2,'hub.py: '+PID+' start '+remotesockdir+'\n')
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
cache=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
cache.connect(('127.15.78.3',15256))
cache.setblocking(0)
cachefd=cache.fileno()
while 1:
    if config.mtime!=os.path.getmtime('config.py'):
        config.mtime=os.path.getmtime('config.py')
        reload(config)

    maxqueue=128*len(os.listdir(remotesockdir))
    message=''
    message+='hub.py: '+PID+' SUCCESS ['
    for this_socket in success:
        message+=this_socket+','
    message+=']'
    success=[]
    message+=' EAGAIN ['
    for this_socket in eagain:
        message+=this_socket+','
    message+=']'
    eagain=[]
    message+=' MAXQUEUE ['+str(maxqueue)+'] QUEUE ['
    for key in queue.keys():
        message+=os.path.basename(key)+'='+str(len(queue[key]))
        if not key in clientsocketpaths:
            del queue[key]
            message+='D'
        message+=','
    message+=']\n'
    os.write(2,message+'\n')
    queued=0
    for key in queue.keys():
        if len(queue[key])>0:
            queued+=1
            try:
                write_length=hub.sendto(queue[key][0],remotesockdir+'/'+key)
                if write_length!=len(queue[key][0]):
                    os.write(2,'hub.py: '+PID+' error: write_length == '+str(write_length)+', packet_length == '+str(len(queue[key][0]))+'\n')
                queue[key].popleft()
                os.write(2,'hub.py: '+PID+' extra send success '+key+' (still '+str(len(queue[key]))+')\n')
                queued+=100
            except socket.error, ex:
                if ex.errno == 111:
                    os.write(2,'hub.py: '+PID+' socket dead '+key+'('+str(len(queue[key]))+')\n')
                    try:
                        os.remove(remotesockdir+'/'+key)
                    except:
                        pass
                if ex.errno != 11:
                    os.write(2,'hub.py: '+PID+' error: cannot write to '+key+' '+str(ex.errno)+'\n')
                if ex.errno == 11:
                    os.write(2,'hub.py: '+PID+' error: try again write to '+key+' (still '+str(len(queue[key]))+')\n')
        if len(queue[key])<=maxqueue:
            queue[key]=collections.deque(queue[key],maxqueue)
    if queued>0:
        timeout=1.0/queued
    else:
        timeout=1
    os.write(2,'hub.py: '+PID+' poll timeout '+str(timeout)+'\n')
    read_this=readable([hubfd],[],[],timeout)[0]
    clientsocketpaths=os.listdir(remotesockdir)
    message=''
    for key in clientsocketpaths:
        if not key in queue:
            queue[key]=collections.deque([],maxqueue)
            message+=os.path.basename(key)+','
    if len(message)>0:
        message='hub.py: '+PID+' NEW ['+message+']\n'
        os.write(2,message+'\n')
    if hubfd in read_this:

        this_packet,this_client=hub.recvfrom(65536)
        os.write(2,'hub.py: '+PID+' received from '+this_client+'\n')
        #sha512sum=sha512(this_packet).digest()

        #if not sha512sum in sha512cache:
        #    if len(sha512cache)==65536:
        #        sha512cache=sha512cache[1::]
        #    sha512cache+=[sha512sum]

        cachedb=''
        while cachedb!='':
            try:
                cache.send(this_packet)
                cachedb=0
            except socket.error, ex:
                if ex.errno == 11: pass

        cachedb=''
        while cachedb!='':
            try:
                cachedb=ord(cache.recv(1))
            except:
                pass

        kvps=udpmsg4.unframe(this_packet)
        packet_test=filter(kvps)
        if cachedb!=1 and kvps!=0 and packet_test!=0:
            packet_length=len(this_packet)
            for this_socket in os.listdir(remotesockdir):
                if remotesockdir+'/'+this_socket!=this_client:
                    if not this_socket in queue:
                        break
                    if len(queue[this_socket])==0:
                        try:
                            write_length=hub.sendto(this_packet,remotesockdir+'/'+this_socket)
                            if write_length!=packet_length:
                                os.write(2,'hub.py: '+PID+' error: write_length == '+str(write_length)+', packet_length == '+str(packet_length)+'\n')
                            os.write(2,'hub.py: '+PID+' success: can write to '+this_socket+'\n')
                            success+=[this_socket]
                        except socket.error, ex:
                            if ex.errno == 111:
                                os.write(2,'hub.py: '+PID+' socket dead '+remotesockdir+'/'+this_socket+'\n')
                                os.remove(remotesockdir+'/'+this_socket)
                            if ex.errno != 11:
                                os.write(2,'hub.py: '+PID+' error: cannot write to '+remotesockdir+'/'+this_socket+' '+str(ex.errno)+'\n')
                            if ex.errno == 11:
                                eagain+=[this_socket]
                                queue[this_socket].append(this_packet)
                    else:
                        queue[this_socket].append(this_packet)
                else:
                    os.write(2,'hub.py: '+PID+' received from '+this_socket+'\n')

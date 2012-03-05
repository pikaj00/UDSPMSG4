#!/usr/bin/env python
import sys, os, select, collections
from time import time
import socket

POLL=select.select
PID=str(os.getpid())
HUBDIR=sys.argv[1]
CACHEDIR=sys.argv[2]
CACHESOCK=sys.argv[2]+'/cache'
CACHEPATH=(sys.argv[2]+'/'+PID)
CLIENT='CLIENT=['+str(os.getpid())+'@'+os.getenv('TCPREMOTEIP')+':'+os.getenv('TCPREMOTEPORT')+']'
cache=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
try:
    os.remove(HUBDIR+'/pid/'+PID)
except:
    pass
file(HUBDIR+'/pid/'+PID,'w')

try:
    os.remove(CACHEPATH)
except:
    pass

cache.setblocking(0)
cache.bind(CACHEPATH)
CACHEFD=cache.fileno()

sys.dont_write_bytecode=True
import config, udpmsg4
config.mtime=os.path.getmtime('config.py')

def filter(kvps):
    if kvps==0:
        return 0
    if config.accept!={}:
        for key in config.accept.keys():
            if config.accept[key]==None:
                if not key in kvps.keys():
                    for this_key in kvps.keys():
                        if not this_key in config.accept:
                            os.write(2,'hub.py: '+CLIENT+' KEY ['+this_key+'] NOT IN ACCEPT\n')
                            return 0
            if config.accept[key]!=None:
                if key in kvps:
                    if config.accept[key]!=kvps[key]:
                        os.write(2,'hub.py: '+CLIENT+' KEY/VALUE ['+key+'='+config.accept[key]+'] != ['+key+'='+kvps[key]+']\n')
                        return 0
        if None in config.accept.keys():
            if not config.accept[None] in kvps.values():
                os.write(2,'hub.py: '+CLIENT+' VALUE ['+config.accept[None]+'] NOT IN PACKET\n')
                return 0

    if config.reject!={}:
        for key in config.reject.keys():
            if config.reject[key]==None:
                if key in kvps.keys():
                    os.write(2,'hub.py: '+CLIENT+' KEY ['+key+'] IN REJECT\n')
                    return 0
            if config.reject[key]!=None:
                if key in kvps.keys():
                    if config.reject[key]==kvps[key]:
                        os.write(2,'hub.py: '+CLIENT+' KEY/VALUE ['+key+'='+config.reject[key]+'] == ['+key+'='+kvps[key]+']\n')
                        return 0
        if None in config.reject.keys():
            if config.reject[None] in kvps.values():
                os.write(2,'hub.py: '+CLIENT+' VALUE ['+config.reject[None]+'] IN PACKET\n')
                return 0
    return kvps

LOOP_TIME=0
CLIENT_QUEUE=[]
SOCKET_QUEUE={}
SENDSOCKETS={}
RECVSOCKETS={}
REMOTE_QUEUE='[]'
while 1:
    if config.mtime!=os.path.getmtime('config.py'):
        config.mtime=os.path.getmtime('config.py')
        reload(config)

    TIME=time()
    TIMEOUT=1.0/(1+LOOP_TIME)
    REMOTE_SOCKS=[]
    try:
        for SOCKET in os.listdir(HUBDIR+'/pid/'):
            if SOCKET!=PID:
                REMOTE_SOCKS+=[SOCKET]
                if not SOCKET in RECVSOCKETS:
                    try:
                        RECVSOCKETS[SOCKET]=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
                        RECVSOCKETS[SOCKET].setblocking(0)
                        try:
                            os.remove(HUBDIR+'/recv/'+PID+'FROM'+SOCKET)
                        except:
                            pass
                        RECVSOCKETS[SOCKET].bind((HUBDIR+'/recv/'+PID+'FROM'+SOCKET))
                    except socket.error, ex:
                        if ex.errno == 24:
                            os.write(2,'hub.py: '+CLIENT+' failed to create recvsocket for '+REMOTE+'\n')
    except socket.error, ex:
        if ex.errno == 24:
            os.write(2,'hub.py: '+CLIENT+' failed to read pids\n') 
    MAX_QUEUE=128*(len(REMOTE_SOCKS)+1)
    os.write(2,'hub.py: '+CLIENT+' MAX_QUEUE=['+str(MAX_QUEUE)+'] TIMEOUT=['+str(TIMEOUT)+'] CLIENT_QUEUE=['+str(len(CLIENT_QUEUE))+'] REMOTE_QUEUE='+REMOTE_QUEUE+'\n')

    if len(POLL([0],[],[],TIMEOUT)[0])!=0:
        try:
            packet=''
            packet_length=0
            packet=os.read(0,2)
            packet_length=(ord(packet[:1:])*256)+ord(packet[1:2:])
            while packet_length!=len(packet[2::]):
                if 0 in POLL([0],[],[],1)[0]:
                    buffer=os.read(0,packet_length-len(packet[2::]))
                    if buffer!='':
                        packet+=buffer
                    else:
                        break
        except:
            pass
        if packet_length==0 or len(packet)<=2:
            os.write(2,'hub.py: '+CLIENT+' connection to client died\n')
            os.remove(HUBDIR+'/pid/'+PID)
            os.remove(CACHEPATH)
            if SENDSOCKETS!={}:
                for REMOTE in SENDSOCKETS:
                    if os.path.exists(HUBDIR+'/send/'+PID+'TO'+REMOTE):
                        os.remove(HUBDIR+'/send/'+PID+'TO'+REMOTE)
            if RECVSOCKETS!={}:
                for REMOTE in RECVSOCKETS:
                    if os.path.exists(HUBDIR+'/recv/'+PID+'FROM'+REMOTE):
                        os.remove(HUBDIR+'/recv/'+PID+'FROM'+REMOTE)
            break
        elif packet_length!=len(packet[2::]):
            os.write(2,'hub.py: '+CLIENT+' fatal protocol error from client\n')
            os.remove(HUBDIR+'/pid/'+PID)
            os.remove(CACHEPATH)
            if SENDSOCKETS!={}:
                for REMOTE in SENDSOCKETS:
                    if os.path.exists(HUBDIR+'/send/'+PID+'TO'+REMOTE):
                        os.remove(HUBDIR+'/send/'+PID+'TO'+REMOTE)
            if RECVSOCKETS!={}:
                for REMOTE in RECVSOCKETS:
                    if os.path.exists(HUBDIR+'/recv/'+PID+'FROM'+REMOTE):
                        os.remove(HUBDIR+'/recv/'+PID+'FROM'+REMOTE)
            break
        else:
            write_length=0
            while write_length!=len(packet):
                try:
                    write_length=cache.sendto(packet,CACHESOCK)
                except:
                    pass
            cache_query=''
            while len(cache_query)!=1:
                if len(POLL([0],[],[],1)[0])==1:
                    try:
                        cache_query=cache.recv(1)
                    except:
                        pass
            if cache_query=='\x00':
                if filter(udpmsg4.unframe(packet))!=0:
                    os.write(2,'hub.py: '+CLIENT+' successful read from client\n')
                    for REMOTE in REMOTE_SOCKS:
                        if not REMOTE in SOCKET_QUEUE:
                            try:
                                SENDSOCKETS[REMOTE]=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
                                SENDSOCKETS[REMOTE].setblocking(0)
                                try:
                                    os.remove(HUBDIR+'/send/'+PID+'TO'+REMOTE)
                                except:
                                    pass
                                SENDSOCKETS[REMOTE].bind((HUBDIR+'/send/'+PID+'TO'+REMOTE))
                                SOCKET_QUEUE[REMOTE]=collections.deque([],MAX_QUEUE)
                            except socket.error, ex:
                                if ex.errno == 24:
                                    os.write(2,'hub.py: '+CLIENT+' failed to create sendsocket for '+REMOTE+'\n')
                        if REMOTE in SOCKET_QUEUE:
                            SOCKET_QUEUE[REMOTE]+=[packet]

    for SOCKET in RECVSOCKETS:
        while POLL([RECVSOCKETS[SOCKET].fileno()],[],[],0)[0]!=[]:
            if len(CLIENT_QUEUE)<=MAX_QUEUE:
                CLIENT_QUEUE=collections.deque(CLIENT_QUEUE,MAX_QUEUE)
            try:
                packet_length=0
                packet,REMOTE=RECVSOCKETS[SOCKET].recvfrom(65536)
                packet_length=(ord(packet[:1:])*256)+ord(packet[1:2:])
            except:
                pass
            if packet_length==0 or len(packet)<=2:
                os.write(2,'hub.py: '+CLIENT+' connection to '+REMOTE[len(HUBDIR)+6::].split('TO')[0]+' died\n')
            elif packet_length!=len(packet[2::]):
                os.write(2,'hub.py: '+CLIENT+' rejected protocol error from '+REMOTE[len(HUBDIR)+6::].split('TO')[0]+'\n')
            if filter(udpmsg4.unframe(packet))!=0:
                CLIENT_QUEUE+=[packet]
                write_length=0
                packet=CLIENT_QUEUE[0]
                packet_length=len(packet)
                while packet_length!=write_length:
                    try:
                        write_length=os.write(1,packet[write_length::])
                    except:
                        break
                if packet_length==write_length:
                    CLIENT_QUEUE.popleft()
                    os.write(2,'hub.py: '+CLIENT+' successful write to client\n')
                elif write_length>0:
                    CLIENT_QUEUE[0]=[packet[write_length::]]
                    os.write(2,'hub.py: '+CLIENT+' could not write complete packet to client\n')
                elif write_length==0:
                    os.write(2,'hub.py: '+CLIENT+' failed to write to client\n')

    if SOCKET_QUEUE!={}:
        DEQUE=[]
        REMOTE_QUEUE=''
        for REMOTE in SOCKET_QUEUE:
            if os.path.exists(HUBDIR+'/pid/'+REMOTE)==False:
                DEQUE+=[REMOTE]
            else:
                while len(SOCKET_QUEUE[REMOTE])!=0:
                    write_length=0
                    packet=SOCKET_QUEUE[REMOTE][0]
                    packet_length=len(packet)
                    while packet_length!=write_length:
                        try:
                            write_length=SENDSOCKETS[REMOTE].sendto(packet[write_length::],HUBDIR+'/recv/'+REMOTE+'FROM'+PID)
                        except:
                            break
                    if packet_length==write_length:
                        SOCKET_QUEUE[REMOTE].popleft()
                        os.write(2,'hub.py: '+CLIENT+' successful write to '+REMOTE+'\n')
                    elif write_length>0:
                        SOCKET_QUEUE[REMOTE][0]=packet[write_length::]
                        os.write(2,'hub.py: '+CLIENT+' could not write complete packet to '+REMOTE+'\n')
                        break
                    elif write_length==0:
                        os.write(2,'hub.py: '+CLIENT+' failed to write to '+REMOTE+'\n')
                        break
                if len(SOCKET_QUEUE[REMOTE])<=MAX_QUEUE:
                    SOCKET_QUEUE[REMOTE]=collections.deque(SOCKET_QUEUE[REMOTE],MAX_QUEUE)
                REMOTE_QUEUE+=REMOTE+'='+str(len(SOCKET_QUEUE[REMOTE]))+', '
        REMOTE_QUEUE='['+REMOTE_QUEUE[:len(REMOTE_QUEUE)-2:]+']'
        for REMOTE in DEQUE:
            del SOCKET_QUEUE[REMOTE]
            os.remove(HUBDIR+'/send/'+PID+'TO'+REMOTE)
            SENDSOCKETS[REMOTE].close()
            del SENDSOCKETS[REMOTE]
            try:
                os.remove(HUBDIR+'/recv/'+PID+'FROM'+REMOTE)
                RECVSOCKETS[REMOTE].close()
                del RECVSOCKETS[REMOTE]
            except:
                pass
    else:
        REMOTE_QUEUE='[]'

    while len(CLIENT_QUEUE)!=0:
        write_length=0
        packet=CLIENT_QUEUE[0]
        packet_length=len(packet)
        while packet_length!=write_length:
            try:
                write_length=os.write(1,packet[write_length::])
            except:
                break
        if packet_length==write_length:
            CLIENT_QUEUE.popleft()
            os.write(2,'hub.py: '+CLIENT+' successful write to client\n')
        elif write_length>0:
            CLIENT_QUEUE[0]=[packet[write_length::]]
            os.write(2,'hub.py: '+CLIENT+' could not write complete packet to client\n')
            break
        elif write_length==0:
            os.write(2,'hub.py: '+CLIENT+' failed to write to client\n')
            break

    LOOP_TIME=time()-TIME

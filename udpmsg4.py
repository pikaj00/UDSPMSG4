#!/usr/bin/env python

def frame(KVP):
    try:
        UDPMSG4=''
        for FRAME in KVP.items():
            UDPMSG4+=chr(len(FRAME[0]))+FRAME[0]+\
                     chr(int(round(len(FRAME[1])/256)))+\
                     chr(int(round(len(FRAME[1])%256)))+FRAME[1]
        return chr(int(round(len(UDPMSG4)/256)))+chr(int(round(len(UDPMSG4)%256)))+UDPMSG4
    except:    return 0

def unframe(UDPMSG4):
    try:
        KVP={}
        if len(UDPMSG4[2::])==(ord(UDPMSG4[:1:])*256)+ord(UDPMSG4[1:2:])\
            and UDPMSG4[2::]==UDPMSG4[2:(ord(UDPMSG4[:1:])*256)+ord(UDPMSG4[1:2:])+2:]:
                UDPMSG4=UDPMSG4[2::]

        while UDPMSG4!='':
            KEY=UDPMSG4[1:ord(UDPMSG4[:1:])+1:]
            len_KEY=len(KEY)
            VALUE=UDPMSG4[len_KEY+3:len_KEY+(ord(UDPMSG4[len_KEY+1:len_KEY+2:])*256)+ord(UDPMSG4[len_KEY+2:len_KEY+3:])+3:]
            KVP[KEY]=VALUE
            UDPMSG4=UDPMSG4[len_KEY+1+len(VALUE)+2::]
        return KVP
    except:    return 0

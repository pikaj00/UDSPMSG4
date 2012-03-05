#!/bin/sh

this_dir=`pwd`
mkdir -p env
mkdir -p env/servers
touch env/hubip
touch env/hubsocketsdir
touch env/clientsocketsdir
touch env/client2server

read -p "[Y/N] make hub?: " qna
if [[ "${qna//y/Y}" == *Y* ]]; then
    echo "[Default] `cat env/hubip`"
    read -p "[Enter] hub ip: " hubip
    [[ "$hubip" == '' ]] && hubip=`cat env/hubip`

    echo "[Default] `cat env/client2server`"
    read -p "[Enter] /path/to/ucspi-client2server: " client2server
    [[ "$client2server" == '' ]] && client2server=`cat env/client2server`

    echo "[Default] `cat env/hubsocketsdir`"
    read -p "[Enter] /path/to/hub/sockets/directory: " hubsocketsdir
    [[ "$hubsocketsdir" == '' ]] && hubsocketsdir=`cat env/hubsocketsdir`

    echo "[Default] `cat env/cachesocketsdir`"
    read -p "[Enter] /path/to/cache/sockets/directory: " cachesocketsdir
    [[ "$cachesocketsdir" == '' ]] && cachesocketsdir=`cat env/cachesocketsdir`

    echo "[Proposed configuration]
        hub ip: $hubip
        /path/to/ucspi-client2server: $client2server
        /path/to/hub/sockets/directory: $hubsocketsdir
        /path/to/cache/sockets/directory: $cachesocketsdir"

    read -p "[Y/N] use this configuration?: " qna
    if [[ "${qna//y/Y}" == *Y* ]]; then
        echo -n $hubip>env/hubip
        echo -n $client2server>env/client2server
        echo -n $hubsocketsdir>env/hubsocketsdir
        echo -n $cachesocketsdir>env/cachesocketsdir

        mkdir -p $hubsocketsdir
        mkdir -p $hubsocketsdir/pid
        mkdir -p $hubsocketsdir/send
        mkdir -p $hubsocketsdir/recv
        mkdir -p $cachesocketsdir

        mkdir -p /service/udpmsg4.hub
        cp run.hub /service/udpmsg4.hub/run
        cp hub.py /service/udpmsg4.hub/hub.py
        cp udpmsg4.py /service/udpmsg4.hub/udpmsg4.py
        [ -e /service/udpmsg4.hub/config.py ] || cp config.py /service/udpmsg4.hub/config.py
        [ -L /service/udpmsg4.hub/env ] || ( cd / ; ln -s $this_dir/env /service/udpmsg4.hub )
        [ -L /service/udpmsg4.hub/ucspi-client2server ] || ( cd / ; ln -s $client2server /service/udpmsg4.hub/client2server )

        mkdir -p /service/udpmsg4.cache
        cp run.cache /service/udpmsg4.cache/run
        cp cache.py /service/udpmsg4.cache/cache.py
        [ -L /service/udpmsg4.cache/env ] || ( cd / ; ln -s $this_dir/env /service/udpmsg4.cache )

        chmod +x /service/udpmsg4.cache/run
        chmod +x /service/udpmsg4.hub/run
    fi
fi

read -p "[Y/N] make peers?: " qna
if [[ "${qna//y/Y}" == *Y* ]]; then
    for this_peer in `ls peers` ; do
        mkdir -p /service/udpmsg4.$this_peer
        cp run.peer /service/udpmsg4.$this_peer/run
        [ -L /service/udpmsg4.$this_peer/env ] || ( cd / ; ln -s $this_dir/env /service/udpmsg4.$this_peer )
        [ -L /service/udpmsg4.$this_peer/$this_peer ] || ( cd / ; ln -s $this_dir/peers/$this_peer /service/udpmsg4.$this_peer/peer )
        chmod +x /service/udpmsg4.$this_peer/run
    done
fi

read -p "[Y/N] make ucspi-server2hub?: " qna
if [[ "${qna//y/Y}" == *Y* ]]; then
    read -p "[Y/N] configure new ucspi-server2hub?: " qna
    if [[ "${qna//y/Y}" == *Y* ]]; then
        read -p "[Enter] servname: " servname
        read -p "[Enter] servip: " servip
        read -p "[Enter] hubip: " hubip

        echo "[Proposed configuration]
        servname: $servname
        servip: $servip
        hubip: $hubip"

        read -p "[Y/N] use this configuration?: " qna
        if [[ "${qna//y/Y}" == *Y* ]]; then
            mkdir -p env/servers/$servname
            echo -n $servip>env/servers/$servname/servip
            echo -n $hubip>env/servers/$servname/hubip

            for this_serv in `ls env/servers` ; do
                mkdir -p /service/udpmsg4.$this_serv
                cp run.server2hub /service/udpmsg4.$this_serv/run
                cp udpmsg4.py /service/udpmsg4.$this_serv/udpmsg4.py
                cp ucspi-server2hub.py /service/udpmsg4.$this_serv/ucspi-server2hub.py
                [ -e /service/udpmsg4.$this_serv/config.py ] || cp ucspi-server2hub.config.py /service/udpmsg4.$this_serv/config.py
                [ -L /service/udpmsg4.$this_serv/env/servip ] ||
                    ( cd / ; ln -s $this_dir/env/servers/$this_serv/servip /service/udpmsg4.$this_serv )
                [ -L /service/udpmsg4.$server/env/hubip ] ||
                    ( cd / ; ln -s $this_dir/env/servers/$this_serv/hubip /service/udpmsg4.$this_serv )
                chmod +x /service/udpmsg4.$this_serv/run
            done
        fi
    fi

    if [[ $(ls env/servers) == '' ]]; then
        read -p "[Enter] servname: " servname
        read -p "[Enter] servip: " servip
        read -p "[Enter] hubip: " hubip

        echo "[Proposed configuration]
        servname: $servname
        servip: $servip
        hubip: $hubip"

        read -p "[Y/N] use this configuration?: " qna
        if [[ "${qna//y/Y}" == *Y* ]]; then
            mkdir -p env/servers/$servname
            echo -n $servip>env/servers/$servname/servip
            echo -n $hubip>env/servers/$servname/hubip

            for this_serv in `ls env/servers` ; do
                mkdir -p /service/udpmsg4.$this_serv
                cp run.server2hub /service/udpmsg4.$this_serv/run
                cp udpmsg4.py /service/udpmsg4.$this_serv/udpmsg4.py
                cp ucspi-server2hub.py /service/udpmsg4.$this_serv/ucspi-server2hub.py
                [ -e /service/udpmsg4.$this_serv/config.py ] || cp ucspi-server2hub.config.py /service/udpmsg4.$this_serv/config.py
                [ -L /service/udpmsg4.$this_serv/env/servip ] ||
                    ( cd / ; ln -s $this_dir/env/servers/$this_serv/servip /service/udpmsg4.$this_serv )
                [ -L /service/udpmsg4.$server/env/hubip ] ||
                    ( cd / ; ln -s $this_dir/env/servers/$this_serv/hubip /service/udpmsg4.$this_serv )
                chmod +x /service/udpmsg4.$this_serv/run
            done
        fi

    elif [[ $(ls env/servers) != '' ]]; then
        for this_serv in `ls env/servers` ; do
            mkdir -p /service/udpmsg4.$this_serv
            cp run.server2hub /service/udpmsg4.$this_serv/run
            cp udpmsg4.py /service/udpmsg4.$this_serv/udpmsg4.py
            cp ucspi-server2hub.py /service/udpmsg4.$this_serv/ucspi-server2hub.py
            [ -e /service/udpmsg4.$this_serv/config.py ] || cp config.py /service/udpmsg4.$this_serv/config.py
            [ -L /service/udpmsg4.$this_serv/env/servip ] ||
                ( cd / ; ln -s $this_dir/env/servers/$this_serv/servip /service/udpmsg4.$this_serv )
            [ -L /service/udpmsg4.$server/env/hubip ] ||
                ( cd / ; ln -s $this_dir/env/servers/$this_serv/hubip /service/udpmsg4.$this_serv )
            chmod +x /service/udpmsg4.$this_serv/run
        done
    fi
fi

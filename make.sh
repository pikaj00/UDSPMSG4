#!/bin/sh

this_dir=`pwd`
mkdir -p env
mkdir -p env/servers
touch env/this_ip
touch env/hub_socket
touch env/remote_sockets
touch env/client2server
touch env/naive

read -p "[Y/N] make hub?: " qna
if [[ "${qna//y/Y}" == *Y* ]]; then
    echo "[Default] `cat env/this_ip`"
    read -p "[Enter] this ip: " this_ip
    [[ "$this_ip" == '' ]] && this_ip=`cat env/this_ip`

    echo "[Default] `cat env/hub_socket`"
    read -p "[Enter] /path/to/hub/socket: " hub_socket
    [[ "$hub_socket" == '' ]] && hub_socket=`cat env/hub_socket`

    echo "[Default] `cat env/remote_sockets`"
    read -p "[Enter] /remote/sockets/directory: " remote_sockets
    [[ "$remote_sockets" == '' ]] && remote_sockets=`cat env/remote_sockets`

    echo "[Default] `cat env/naive`"
    read -p "[Enter] /path/to/hubtools/hashcache: " naive
    [[ "$naive" == '' ]] && naive=`cat env/naive`

    echo "[Proposed configuration]
        this ip: $this_ip
        /path/to/hub/socket: $hub_socket
        /remote/sockets/directory: $remote_sockets
        /path/to/hubtools/hashcache: $naive"

    read -p "[Y/N] use this configuration?: " qna
    if [[ "${qna//y/Y}" == *Y* ]]; then
        echo -n $this_ip>env/this_ip
        echo -n $hub_socket>env/hub_socket
        echo -n $remote_sockets>env/remote_sockets
        echo -n $naive>env/naive

        mkdir -p /service/udpmsg4.hub
        cp run.hub /service/udpmsg4.hub/run
        cp hub.py /service/udpmsg4.hub/hub.py
        cp udpmsg4.py /service/udpmsg4.hub/udpmsg4.py
        chmod +x /service/udpmsg4.hub/run
        [ -L /service/udpmsg4.hub/env ] || ( cd / ; ln -s $this_dir/env /service/udpmsg4.hub )
        [ -e /service/udpmsg4.hub/config.py ] || cp hub.config.py /service/udpmsg4.hub/config.py

        #mkdir -p /service/udpmsg4.cache
        #cp run.cache /service/udpmsg4.cache/run
        #(
        #    cd $naive
        #    make
        #    mv naive /service/udpmsg4.cache/naive
        #    rm naive.o
        #)
        #chmod +x /service/udpmsg4.cache/run

        mkdir -p /service/udpmsg4.client
        cp run.client /service/udpmsg4.client/run
        cp stream.py /service/udpmsg4.client/stream.py
        chmod +x /service/udpmsg4.client/run
        [ -L /service/udpmsg4.client/env ] || ( cd / ; ln -s $this_dir/env /service/udpmsg4.client )
    fi
fi

read -p "[Y/N] make peers?: " qna
if [[ "${qna//y/Y}" == *Y* ]]; then
    echo "[Default] `cat env/client2server`"
    read -p "[Enter] /path/to/ucspi-client2server: " client2server
    [[ "$client2server" == '' ]] && client2server=`cat env/client2server`

    echo "[Proposed configuration]
        /path/to/ucspi-client2server: $client2server"

    read -p "[Y/N] use this configuration?: " qna
    if [[ "${qna//y/Y}" == *Y* ]]; then
        echo -n $client2server>env/client2server

        for this_peer in `ls peers` ; do
            mkdir -p /service/udpmsg4.$this_peer
            cp run.peer /service/udpmsg4.$this_peer/run
            cp stream.py /service/udpmsg4.$this_peer/stream.py
            chmod +x /service/udpmsg4.$this_peer/run
            [ -L /service/udpmsg4.$this_peer/env ] || ( cd / ; ln -s $this_dir/env /service/udpmsg4.$this_peer )
            [ -L /service/udpmsg4.$this_peer/$this_peer ] || ( cd / ; ln -s $this_dir/peers/$this_peer /service/udpmsg4.$this_peer/peer )
            [ -L /service/udpmsg4.$this_peer/ucspi-client2server ] || ( cd / ; ln -s $client2server /service/udpmsg4.$this_peer/client2server )
        done
    fi
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
            [ -e /service/udpmsg4.$this_serv/config.py ] || cp ucspi-server2hub.config.py /service/udpmsg4.$this_serv/config.py
            [ -L /service/udpmsg4.$this_serv/env/servip ] ||
                ( cd / ; ln -s $this_dir/env/servers/$this_serv/servip /service/udpmsg4.$this_serv )
            [ -L /service/udpmsg4.$server/env/hubip ] ||
                ( cd / ; ln -s $this_dir/env/servers/$this_serv/hubip /service/udpmsg4.$this_serv )
            chmod +x /service/udpmsg4.$this_serv/run
        done
    fi
fi

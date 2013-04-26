#! /usr/bin/env python

from sys import path, argv; path.append('..')

from socket import *
from manager import *
from player.proxyplayer import *

server_socket = socket(AF_INET, SOCK_STREAM)
server_socket.bind((argv[1], int(argv[2])))
server_socket.listen(6)

admin = Administrator()

needed_players = int(argv[3])
while needed_players:
    sock, _ = server_socket.accept()
    prox_player = ProxyPlayer('remote_player_wow', sock)
    prox_player.start(admin)
    needed_players -= 1

try:
    if (len(argv) == 5):
        renderer = GameRenderer(admin, admin.run_acquire_game(1000))
        renderer.display_acquire_game()
    else:
        for state in admin.run_acquire_game(1000):
            if isinstance(state, str):
                print state
            else:
                state.printgs()

    print "HOLY SHIT WE DID IT"
finally:
    if server_socket:
        server_socket.shutdown(SHUT_WR)
    server_socket.close()

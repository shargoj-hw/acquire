#! /usr/bin/env python

from sys import path, argv; path.append('..')

from socket import *
from proxymanager import *
from player.tile_cheater import *
from player.share_cheater import *
from player.keep_cheater import *

player_socket = socket(AF_INET, SOCK_STREAM)
player_socket.connect((argv[1], int(argv[2])))

admin = ProxyAdministrator(player_socket)

#player = TileCheater("we_are_far_away")
#player = ShareCheater("we_are_far_away")
player = KeepCheater("we_are_far_away")

player.start(admin)

for game in admin.run_acquire_game(1000):
    if isinstance(game, str):
        print game
    else:
        game.printgs()

print "holy shit we played a game"

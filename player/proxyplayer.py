from player import Player

from Lib.acquire_xml_interface import *
from Lib.remote_xml_interface import *
from Lib.errors import PlayerError
from Lib.networking import AcquireNetworkMixin

TIMEOUT = 3 #seconds


class ProxyPlayer(Player, AcquireNetworkMixin):

    """
    Proxy player to play a networked acquire game
    Sends messages to a ProxyAdmin, which are then sent to actual players
    """

    def __init__(self, name, connection):
        """
        Create a proxy player

        Arguments:
            name - a sting representing the player's name
            connection - some sort of socket-y thing? just an ip?
                anyway the way we connect back to the remote player
        """
        Player.__init__(self, name)
        self.name = name
        AcquireNetworkMixin.__init__(self, connection, TIMEOUT)

    def start(self, admin):
        """ assume signup message is waiting on the wire """
        self.id = elt_to_signup(self.recieve())
        self.id = admin.sign_up(self.id, self)
        self.send(signup_to_xml(self.id))

    def setup(self, game_state):
        self.send_and_accept_void_response(state_to_xml(game_state))

    def take_turn(self, state, merger_function):
        self.send(turn_to_xml(state.board, state.players))

        response = self.recieve()

        if response.tag.lower() == 'pbuy':
            return elt_to_pbuy(response)
        elif response.tag.lower() == 'placement':
            tile, maybeHotel = elt_to_placement(response)

            if state.board.valid_merge_placement(tile, maybeHotel):
                _, players = merger_function(tile, maybeHotel)

                self.send(players_to_xml(players))
                # TODO tighten up checking
                buys = elt_to_order(self.recieve())

                return tile, maybeHotel, buys

            else:
                # TODO who is this allowed when these must be mergers?
                raise PlayerError("lolwhat")
        else:
            raise PlayerError("incorrect xml response to taketurn")

    def keep(self, state, hotels):
        self.send(keeps_to_xml(hotels))
        return elt_to_booleans(self.recieve())

    def inform(self, state):
        self.send_and_accept_void_response(state_to_xml(state))

    def new_tile(self, tile):
        self.send_and_accept_void_response(tile_to_xml(tile))

    def end_game(self, score, state):
        self.send_and_accept_void_response(score_state_to_xml(score, state))

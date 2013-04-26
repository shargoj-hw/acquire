from manager import Administrator
from Lib.acquire_xml_interface import *
from Lib.remote_xml_interface import *
from Lib.networking import AcquireNetworkMixin

class ProxyAdministrator(Administrator, AcquireNetworkMixin):

    def __init__(self, connection):
        """ initialize this networked Administrator """
        Administrator.__init__(self)
        AcquireNetworkMixin.__init__(self, connection)

    def sign_up(self, name, player_reference):
        self.player = player_reference

        self.send(signup_to_xml(name))
        name = elt_to_signup(self.recieve())
        # self.respond_with_void() # CODEWALK TODO: is this proper? see spec (no void mentioned)
        return name


    def run_acquire_game(self, number_of_turns):
        # Accept the initial game state (for setup)
        state = elt_to_state(self.recieve())
        self.player.setup(state)
        self.respond_with_void()

        yield state

        while 1:
            request = self.recieve()
            tag = request.tag.lower()

            if tag == 'turn':
                board, players = elt_to_turn(request)
                state = GameState._game_state_in_progress(players, board)

                merged = []
                def merger_function(tile, hotel):
                    merged.append(tile)
                    merged.append(hotel)

                    self.send(placement_to_xml(tile, hotel))

                    keeps = elt_to_keeps(self.recieve())
                    self.send(booleans_to_xml(self.player.keep(state, keeps)))

                    players = elt_to_players(self.recieve())

                    return state, players

                tile, hotel, buys = self.player.take_turn(state, merger_function)

                if merged:
                    self.send(order_to_xml(buys))
                else:
                    self.send(pbuy_to_xml(tile, hotel, buys))

            elif tag == 'keep':
                keeps = elt_to_keeps(request)
                self.send(booleans_to_xml(self.player.keep(state, keeps)))
            elif tag == 'tile':
                tile = elt_to_tile(request)
                self.player.new_tile(tile)
                self.respond_with_void()
            elif tag == 'state':
                state = elt_to_state(request)
                self.player.inform(state)
                self.respond_with_void()
                yield state
            elif tag == 'score':
                score, state = elt_to_score_state(request)
                self.player.end_game(score, state)
                self.respond_with_void()
                yield state
                return
            else:
                print tag
                raise Exception("The remote administrator is an asshole.")

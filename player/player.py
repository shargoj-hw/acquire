from copy import deepcopy
from basics import *
from state import GameState
from Lib.errors import PlayerError
from Lib.decontractors import *

"""
mad code skillz by lori
(and jim ^_^)
(and sarah :))
"""

class Player():
    """
    Template class for players.

    Players players are required to implement:
        take_turn
        keep
    Players should implement:
        setup
        inform
        new_tile
        end_game

    The following methods are provided for the convenience of implementors:
        valid_tile_moves
        valid_buy_orders

    Fields:
        id - this player's name

    """

    def __init__(self, id):
        """
        Creates an instance of this player type with a unique id

        Arguments:
            id - string

        """
        self.id = id

    def start(self, admin):
        """ Start this player with the given Administrator """
        self.id = admin.sign_up(self.id, self)

    ################################################################################
    #### Convenience methods provided for players ##################################
    ################################################################################
    def valid_tile_moves(self, state):
        """
        Get the list of all valid tile moves for state's current_player

        Arguments:
            state - state to inspect
        Returns:
            [(tile, maybeHotel, movetype)]
        Throws:
            PlayerError in the case when no playermoves are available
        """
        tiles = list(state.current_player.tiles)
        valid_tiles = []

        for tile in tiles:
            query_result = state.board.query(tile)

            if SINGLETON == query_result:
                valid_tiles.append((tile, None, SINGLETON))
            elif GROW == query_result:
                valid_tiles.append((tile, None, GROW))
            elif FOUND == query_result:
                hotels = list(state.board.hotels_not_in_play)
                map(valid_tiles.append, [(tile, hotel, FOUND) for hotel in hotels])
            elif MERGE == query_result:
                map(valid_tiles.append, [(tile, hotel, MERGE) for hotel in state.board.acquirers(tile)])
            elif INVALID == query_result:
                continue

        if valid_tiles == []:
            raise PlayerError("No tiles available for this player")

        return valid_tiles

    def valid_buy_orders(self, state):
        """ returns a list of all valid buy orders for the current player """
        def _can_afford_stocks(order):
            return state.current_player.money >= sum(state.board.stock_price(stock) for stock in order)

        def _are_available(order):
            return len(order) <= state.shares_map[order[0]] if order != [] else True

        def _buyable(order):
            return all(state.board.stock_price(stock) is not None for stock in order)

        return [order for order in ALL_LEGAL_BUYS
                if _buyable(order) and _are_available(order) and _can_afford_stocks(order)]

    ################################################################################
    #### Methods the player is to implement to play the game #######################
    ################################################################################
    def setup(self, game_state):
        """
        Sends this a player a full copy of gamestate
        """
        pass

    def take_turn(self, state, merger_function):
        """
        Called when this player takes a turn, returning his move and calling into merger_function
            when there is a merger.

        Arguments:
            state - the most updated GameState
            merger_function - Function (State Tile Hotel -> State, [Players])
                to be called when only when this player merges
        Returns:
            Tile, maybeHotel, BuyOrder
        """
        pass

    def keep(self, state, hotels):
        """
        Called by the manager when a merger happens,
        does this player want a buyback on the listed stocks?

        Contract: This should be deterministic. That is, when called twice with the same
            self and arguments, it returns the same values. !!! HANDWAVE !!!

        Arguments:
            hotels - a list of hotels which have been acquired

        Returns:
            [boolean] same length as the given list of hotels
                True- keep the shares of a hotel
                False- buyback the shares
        """
        pass

    def inform(self, state):
        """
        Inform this player of the newest state of the game (called at the end of turns)

        Arguments:
            state - the current state of the game
        """
        pass

    def new_tile(self, tile):
        """
        Give this player a new tile.

        Arguments:
            tile - this player's new tile
        """
        pass

    def end_game(self, score, state):
        """
        Inform this player that the game is over, informing them that the game is over
        and of everyone's score.

        Arguments:
            score - map of playernames to score
                score is an integer, the player's money + the cost of all their shares
            state - the last game state
        """
        pass

from player import Player
from basics import MERGE


class SimplePlayer(Player):
    """
    Convenience class for the easy implementation of simple Player strategies.

    Implementors should implement:
        _place_tile
        _buy_stock
    """

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
        tile, hotel, movetype = self._place_tile(state)

        if movetype == MERGE:
            state, _ = merger_function(tile, hotel)
        else:
            state.place_a_tile(tile, hotel)
        buys = self._buy_stock(state)
        return tile, hotel, buys

    def _place_tile(self, state):
        """
        What tile move will this player make for the given turn?

        This is a "protected" method, called by Player's implemenation of take_turn

        Return:
            (Tile, maybeHotel, Movetype)
        """
        pass

    def _buy_stock(self, state):
        """
        What buy move will this player make for the given turn?

        This is a "protected" method, called by Player's implemenation of take_turn

        Return:
            [Hotel] - (element of ALL_LEGAL_BUYS)
        """
        pass

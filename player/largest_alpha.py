from sys import path
path.append('..')

from player import *
from basics import *

# something like this should be defined somewhere
MAX_SHARES_PER_TURN = 3

class LargestAlphaStrategy(Player):
    """
    A strategy that chooses the largest tile according to tile<=?
    and as many shares as possible in alphabetical order.
    """

    def place_tile(self):
        # assuming tiles implement a comparison operator that should be used
        tiles = sorted(list(self.tiles), reverse=True, key=tile_sortkey)
        tile_move = TileMove()
        for tile in tiles:
            # assuming a few board methods here:
            query_result = self.board.query(tile)
            if query_result != INVALID:
                tile_move.tile = tile
                if FOUND in query_result:
                    tile_move.hotel = sorted(list(self.board.hotels_not_in_play))[0]
                elif MERGE in query_result:
                    hotels = [h for h, hs in query_result[1]]
                    tile_move.hotel = sorted(hotels)[0]
                return tile_move
        return TileMove()

    def buy_stock(self):
        shares_to_buy = list()
        for i in range(MAX_SHARES_PER_TURN):
            # sort on hotel_name (whic is i[0] in the lambda)
            for hotel, remaining in sorted(self.available_shares.items(), key=lambda i: i[0]):
                # No clue where to call calculate_stock_price from. It wasn't provided
                # in the interface, but it was used in comments on available_shares.
                if remaining > 0 and self.money > calculate_stock_price(hotel, len(self.board[hotel])):
                    shares_to_buy.append(hotel)
                    break
        return BuyMove(shares_to_buy)

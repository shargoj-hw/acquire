from sys import path
path.append('..')

from player import *
from basics import *

MAX_SHARES_PER_TURN = 3

class SmallestAntiStrategy(Player):
    """
    A strategy that chooses the smallest tile according to tile<=?
    and as many shares as possible in anti-alphabetical order.
    """

    #Returns a TileMove
    def place_tile(self):
        """
        Places the smallest tile determined by tile<=?
        """
        #assume sorted by tile<=?
        sorted_tiles = list(self.tiles).sort()
        tile_move = TileMove()
        for tile in sorted_tiles:
            if self.board.can_place_tile(tile):
                tile_move.tile = tile
                if self.board.is_founding(tile):
                    tile_move.hotel = sorted(self.board.not_placed_hotels())[0]
                elif self.board.is_merging(tile):
                    tile_move.hotel = sorted(self.board.merge_acquirers(tile))[0]
            return tile_move

    #Returns a BuyMove
    def buy_stock(self):
        """
        Purchases up to the max number of stocks in anti-alphabetical order
        """
        shares_to_buy = list()
        for i in range(MAX_SHARE_PER_TURN):
            #Sorted in anti-alphabetical order
            for hotel, remaining in sorted(self.available_shares.items(), key=lambda i: i[0], reverse=True):
                if remaining > 0 and self.money > calculate_stock_price(hotel, len(self.board()[hotel_name])):
                    shares_to_buy.append(hotel)
                    break
        return BuyMove(shares_to_buy)

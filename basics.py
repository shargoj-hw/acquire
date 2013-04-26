# constantinople
##########################################################################
## Data Definitions
##########################################################################
"""
board         -- dict from coords to squares
coord         -- one of coords
tile          -- one of coords
colrow        -- representation of tile: (col, row) where col is an int and row is a string
hotel         -- one of hotels; a string representing hotel names
money         -- non-negative integer representing the currency of the game
cash          -- same as money
shares        -- dict(hotel=>count) where count is a positive integer and hotel in hotels
stocks        -- same as shares
square is one of:
    Empty   - the square is unoccupied
    NoHotel - the square is occupied but not associated with a hotel
    hotel   - the square is associated with a hotel
movetype is one of:
    SINGLETON
    FOUND
    GROW
    MERGE
    INVALID

!!! in this data definition, tiles and coords can be used _interchangeably_ !!!
"""

##########################################################################
##  Define constants to be used by Acquire                               #
##########################################################################
Empty = None
NoHotel = 'NoHotel'

STARTING_MONEY = 8000
STARTING_TILES = 6

INITIAL_SHARES_PER_HOTEL = 25
FOUND_SHARES = 1

BUYS_PER_TURN = 2

HOTEL_SAFE_SIZE = 12
MAX_HOTEL_SIZE = 40

MAJORITY_PAYOUT_SCALE = 10
MINORITY_PAYOUT_SCALE = 5

MINIMUM_PRICE = 200
MAXIMUM_PRICE = 1200
PRICE_DIFFERENCE = 100

MIN_PLAYERS, MAX_PLAYERS = 3, 6

# Hotel Names
A = 'American'
C = 'Continental'
F = 'Festival'
I = 'Imperial'
S = 'Sackson'
T = 'Tower'
W = 'Worldwide'
# Colors
AColor = 'red'
CColor = 'blue'
FColor = 'green'
IColor = 'yellow'
SColor = 'purple'
TColor = 'brown'
WColor = 'orange'

SINGLETON = 'singleton'
FOUND = 'found'
GROW = 'grow'
MERGE = 'merge'
INVALID = 'invalid'

# valid range for rows in an Acquire board
rows = "ABCDEFGHI"

# valid range for columns in an Acquire board
cols = range(1,13)

# array of valid coordinates in an Acquire board, eg '12C'
coords = [str(__c) + __r for __r in rows for __c in cols]

def _dist(a, b):
    """
    Arguments : a - coord
                b - coord
    Returns   : int distance 'twixt a and b

    """
    col_a, row_a = int(a[:-1]), ord(a[-1:])
    col_b, row_b = int(b[:-1]), ord(b[-1:])
    # This will have to change if we need to use diagnals
    return abs(col_a - col_b) + abs(row_a - row_b)

adjacencies = dict([(__c, set()) for __c in coords])
for __c1 in coords:
    for __c2 in coords:
        if _dist(__c1, __c2) == 1:
            adjacencies[__c1].add(__c2)

# array of all hotel names
hotels = [A, C, F, I, S, T, W]

# array of all possible buy moves
ALL_LEGAL_BUYS = [[]] + \
                 [[__h] for __h in hotels] + [[__h, __h] for __h in hotels]

# array of hotel colors in order of hotels
colors = [AColor,CColor,FColor,IColor,SColor,TColor,WColor]

# map of all hotels with their associated color
hotel_color_map = dict(zip(hotels, colors))

# array of valid squares
squares = hotels + [Empty, NoHotel]

def calculate_stock_price(hotel, count):
    """
    Calculate the stock price for a hotel based on its size
    Arguments:
        hotel - name of a hotel
        count - size of the hotel chain
    Retuns:
        Natural Number or None (representing this stock can not be bought)

    """
    # smallest number of tiles associated with a particular price - used for
    #   all hotel categories, excluding the N/A cases
    prices = range(MINIMUM_PRICE, MAXIMUM_PRICE+PRICE_DIFFERENCE, PRICE_DIFFERENCE)

    if hotel in ['Worldwide', 'Sackson']:
        count_levels = [2, 3, 4, 5, 6, 11, 21, 31, 41]
    elif hotel in ['Festival', 'Imperial', 'American']:
        count_levels = [0, 2, 3, 4, 5, 6, 11, 21, 31, 41]
    elif hotel in ['Tower', 'Continental']:
        count_levels = [0, 0, 2, 3, 4, 5, 6, 11, 21, 31, 41]

    count_price_list = zip(count_levels, prices)
    for min_count, price in reversed(count_price_list):
        if count >= min_count:
            return price
    return None # Nobody can buy these

def tile_to_colrow(tile):
    """ returns a pair that is the strings (col, row) """
    return (int(tile[:-1]), tile[-1:])


def colrow_to_tile(col, row):
    """ returns a tile given the column and the row """
    return str(col) + row.upper()


def tile_sortkey(tile):
    """ convenience function for sorting tiles """
    return colrow_sortkey(tile_to_colrow(tile))


def colrow_sortkey(colrow):
    """ convenience function for sorting colrows """
    col, row = colrow

    # convert the column and row to a number that will enforce
    # the order (for sorting)
    return ord(row) * 1000 + col

def divide_and_round_integers(i, j):
    """ divides two integers and rounds to the nearest whole number """
    return int(round(float(i) / float(j)))

import unittest as ut
class TestBasics(ut.TestCase):
    def test_calculate_stock_price(self):
        self.assertEquals(calculate_stock_price(W, 0), None)
        self.assertEquals(calculate_stock_price(S, 1), None)
        self.assertEquals(calculate_stock_price(F, 0), MINIMUM_PRICE)
        self.assertEquals(calculate_stock_price(T, 12), 900)

    def test_tile_to_colrow(self):
        self.assertEquals(tile_to_colrow("11C"), (11, 'C'))

    def test_colrow_to_tile(self):
        self.assertEquals("11C", colrow_to_tile(11, 'C'))

    def test_tile_sortkey(self):
        for i in range(len(coords)):
            for j in range(i+1, len(coords)):
                self.assertTrue(tile_sortkey(coords[i]) < tile_sortkey(coords[j]))

    def test_colrow_sortkey(self):
        colrows = [tile_to_colrow(c) for c in coords]
        for i in range(len(colrows)):
            for j in range(i+1, len(colrows)):
                self.assertTrue(colrow_sortkey(colrows[i]) < colrow_sortkey(colrows[j]))

    def test_divide_and_round_integers(self):
        self.assertEquals(divide_and_round_integers(5,3), 2)

# For testing!
t1A = "1A"
t2A = "2A"
t3A = "3A"
t4A = "4A"
t5A = "5A"
t6A = "6A"
t7A = "7A"
t8A = "8A"
t9A = "9A"
t10A = "10A"
t11A = "11A"
t12A = "12A"
t1B = "1B"
t2B = "2B"
t3B = "3B"
t4B = "4B"
t5B = "5B"
t6B = "6B"
t7B = "7B"
t8B = "8B"
t9B = "9B"
t10B = "10B"
t11B = "11B"
t12B = "12B"
t1C = "1C"
t2C = "2C"
t3C = "3C"
t4C = "4C"
t5C = "5C"
t6C = "6C"
t7C = "7C"
t8C = "8C"
t9C = "9C"
t10C = "10C"
t11C = "11C"
t12C = "12C"
t1D = "1D"
t2D = "2D"
t3D = "3D"
t4D = "4D"
t5D = "5D"
t6D = "6D"
t7D = "7D"
t8D = "8D"
t9D = "9D"
t10D = "10D"
t11D = "11D"
t12D = "12D"
t1E = "1E"
t2E = "2E"
t3E = "3E"
t4E = "4E"
t5E = "5E"
t6E = "6E"
t7E = "7E"
t8E = "8E"
t9E = "9E"
t10E = "10E"
t11E = "11E"
t12E = "12E"
t1F = "1F"
t2F = "2F"
t3F = "3F"
t4F = "4F"
t5F = "5F"
t6F = "6F"
t7F = "7F"
t8F = "8F"
t9F = "9F"
t10F = "10F"
t11F = "11F"
t12F = "12F"
t1G = "1G"
t2G = "2G"
t3G = "3G"
t4G = "4G"
t5G = "5G"
t6G = "6G"
t7G = "7G"
t8G = "8G"
t9G = "9G"
t10G = "10G"
t11G = "11G"
t12G = "12G"
t1H = "1H"
t2H = "2H"
t3H = "3H"
t4H = "4H"
t5H = "5H"
t6H = "6H"
t7H = "7H"
t8H = "8H"
t9H = "9H"
t10H = "10H"
t11H = "11H"
t12H = "12H"
t1I = "1I"
t2I = "2I"
t3I = "3I"
t4I = "4I"
t5I = "5I"
t6I = "6I"
t7I = "7I"
t8I = "8I"
t9I = "9I"
t10I = "10I"
t11I = "11I"
t12I = "12I"
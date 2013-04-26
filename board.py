from copy import copy, deepcopy
from basics import *
from Lib.decontractors import Precondition, Postcondition
import unittest as ut

class Board:
    """
    Representation of an Aquire board

    Properties:
        board
        hotels_with_sizes
        tiles_for_hotels
        hotels_in_play
        hotels_not_in_play

    Select Methods : grow
                     singleton
                     merge
                     found
    """
    def __init__(self):
        """ initializes an empty board """
        self.board = {}


    @Precondition(lambda: item in coords or item in squares, globals=globals())
    @Postcondition(lambda: __return__ in squares or all([c in coords for c in __return__]), globals=globals())
    def __getitem__(self, item):
        """
        Reference lookup into boards.
        Arguments : item - coord|square
        Returns   : square if item is a coord
                    set([coord]) if item is a square

        """
        if item in coords:
            if item in self.board:
                return self.board[item]
            else:
                return Empty
        else:
            return set([coord for coord in coords if self[coord] == item])

    def __eq__(self, other):
        """
        Is this board equal to the given object
        Arguments : other - object
        Returns   : bool

        """
        if isinstance(other, Board):
            return self.board == other.board
        return False

    def __iter__(self):
        """ Returns an iterator for this board's (coord, square) pairs ordered by coord. """
        return iter(sorted(((coord, self[coord]) for coord in coords), key=lambda (c, s): tile_sortkey(c)))

    @staticmethod
    # this precondition is incorrect
    #@Precondition(lambda: all([s in squares and all([c in coords for c in cs])
    #    for s, cs in square_coords]))
    @Postcondition(lambda: isinstance(__return__, Board), globals=globals())
    def _board_in_play(square_coords):
        """
        Construct a testable Board from the given mapping of squares, to the set of coordinates with that square, which
            represents tiles that players have placed. (this simulates many turns quickly for testing purposes)
        Arguments : dict[(square => [coord])]
        Return    : Board

        """
        b = Board()
        for s, cs in square_coords:
            for c in cs:
                b.board[c] = s
        return b

    def _to_board_in_play(self):
        board_data = [(NoHotel, self[NoHotel])]
        for h in self.hotels_in_play:
            board_data.append((h, self[h]))
        return board_data

    def __copy__(self):
        b = Board()
        b.board = copy(self.board)
        return b

    def __deepcopy__(self, _):
        return self.__copy__()

    def __str__(self):
        inv_map = {}
        for k, v in self.board.iteritems():
            inv_map[v] = inv_map.get(v, [])
            inv_map[v].append(k)
        return str(inv_map)

    ###########################################################################
    ### Board Query Functions: ################################################
    ###########################################################################
    @Precondition(lambda: coord in coords, globals=globals())
    def is_space_free(self, coord):
        """
        Is the space at the given coordinate currently unused on this board
        Arguments : coord
        Returns   : bool

        """
        return self[coord] == Empty

    @property
    @Postcondition(lambda: all(h in hotels and h in self.board.values() for h in __return__ ), globals=globals())
    def hotels_in_play(self):
        """
        Get the hotels that are currently placed on this board
        Returns   : set([hotel])

        """
        return set([s for s in self.board.values() if s in hotels])

    @property
    def hotels_not_in_play(self):
        """
        Get the hotels not currently placed on this board
        Returns   : set([hotel])

        """
        return set(hotels) - self.hotels_in_play

    @property
    def tiles_for_hotels(self):
        """
        Get the hotels currently placed on this board, mapped to the tiles currently associated with those hotels
        Returns   : dict([(hotel, set([tile])...])

        """
        hip = self.hotels_in_play
        return dict([(h, set([c for c, s in self.board.items() if s == h])) for h in hip])

    @property
    def hotels_with_sizes(self):
        """
        Get the list of hotels currently on this board, mapped to their sizes, and ordered by those sizes
        Returns   : [(hotel, int)...] ordered by size for hotels in play

        """
        hotels_with_sizes = [(h, self.hotel_size(h)) for h in self.hotels_in_play]
        hotels_with_sizes.sort(key=lambda hs: -hs[1])  # sort from biggest to smallest
        return hotels_with_sizes

    @Precondition(lambda: coord in coords, globals=globals())
    def adjacent_coords(self, coord):
        """
        Get the set of coords one unit away from the given coord
        Arguments : coord
        Returns   : set([coord])

        """
        return adjacencies[coord]

    @Precondition(lambda: coord in coords, globals=globals())
    def adjacent_squares(self, coord):
        """
        Get the set of squares one unit away from the given coord.
        Arguments : coord
        Returns   : set([square])

        """
        return set([self[c] for c in self.adjacent_coords(coord)])

    @Precondition(lambda: coord in coords, globals=globals())
    def adjacent_hotels(self, coord):
        """
        Get the set of all hotels adjacent to given coord
        Arguments : coord
        Returns   : set([hotel])

        """
        return set([s for s in self.adjacent_squares(coord) if s in hotels])

    @Precondition(lambda: coord in coords, globals=globals())
    def adjacent_nohotel_count(self, coord):
        """
        Count the number of NoHotel squares around the given coord
        Arguments : coord
        Returns   : integer

        """
        return len([s for s in self.adjacent_coords(coord) if self[s] == NoHotel])

    @Precondition(lambda: hotel in hotels, globals=globals())
    def hotel_size(self, hotel):
        """
        Calculate the size of the given hotel
        Arguments : hotel
        Returns   : int
        """
        return len([s for _, s in self.board.items() if s == hotel])

    @Precondition(lambda: hotel in hotels, globals=globals())
    def stock_price(self, hotel):
        """
        Calculate the stock price of the given hotel for this board.

        Arguments:
            hotel - the hotel
        Returns:
            int or None - the cost of None if impossible to buy.
        """
        return calculate_stock_price(hotel, self.hotel_size(hotel))

    @Precondition(lambda: hotel in hotels, globals=globals())
    def is_hotel_safe(self, hotel):
        """
        Is the given hotel considered safe on this board?
        Arguments : hotel
        Returns   : bool

        """
        return self.hotel_size(hotel) >= HOTEL_SAFE_SIZE

    @Precondition(lambda: tile in coords, globals=globals())

    def acquirers(self, tile):
        """ returns a list of the largest hotels adjacent to this coord """
        hotels_with_sizes = [(h, self.hotel_size(h)) for h in self.adjacent_hotels(tile)]
        if hotels_with_sizes:
            hotels_with_sizes.sort(key=lambda (hotel, size): -size)
            return [h for h, s in hotels_with_sizes if s==hotels_with_sizes[0][1]]
        else:
            return []

    @Precondition(lambda: hotel in hotels and self.valid_merge_placement(tile, hotel), globals=globals())
    def acquirees(self, tile, hotel):
        """ returns the list of hotels that would be acquired in this tile merger """
        return [h for h in self.adjacent_hotels(tile) if h != hotel]

    @Precondition(lambda: tile in coords, globals=globals())
    def query(self, tile):
        """
        Ask this board what can be done what effect placing the given tile will have
        Arguments:
            tile
        Returns:
            movetype
        """
        acquirers = self.acquirers(tile)

        if not self.is_space_free(tile):
            return INVALID
        elif any([self.valid_found_placement(tile, h) for h in self.hotels_not_in_play]):
            return FOUND
        elif self.valid_grow_placement(tile):
            return GROW
        elif acquirers and all([self.valid_merge_placement(tile, h) for h in acquirers]):
            return MERGE
        elif self.valid_singleton_placement(tile):
            return SINGLETON
        else:
            return INVALID

    ###########################################################################
    ### Board modifying commands: #############################################
    ###########################################################################
    @Precondition(lambda: self.valid_singleton_placement(tile), globals=globals())
    def singleton(self, tile):
        """
        Place the given tile on this board, with no other effects
        Arguments : tile

        """
        # assert self.valid_singleton_placement(tile)
        # tile as coordinate
        self.board[tile] = NoHotel

    @Precondition(lambda: self.valid_found_placement(tile, hotel), globals=globals())
    def found(self, tile, hotel):
        """
        Place the given tile on this board to found the given hotel
        Arguments : tile
                    hotel

        """
        # assert self.valid_found_placement(tile, hotel)
        self.board[tile] = hotel
        for c in [c for c in self.adjacent_coords(tile) if self[c] == NoHotel]:
            self.board[c] = hotel

    @Precondition(lambda: self.valid_merge_placement(tile, hotel), globals=globals())
    def merge(self, tile, hotel):
        """
        Place the given tile on the board and merge the adjacent hotels with the given hotel
        Arguments : tile
                    hotel
        """
        # assert self.valid_merge_placement(tile, hotel)
        self.board[tile] = hotel
        adj_hotels = self.adjacent_hotels(tile)
        for coord in sum([list(t) for h, t in self.tiles_for_hotels.items() if h in adj_hotels], []):
            self.board[coord] = hotel

    @Precondition(lambda: self.valid_grow_placement(tile), globals=globals())
    def grow(self, tile):
        """
        Place the given tile on the board and add the square on which it is placed to the adjacent hotel.
        Arguments : tile

        """
        # assert self.valid_grow_placement(tile)
        # this seems wrong, we should also link any adjacent, unaffiliated tiles
        #   with the hotel
        self.board[tile] = list(self.adjacent_hotels(tile))[0]

    ###########################################################################
    ### Tile Placement Assertions: ############################################
    ###########################################################################
    @Precondition(lambda: tile in coords, globals=globals())
    def valid_singleton_placement(self, tile):
        """
        Can the given tile be placed to make a singleton move on this board?
        Arguments : tile
        Returns   : bool

        """
        adj_squares = self.adjacent_squares(tile)
        hotels_not_in_play = self.hotels_not_in_play
        return self.is_space_free(tile) and \
            all([s == Empty or s == NoHotel for s in adj_squares]) and \
            not (hotels_not_in_play and self.valid_found_placement(tile, self.hotels_not_in_play.pop()))

    @Precondition(lambda: tile in coords, globals=globals())
    @Precondition(lambda: hotel in hotels or hotel is None, globals=globals())
    def valid_found_placement(self, tile, hotel):
        """
        Can the given tile be placed to found the given hotel on this board?
        Arguments : tile
                    hotel
        Returns   : bool

        """
        if hotel == None : return False
        assert hotel in hotels
        adj_nohot = [c for c in self.adjacent_coords(tile) if self[c] == NoHotel]
        return self.is_space_free(tile) and \
            self.hotels_not_in_play and \
            hotel not in self.hotels_in_play and \
            all([s not in hotels for s in self.adjacent_squares(tile)]) and \
            len(adj_nohot) >= 1 and \
            all([s == Empty for s in self.adjacent_squares(adj_nohot[0])])

    @Precondition(lambda: tile in coords, globals=globals())
    @Precondition(lambda: hotel in hotels or hotel is None, globals=globals())
    def valid_merge_placement(self, tile, hotel):
        """
        Can the given tile be placed to merge adjacent hotels with the given hotel on this board?
        Arguments : tile
                    hotel (acquirer)
        Returns   : bool

        """
        if hotel == None : return False
        assert hotel in hotels
        adj_hot = self.adjacent_hotels(tile)
        return self.is_space_free(tile) and \
            len(adj_hot) >= 2 and hotel in adj_hot and \
            all([not self.is_hotel_safe(h) for h in adj_hot]) and \
            all([not s == NoHotel for s in self.adjacent_squares(tile)])

    @Precondition(lambda: tile in coords, globals=globals())
    def valid_grow_placement(self, tile):
        """
        Can the given tile be placed to grow the adjacent hotel on this board
        Arguments : tile
        Returns   : bool

        """
        adj_hot = self.adjacent_hotels(tile)
        return self.is_space_free(tile) and len(adj_hot) == 1

    ###########################################################################
    ### Internal Function: ####################################################
    ###########################################################################


class TestBoard(ut.TestCase):
    def setUp(self):
        self.empty_board = Board()
        self.singleton_board = Board._board_in_play([(NoHotel, ['1A'])])
        self.board_1_hotel = Board._board_in_play([(A, ['3D','4E','3C'])])
        self.grow_1_hotel = Board._board_in_play([(A, ['4D','3D','4E','3C'])])
        self.board_2_hotels = Board._board_in_play([(W,['1A','2A','3A']),
                                                    (S,['1C','2C','3C'])])
        self.board_merged_2_hotels = Board._board_in_play([(W,['1A','2A','3A','1C','2C','2B','3C'])])
        self.two_hotels = set([W,S])
        self.board_3_hotels = Board._board_in_play([(F,['1C','2C']),
                                                    (S,['3A','3B']),
                                                    (I,['3D','3E'])])
        self.board_found_hotel = Board._board_in_play([(NoHotel, ['2A'])])
        self.board_founded_sackson = Board._board_in_play([(S, ['1A','2A'])])
        self.board_sackson_safe = Board._board_in_play([(S, [c for i,c in enumerate(coords) if i < HOTEL_SAFE_SIZE])])

        self.board_with_all_hotels = Board._board_in_play(
            [(NoHotel, set(['7G', '12A', '6C', '12F', '7A', '11D', '8B', '6I', '10F', '7D', '1G', '1I', '5A'])),
             (W, set(['6D', '6E', '6F', '4F', '5E', '5G', '5F'])), (F, set(['9E', '9D', '8E'])),
             (I, set(['1A', '1B'])), (C, set(['4H', '4I'])), (S, set(['4D', '3D'])),
             (A, set(['3B', '4B'])), (T, set(['9H', '9G']))])

        self.all_hotels_singleton_5E = Board._board_in_play(
                [(A, ["1A", "2A"]),
                 (C, ["4A", "5A"]),
                 (F, ["7A", "8A"]),
                 (I, ["10A", "11A"]),
                 (S, ["1C", "2C"]),
                 (T, ["4C", "5C"]),
                 (W, ["7C", "8C"]),
                 (NoHotel, ["5E"])])

    def test___getitem__(self):
        self.assertEquals(self.empty_board['1A'], Empty)
        self.empty_board.singleton('1A')
        self.assertEquals(self.empty_board['1A'], NoHotel)
        self.assertEquals(self.board_2_hotels[W], set(['1A', '2A', '3A']))

    def test___eq__(self):
        board_a = Board._board_in_play([(NoHotel, ['1A', '3B'])])
        board_b = Board._board_in_play([(NoHotel, ['1A', '3B'])])
        board_c = Board._board_in_play([(W, ['1A', '3B'])])

        self.assertEqual(board_a, board_b)
        self.assertNotEqual(board_a, board_c)
        self.assertNotEqual(board_a, "notaboard")

    def test___copy__(self):
        self.assertEqual(self.board_with_all_hotels, copy(self.board_with_all_hotels))

    #def test___deepcopy__(self):
    #    self.assertEqual(self.board_with_all_hotels, deepcopy(self.board_with_all_hotels))

    def test___iter__(self):
        for c, s in self.board_with_all_hotels:
            self.assertEqual(self.board_with_all_hotels[c], s)

    def test__board_in_play(self):
        b = Board._board_in_play([(NoHotel, ['1A']), ('Imperial', ['12E', '11E'])])
        self.empty_board.singleton('1A')
        self.empty_board.singleton('12E')
        self.empty_board.found('11E', 'Imperial')
        self.assertEqual(b, self.empty_board)

    def test__to_board_in_play(self):
        self.assertEqual(self.board_with_all_hotels, Board._board_in_play(self.board_with_all_hotels._to_board_in_play()))

    def test___str__(self):
        self.assertEqual(str(self.board_3_hotels),
            "{'Festival': ['1C', '2C'], 'Sackson': ['3B', '3A'], 'Imperial': ['3E', '3D']}")

    ###########################################################################
    ### Board Query Tests: ####################################################
    ###########################################################################
    def test_is_space_free(self):
        self.assertTrue(self.empty_board.is_space_free('5B'))

        self.empty_board.board['5B'] = NoHotel
        self.assertFalse(self.empty_board.is_space_free('5B'))

    def test_hotels_in_play(self):
        self.assertEquals(self.empty_board.hotels_in_play, set([]))

        self.assertEquals(self.board_2_hotels.hotels_in_play, self.two_hotels)

    def test_hotels_not_in_play(self):
        self.assertEqual(self.empty_board.hotels_not_in_play, set(hotels))

        less_two_hotels = set(hotels) - self.two_hotels
        self.assertEqual(self.board_2_hotels.hotels_not_in_play, less_two_hotels)

    def test_tiles_for_hotels(self):
        self.assertEquals(self.empty_board.tiles_for_hotels, dict())

        tfh = dict()
        tfh[W] = set(['1A', '2A', '3A'])
        tfh[S] = set(['1C', '2C', '3C'])
        self.assertEquals(self.board_2_hotels.tiles_for_hotels, tfh)

    def test_hotels_with_sizes(self):
        self.assertEquals(self.empty_board.hotels_with_sizes, [])

        self.assertEquals(self.board_3_hotels.hotels_with_sizes, [(F,2),(S,2),(I,2)])

    def test_adjacent_coords(self):
        self.assertEqual(self.empty_board.adjacent_coords('1A'), set(['2A', '1B']))

        self.assertEqual(self.empty_board.adjacent_coords('6F'), set(['5F', '6E', '6G', '7F']))

    def test_adjacent_squares(self):
        self.assertEquals(self.empty_board.adjacent_squares('5D'), set([Empty]))

        board_with_tower = Board._board_in_play([(T,['6D','5E','5F'])])
        self.assertEquals(board_with_tower.adjacent_squares('5D'), set([T, Empty]))

    def test_adjacent_hotels(self):
        self.assertEquals(self.empty_board.adjacent_hotels('4F'), set([]))

        self.assertEquals(self.board_3_hotels.adjacent_hotels('3C'), set([F,S,I]))

    def test_adjacent_nohotel_count(self):
        self.assertEquals(self.empty_board.adjacent_nohotel_count('2A'), 0)

        self.assertEquals(self.board_found_hotel.adjacent_nohotel_count('3A'), 1)

    def test_hotel_size(self):
        self.assertEquals(self.empty_board.hotel_size(T), 0)

        self.assertEquals(self.board_3_hotels.hotel_size(F), 2)

    def test_is_hotel_safe(self):
        self.assertFalse(self.empty_board.is_hotel_safe(F))

        self.assertFalse(self.board_1_hotel.is_hotel_safe(A))

        self.assertTrue(self.board_sackson_safe.is_hotel_safe(S))

    def test_query(self):
        self.assertEquals(self.empty_board.query('1A'),SINGLETON)

        self.assertEquals(self.board_found_hotel.query('2A'),INVALID)

        self.assertEquals(self.board_found_hotel.query('2B'),FOUND)

        self.assertEquals(self.board_1_hotel.query('3B'), GROW)

        self.assertEquals(self.board_2_hotels.query('2B'), MERGE)

    ###########################################################################
    ### Board modifying tests: ################################################
    ###########################################################################
    def test_singleton(self):
        self.empty_board.singleton('1A')
        self.assertEquals(self.empty_board, self.singleton_board)

    def test_found(self):
        self.board_found_hotel.found('1A',S)
        self.assertEqual(self.board_found_hotel, self.board_founded_sackson)

    def test_merge(self):
        self.board_2_hotels.merge('2B',W)
        self.assertEquals(self.board_2_hotels, self.board_merged_2_hotels)

        self.assertEquals(self.board_2_hotels.hotel_size(W), 7)

    def test_grow(self):
        self.board_1_hotel.grow('4D')
        self.assertEquals(self.board_1_hotel, self.grow_1_hotel)

        self.assertEquals(self.board_1_hotel.hotel_size(A), self.grow_1_hotel.hotel_size(A))

    ###########################################################################
    ### Board modifying tests: ################################################
    ###########################################################################
    def test_valid_singleton_placement(self):
        self.assertTrue(self.empty_board.valid_singleton_placement('10G'))
        self.assertFalse(self.board_found_hotel.valid_singleton_placement('2B'))
        self.assertFalse(self.board_1_hotel.valid_singleton_placement('5E'))
        self.assertFalse(self.board_3_hotels.valid_singleton_placement('1C'))

    def test_valid_found_placement(self):
        self.assertFalse(self.empty_board.valid_found_placement('2D',W))
        self.assertFalse(self.board_1_hotel.valid_found_placement('3D',S))
        self.assertTrue(self.board_found_hotel.valid_found_placement('2B',F))
        self.assertFalse(self.all_hotels_singleton_5E.valid_found_placement('6E', W))

    def test_valid_merge_placement(self):
        self.assertFalse(self.empty_board.valid_merge_placement('3A',T))
        self.assertTrue(self.board_2_hotels.valid_merge_placement('2B',W))
        self.assertFalse(self.board_found_hotel.valid_merge_placement('3A',F))

    def test_valid_grow_placement(self):
        self.assertTrue(self.board_1_hotel.valid_grow_placement('4C'))
        self.assertFalse(self.empty_board.valid_grow_placement('4D'))
        self.assertFalse(self.board_2_hotels.valid_grow_placement('2B'))

    ###########################################################################
    ### Misc. Board Tests: ####################################################
    ###########################################################################
    def test_placing_singleton_next_to_multiple_singletons(self):
        empty_board = Board._board_in_play([(NoHotel, ['2A', '1B'])])
        self.assertEqual(empty_board.query('1A'), 'found')
        #changed after proj10 rule changes

    def test_singleton_move_when_trying_to_place_on_full_board(self):
        self.assertEqual(self.board_with_all_hotels.query('12G'), 'singleton')


from sys import path, argv; path.append('..')

from acquire_xml_interface import *
import xml.etree.ElementTree as et

def elt_to_signup(e):
    if e.tag.lower() != "signup":
        raise XMLError("incorrect tag")

    name = e.attrib.get('name', None)
    return name

def elt_to_state(e):
    if e.tag.lower() != "state":
        raise XMLError("incorrect tag")

    board = elt_to_board(e[0])

    # the list of players is everything in the list of children after the board
    players = deque([])
    for c in e[1:]:
        players.append(elt_to_player(c))

    return game_state_in_progress(players,board)

def is_void(e):
    return e.tag.lower() == 'void'

def elt_to_turn(e):
    if e.tag.lower() != "turn":
        raise XMLError("incorrect tag")

    board = elt_to_board(e[0])

    # the list of players is everything in the list of children after the board
    players = deque([])
    for c in e[1:]:
        players.append(elt_to_player(c))

    return board, players

def elt_to_pbuy(e):
    if e.tag.lower() != "pbuy":
        raise XMLError("incorrect tag")

    tile, maybehotel = elt_to_placement(e[0])
    order = elt_to_order(e[1])

    return tile, maybehotel, order

def elt_to_placement(e):
    if e.tag.lower() != "placement":
        raise XMLError("incorrect tag")

    tile = elt_to_tile(e[0])
    hotel = None
    if len(e) > 1:
        hotel = elt_to_hotel(e[1])

    return tile, hotel

elt_to_tile = elt_to_tile

def elt_to_order(e):
    if e.tag.lower() != "order":
        raise XMLError("incorrect tag")

    return elt_to_hotels(e)

def elt_to_keeps(e):
    if e.tag.lower() != "keep":
        raise XMLError("incorrect tag")

    return elt_to_hotels(e)

def elt_to_booleans(e):
    if e.tag.lower() != "keep":
        raise XMLError("incorrect tag")

    return [elt_to_boolean(bool) for bool in e]

def elt_to_boolean(e):
    if e.tag.lower() == 'true':
        return True
    elif e.tag.lower() == 'false':
        return False
    else:
        raise XMLError('xml not true or false')

def elt_to_players(e):
    if e.tag.lower() != "players":
        raise XMLError("incorrect tag")

    return [elt_to_player(player) for player in e]

def elt_to_score_state(e):
    if e.tag.lower() != "score":
        print e.tag.lower()
        raise XMLError("incorrect tag")

    scores = dict([elt_to_score(score) for score in e[:-1]])
    state = elt_to_state(e[-1])

    return scores, state

def elt_to_score(e):
    if e.tag.lower() != "result":
        raise XMLError("incorrect tag")

    name = e.attrib.get('name', None)
    score = int(e.attrib.get('score', None))

    return name, score

def signup_to_xml(name):
    e = et.Element('signup')
    e.attrib['name'] = name
    return e

def state_to_xml(state):
    return game_state_to_xml(state)

def void_to_xml():
    return et.Element('void')

def turn_to_xml(board, players):
    e = et.Element('turn')
    e.append(board_to_xml(board))
    [e.append(player_to_xml(p)) for p in players]
    return e

def pbuy_to_xml(tile, hotel, order):
    e = et.Element('pbuy')
    e.append(placement_to_xml(tile, hotel))
    e.append(order_to_xml(order))
    return e

def placement_to_xml(tile, maybeHotel):
    e = et.Element('placement')
    e.append(tile_to_xml(tile))
    if maybeHotel:
        e.append(xhotel_to_xml(maybeHotel))
    return e

def _tag_with_hotels_to_xml(tag, hotels):
    e = et.Element(tag)
    for hotel in hotels:
        e.append(xhotel_to_xml(hotel))
    return e

def order_to_xml(order):
    return _tag_with_hotels_to_xml('order', order)

def keeps_to_xml(keeps):
    return _tag_with_hotels_to_xml('keep', keeps)

tile_to_xml = tile_to_xml

def _bool_to_xml(b):
    if b:
        return et.Element('true')
    else:
        return et.Element('false')

def booleans_to_xml(bools):
    e = et.Element('keep')
    for b in bools:
        e.append(_bool_to_xml(b))
    return e

def players_to_xml(players):
    e = et.Element('players')
    [e.append(player_to_xml(p)) for p in players]
    return e

def _result_to_xml(scores, player):
    e = et.Element('result')
    e.attrib['name'] = player.name
    e.attrib['score'] = str(scores[player.name])
    return e

def score_state_to_xml(scores, state):
    e = et.Element('score')
    [e.append(_result_to_xml(scores, p)) for p in state.players]
    e.append(state_to_xml(state))
    return e

import unittest as ut
from manager import Administrator
from player.random_player import RandomPlayer
class TestXML(ut.TestCase):

    def setUp(self):
        #example state
        admin = Administrator()
        names = ["Jim", "Sarah", "Lori"]
        players = [RandomPlayer(name) for name in names]
        map(lambda player: player.start(admin), players)
        game = admin.run_acquire_game(10)

        self.s0 = list(game)[5]

    def test_signup(self):
        name = "Bob"
        self.assertEqual(name, elt_to_signup(signup_to_xml(name)))

    def test_void(self):
        self.assertTrue(is_void(void_to_xml()))

    def test_state(self):
        self.assertEqual(self.s0, elt_to_state(state_to_xml(self.s0)))

    def test_turn(self):
        self.assertEqual(self.s0.board, elt_to_turn(turn_to_xml(self.s0.board, self.s0.players))[0])
        self.assertEqual(self.s0.players, elt_to_turn(turn_to_xml(self.s0.board, self.s0.players))[1])

    def test_pbuy(self):
        self.assertEqual((t1A, A, [S, S]), elt_to_pbuy(pbuy_to_xml(t1A, A, [S, S])))

    def test_placement(self):
        self.assertEqual((t1A, A), elt_to_placement(placement_to_xml(t1A, A)))
        self.assertEqual((t1A, None), elt_to_placement(placement_to_xml(t1A, None)))

    def test_order(self):
        self.assertEqual([A, S, T], elt_to_order(order_to_xml([A, S, T])))

    def test_keeps(self):
        self.assertEqual([W, W], elt_to_keeps(keeps_to_xml([W, W])))

    def test_booleans(self):
        self.assertEqual([True, False], elt_to_booleans(booleans_to_xml([True, False])))

    def test_players(self):
        self.assertEqual(set(self.s0.players), set(elt_to_players(players_to_xml(self.s0.players))))

    def test_score_state(self):
        score = {'Lori':5,'Jim':3,'Sarah':6}
        print score_state_to_xml(score, self.s0)
        self.assertEquals(score, elt_to_score_state(score_state_to_xml(score, self.s0))[0])
        self.assertEqual(self.s0, elt_to_score_state(score_state_to_xml(score, self.s0))[1])



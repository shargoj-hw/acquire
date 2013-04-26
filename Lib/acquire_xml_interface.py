import xml.etree.ElementTree as et
from collections import deque
from basics import *
from board  import *
from errors  import *
from state  import *
from player.player import *

################################################################################
##### Helper Methods
################################################################################
def game_state_in_progress(players, board):
    """ create a representation of a game state in progress -  only used to help run tests"""
    state = GameState([], False)
    state.players = players
    state.board = board

    # getting the deck of tiles that have been handed to players, and played, to make
    #   the deck of available tiles for the game state
    used_tiles = set([])
    for player in state.players:
        for tile in player.tiles:
            if tile in used_tiles:
                raise XMLError("same tile can only be dealt once")
            used_tiles.add(tile)

    for tile in board.board:
        if not board.is_space_free(tile):
            if tile in used_tiles:
                raise XMLError("tile in play is currently assigned to a player.")
            used_tiles.add(tile)

    for tile in used_tiles:
        state.tile_deck.remove(tile)

    used_shares = dict([(h, 0) for h in hotels])
    for player in state.players:
        for hotel, shares in player.shares_map.items():
            used_shares[hotel] += shares

    for h in hotels:
        state.shares_map[h] -= used_shares[h]
        if state.shares_map[h] < 0:
            raise XMLError("too many shares have been allocated in this game state")

    return state

################################################################################
##### XML -> Objects
################################################################################
def elt_to_tile(e):
    """ grabs a tile out of an element """
    col, row = e.attrib.get('column', None), e.attrib.get('row', None)
    if col is None or row is None:
        raise XMLError("couldn't parse a tile out of elt: "+e.tag)
    return colrow_to_tile(col, row)

def elt_to_hotel(e):
    """ grabs the hotel out of an element """
    hotel = e.attrib.get('label', e.attrib.get('name', None))
    if hotel is None:
        raise XMLError("couldn't parse a label out of elt: "+e.tag)
    elif hotel not in hotels:
        raise XMLError("Invalid label")
    return hotel

def elt_to_board(e):
    """ converts an xml object to a board. throws an XMLError if something bad happens """
    if e.tag.lower() != 'board':
        raise XMLError('tried to parse a board without a board tag')

    board = Board()
    for child in e:
        if child.tag.lower() == 'tile':
            board.board[elt_to_tile(child)] = NoHotel
        elif child.tag.lower() == 'hotel':
            hotel = elt_to_hotel(child)
            for hotel_child in child:
                board.board[elt_to_tile(hotel_child)] = hotel
        else:
            raise XMLError('unexpected tag in board: '+child.tag)
    return board

def elt_to_game_state(e):
    if e.tag.lower() != 'state':
        raise XMLError('tried to parse game state with no state tag')

    board = elt_to_board(e[0])

    # the list of players is everything in the list of children after the board
    players = deque([])
    for c in e[1:]:
        players.append(elt_to_player(c))

    if not (3 <= len(players) <= 6):
        raise XMLError("bad number of players, got {0}".format(len(players)))

    return game_state_in_progress(players,board)

def elt_to_player(elt):
    if elt.tag.lower() != 'player':
        raise XMLError('player requires a player tag')

    name = elt.attrib.get('name', None)
    cash = elt.attrib.get('cash', None)

    if name is None or cash is None:
        raise XMLError('player needs name and cash')

    try:
        cash = int(cash)
    except ValueError:
        raise XMLError('cash is not a valid number')
    if cash < 0:
        raise XMLError('money can not be negative')

    shares_map = dict([(h, 0) for h in hotels])
    tiles = set([])

    for e in elt:
        if e.tag.lower() == 'share':
            hotel = e.attrib.get('name', None)
            count = e.attrib.get('count', None)
            if hotel is None or count is None:
                raise XMLError('share needs name and count')
            if hotel not in hotels:
                raise XMLError('{0} is not a valid hotel name'.format(hotel))
            try:
                count = int(count)
            except ValueError:
                raise XMLError('count is not a valid number')
            if not 0 <= count <= 25:
                raise XMLError('count must be 25 or less')
            shares_map[hotel] = count

        if e.tag.lower() == 'tile':
            tiles.add(elt_to_tile(e))

    player = GameStatePlayer()
    player.name = name
    player.money = cash
    player.shares_map = shares_map
    player.tiles = tiles
    return player

def elt_to_share(e):
    """ Parses <share name=Label count=Nat /> into (hotel, count) """
    if e.tag.lower() != 'share':
        raise XMLError("expected share tag, got {0}".format(e.tag))
    if 'name' not in e.attrib or 'count' not in e.attrib:
        raise XMLError("name and count need to be attributes of shares")
    try:
        name = e.attrib['name']
        count = int(e.attrib['count'])
    except Exception:
        raise XMLError("problem trying to parse attributes in share")
    return name, count

def elt_to_hotels(e):
    """ Parses <hotel name=Label>Tile Tile Tile ...</hotel> into (hotel, [tile]) """
    if e.tag.lower() != 'hotel':
        raise XMLError("expected share tag, got {0}".format(e.tag))
    if 'name' not in e.attrib:
        raise XMLError("hotel has no name!")
    name = e.attrib['name']
    tiles = [elt_to_tile(t) for t in e]
    return name, tiles

def elt_to_turn(e):
    """
    Parses <take-turn cash=Cash> Board Tile ... Share ... XHotel ... </take-turn> and
    returns (Board, cash, set([tile]), dict(hotel=>count), set([hotel]))

    """
    if e.tag.lower() != 'take-turn':
        raise XMLError("expected 'take-turn' tag, got {0}".format(e.tag))
    if 'cash' not in e.attrib:
        raise XMLError("expected cash attribute on take-turn")
    try:
        cash   = int(e.attrib['cash'])
    except ValueError:
        raise XMLError("Cash is not a number, it's {0}".format(e.attrib['cash']))
    board  = elt_to_board(e[0])
    tiles  = set([elt_to_tile(t) for t in e if t.tag.lower() == 'tile'])
    shares = dict([elt_to_share(s) for s in e if s.tag.lower() == 'share'])
    hotels = set([elt_to_hotel(h) for h in e if h.tag.lower() == 'hotel'])

    if hotels != board.hotels_not_in_play:
        raise XMLError("Bad set of hotels not in play")

    return board, cash, tiles, shares, hotels

def elt_to_rounds_and_playernames(e):
    if e.tag.lower() != 'run':
        raise XMLError('Bad run tag')

    rounds = e.attrib.get('rounds', None)
    if not rounds:
        raise XMLError('bad rounds value on run element')
    else:
        try:
            rounds = int(rounds)
        except ValueError:
            raise XMLError('invalid rounds number')

    player_names = []
    for child in e:
        if child.tag.lower() != 'player':
            raise XMLError('child of run not a player tag')

        name = child.attrib.get('name', None)
        if not name:
            raise XMLError('bad name value on run element')
        player_names.append(name)

    if not (3 <= len(player_names) <= 6):
        raise XMLError('need between 3 and 6 players')

    return rounds, player_names

def elt_to_hotels(e):
    return [elt_to_hotel(xhotel) for xhotel in e]

def elt_to_query_state_orders_and_depth(e):
    query = e.tag.lower()
    if query not in ['founding', 'merging']:
        raise XMLError('bad query tag')

    try:
        depth = int(e.attrib.get('n', "Bad"))
    except ValueError:
        raise ValueError("bad n attribute on query")

    state = elt_to_game_state(e[0])
    orders = [elt_to_hotels(order) for order in e[1:]]

    return query, state, orders, depth


################################################################################
##### Objects -> XML
################################################################################
def game_state_to_xml(gamestate):
    board_elt = board_to_xml(gamestate.board)
    players = [player_to_xml(p) for p in gamestate.players]

    g = et.Element('state')
    g.append(board_elt)
    for player in sorted(players, key=lambda p: p.attrib['name']):
        g.append(player)

    return g

def player_to_xml(player):
    p = et.Element('player')
    p.attrib['name'] = str(player.name)
    p.attrib['cash'] = str(player.money)

    for hotel, count in sorted(player.shares_map.items(), key=lambda x: x[0]):
        if count != 0:
            s = et.Element('share')
            s.attrib['name'] = hotel
            s.attrib['count'] = str(count)
            p.append(s)

    for tile in sorted(list(player.tiles), key=tile_sortkey):
        p.append(tile_to_xml(tile))

    return p

def tile_to_xml(colrow):
    """ return xml for a tile at the given row/column """
    if isinstance(colrow, str):
        colrow = tile_to_colrow(colrow)
    col, row = colrow

    t = et.Element('tile')
    t.attrib['row'] = row
    t.attrib['column'] = str(col)

    return t

def hotel_to_xml(hotel, tiles):
    """ return element of xml for the given hotel with the given tiles """
    h = et.Element('hotel')
    h.attrib['name'] = hotel
    for tile in tiles:
        h.append(tile_to_xml(tile_to_colrow(tile)))
    return h

def board_to_xml(board):
    """ return xml for the given board """
    tiles = [c for c, s in board.board.items() if s == NoHotel]
    tiles.sort(key=tile_sortkey)

    b = et.Element('board')

    for tile in tiles:
        b.append(tile_to_xml(tile_to_colrow(tile)))

    for hotel, coords in sorted(
            filter(lambda (hotel, coords): len(coords) > 0, board.tiles_for_hotels.items()),
            key=lambda x: x[0]):
        coords = list(coords)
        coords.sort(key=tile_sortkey)
        b.append(hotel_to_xml(hotel, coords))

    return b

def query_response_to_xml(qr):
    """ given a query_response from Board.query(), return` an XML response """
    if qr == 'singleton':
        return et.Element('singleton')
    elif qr == 'found':
        return et.Element('founding')
    elif qr == 'invalid':
        r = et.Element('invalid')
        # TODO perhaps update this with an actual reason?
        r.attrib['msg'] = "no valid moves at this tile location"
        return r
    elif 'grow' in qr:
        r = et.Element('growing')
        r.attrib['name'] = qr[1]
        return r
    elif 'merge' in qr:
        merge, hotels = qr
        acquirer, acquirees = hotels[0][0], [h for h, s in hotels[1:]]
        m = et.Element('merging')
        m.attrib['acquirer'] = acquirer
        for i, label in enumerate(acquirees):
            m.attrib['acquired{0}'.format(i+1)] = label
        return m

def xhotel_to_xml(label):
    x = et.Element('hotel')
    x.attrib['label'] = label
    return x

def action_to_xml(tile_move, buy_move):
    """ Turns a player's turn into an action xml element.

    In:
        tile_move - TileMove preformed by the player
        buy_move  - BuyMove performed by the player
    Out:
        ElementTree - Action XML specified by the Project 6

    """
    action = et.Element('action')
    for i, hotel in enumerate(buy_move.buys):
        action.attrib['hotel{0}'.format(i+1)] = hotel

    place = et.Element('place')
    if tile_move.tile:
        col, row = tile_to_colrow(tile_move.tile)
        place.attrib['row'] = str(row)
        place.attrib['col'] = str(col)
        if tile_move.hotel:
            place.attrib['hotel'] = tile_move.hotel

        action.append(place)

    return action

def game_to_xml(states, tag):
    e = et.Element(tag)
    for state in states:
        e.append(game_state_to_xml(state))
    return e

def share_to_xml(share):
    s = et.Element('share')
    s.attrib['name']=str(share[0])
    s.attrib['count']=str(share[1])
    return s

def count_to_xml(count):
    c = et.Element('count')
    c.attrib['n'] = str(count)
    return c

def error_to_xml(msg):
    err = et.Element('error')
    err.attrib['msg'] = msg
    return err

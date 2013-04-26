# This disables contracts for speed. MUST BE CALLED HERE (before other libraries are imported)
from Lib.decontractors import use_decontractors; use_decontractors(False)

from basics import *
from board import *
from state import *
from gametree import GameTree

from Lib.box import Box

from player.ordered_player import *
from player.random_player import *

from time import sleep
from copy import deepcopy

from random import choice

class GameOverReason:
    """ Enumeration of reasons for a game of Acquire to be over """
    ALLSAFE = "All Hotels in play are safe."
    HOTELTOOBIG = "At least one Hotel on the board has reached the maximum size."
    NOMOVES = "One of the players does not have any placable tiles in his hand."
    NOMORETILES = "There are no more tiles remaining to deal to players."
    OUTOFTURNS = "The players have gone through the number of turns they were told."
    PLAYERMESSEDUP = "The player made a bad move, now nobody can have any more fun."
    NOMOREPLAYERS = "The Administrator has kicked all the players"

class Administrator():
    def __init__(self):
        """
        Fields:
            players - a deque of tuples (playername, Player)
        """
        self.players = deque([])

    def _generate_names(self, name):
        yield name
        for x in xrange(MAX_PLAYERS):
            yield name+str(x)

    def sign_up(self, name, player_reference):
        """
        To add a player to this game before it begins
        Arguments:
            name - desired name of the player
            player_type - instance of subclass of the player
        Returns:
            name' - the players actual name
        """

        for unused_name in self._generate_names(name):
            if unused_name not in self._get_player_names():
                name = unused_name
                break

        player = player_reference
        self.players.append((name, player))
        return name

    def _get_player_names(self):
        return [name for name,_ in self.players]

    def run_acquire_game(self, number_of_turns):
        """
        Arguments:
            number_of_turns - the list of turns for the game to play through

        Returns:
            a generator which lists all the turns in a game and the GameOverReason
            ex: [start_state, state_2 ... state_n-1, state_n, ALLSAFE]
        """
        gs = GameState(self._get_player_names(), handout=choice)
        gt = GameTree(gs)

        #send all initial player name/tile data to all players
        map(lambda (_, player): player.setup(deepcopy(gs)), self.players)

        yield gt.game_state

        turns_played = 0
        while turns_played < number_of_turns:
            # grab the current Player from the list of Players
            name, current_player = self.players[0]

            # is the game over? ie, can we play any tiles?
            if self.is_game_over(gt.game_state, True):
                self.send_scores(gt.game_state)
                yield self.is_game_over(gt.game_state, True)
                return

            sell_back = {}
            keeps_cheaters = []
            merger_happened = Box(False)
            current_player_cheated = Box(False)
            merger_placement = Box((None, None))
            def merger_function(tile, hotel):
                """
                Function handed to players to inform the administrator of a merge.

                Arguments:
                    tile, hotel - tile and acquiring hotel
                        Contract: Placing these results in a legal merge on the current game state.
                                  tile is owned by the current player
                Returns:
                    state, [GameStatePlayer] -
                        The GameState where other players have sold the stocks they intend to sell
                        and a list of players
                """
                state = deepcopy(gt.game_state)
                if merger_happened.get(): # this function has already been called
                    current_player_cheated.set(True)
                    return state, {} # kick!
                elif not state.board.valid_merge_placement(tile, hotel) or sell_back:
                    current_player_cheated.set(True)
                    return state, {} # kick!
                else:
                    merger_happened.set(True)
                    merger_placement.set((tile, hotel))

                acquirees = state.board.acquirees(tile, hotel)

                players_with_keeps = {}
                for _, p in self.players:
                    try:
                        players_with_keeps[p] = p.keep(deepcopy(state), acquirees)
                    except Exception as e:
                        keeps_cheaters.append(p)

                # Deal with cheaters (the jerks) # => local functions
                keeps_cheaters.extend([p for p, ks in players_with_keeps.items() if len(ks) != len(acquirees)])
                [remove_from_state(state, p) for p in keeps_cheaters]
                players_with_keeps = [(p, ks) for p, k in players_with_keeps.items() if p not in keeps_cheaters]

                # Function which given [True, False True] if acquirees are [C,A,T], returns [A]
                keeps_to_acquirees = lambda keeps: [h for h, k in zip(acquirees, keeps) if not k]

                # saves player keep data for the administrator
                for player, keeps in players_with_keeps:
                    sell_back[player.id] = keeps_to_acquirees(keeps)

                if current_player in keeps_cheaters:
                    current_player_cheated.set(True)
                    return state, {} # KICK!

                state.place_a_tile(tile, hotel)
                map(lambda p: state.sellback(p, sell_back[p], gt.game_state), sell_back.keys())

                return state, [state.player_with_name(p.id) for p, k in players_with_keeps if any(k)]

            try:
                tile, maybeHotel, shares = current_player.take_turn(deepcopy(gt.game_state), merger_function)
            except Exception as e:
                current_player_cheated = True

            for p in keeps_cheaters:
                print "cheating in keeps ", turns_played, p.id
                gt = self.kick(p, gt)

            # the current player is cheating! The bastard >:(
            # what to do in the case of the player trying to make an illegal merger
            # which causes other players to seem like they're cheating?
            # Also check that if player called merger placement
            if current_player_cheated.get() \
                    or (tile, maybeHotel) not in gt.get_tile_moves() \
                    or (merger_happened.get() and (tile, maybeHotel) != merger_placement.get()) \
                    or shares not in gt.get_share_moves(tile, maybeHotel, sell_back) \
                    or current_player in keeps_cheaters:
                print "cheating in take_turn", turns_played, current_player.id
                gt = self.kick(current_player, gt)
                continue

            new_tile = choice(gt.get_next_tiles())
            current_player.new_tile(new_tile)

            gt = gt.apply(tile, maybeHotel, sell_back, shares, new_tile)

            # finish the round and ensure that our list of Players
            # is in sync with gs's players
            yield gt.game_state

            # check to see if the game is over again,
            # now that the current player has taken his turn
            if self.is_game_over(gt.game_state, False):
                self.send_scores(gt.game_state)
                yield self.is_game_over(gt.game_state, False)
                return

            for _, p in copy(self.players):
                try:
                    p.inform(deepcopy(gt.game_state))
                except Exception as e:
                    gt = self.kick(p, gt)

            self.players.rotate(-1) # TODO: name this "CLOCKWISE"
            turns_played += 1

        self.send_scores(gt.game_state)
        yield GameOverReason.OUTOFTURNS

    def kick(self, player, gt):
        """
        Kick a misbehaving player. And return the appropriate game tree.
        Arguments:
            player - the bad player
            gt - the current game tree
        Returns:
            GameTree representing the state of the game with the player kicked.
        """
        if (player.id, player) in self.players:
            old_len = len(self.players)
            self.players.remove((player.id, player))

            assert old_len > len(self.players)

            state = gt.game_state
            self.remove_from_state(state, player.id)

            return GameTree(state)
        else:
            return gt

    def remove_from_state(self, state, playername):
        """ removes the given player from the given state """
        gsplayer = state.player_with_name(playername)

        state.players.remove(gsplayer)

        for h, s in gsplayer.shares_map.items():
            state.shares_map[h] += s

        state.tile_deck.extend(gsplayer.tiles)

    @staticmethod
    def is_game_over(gs, beginning_of_turn=False):
        """
        returns whether or not the game represented by gs is over.

        Arguments:
            gs - the GameState whose end state we're checking
            beginning_of_turn - bool representing whether or not
            we're checking at the end of the turn

        Returns:
            GameOverReason

        """
        # all hotels on the board are safe after a player completes a turn
        all_hotels_are_safe = all([gs.board.is_hotel_safe(h) for h in gs.board.hotels_in_play]) and \
                                len(gs.board.hotels_in_play) > 0

        if all_hotels_are_safe:
            return GameOverReason.ALLSAFE

        # any of the hotels on the board consists of 41 tiles after a turn
        hotels_bigger_than_max = [s for h, s in gs.board.hotels_with_sizes if s >= MAX_HOTEL_SIZE]
        any_hotel_too_big = len(hotels_bigger_than_max) != 0

        if any_hotel_too_big:
            return GameOverReason.HOTELTOOBIG

        # a player cannot place a tile on the current board
        player_tile_moves = [gs.board.query(tile) for tile in gs.current_player.tiles]
        no_possible_tile_moves = (all(['invalid' == move for move in player_tile_moves]) or \
                                    len(gs.current_player.tiles) == 0) and beginning_of_turn

        if no_possible_tile_moves:
            return GameOverReason.NOMOVES

        # the administrator runs out of tiles to hand out
        no_more_tiles = len(gs.tile_deck) == 0

        if no_more_tiles:
            return GameOverReason.NOMORETILES

        # we've kicked all the players
        if len(gs.players) == 0:
            return GameOverReason.NOMOREPLAYERS

        return False

    def send_scores(self, gs):
        """ send all the players the endgame message with scores"""
        scores = gs.final_scores()

        for name, player in self.players:
            player.end_game(scores, deepcopy(gs))

class GameRenderer:
    def __init__(self, admin, game):
        self.admin = admin
        self.game = game
        self.coord_to_label = {}
        self.name_to_label = {}

    def display_acquire_game(self):
        """
        Display a full acquire game in tkinter
        """
        import Tkinter as tk
        root = tk.Tk()
        root.resizable(0,0)
        for x, r in enumerate(rows):
            for y, c in enumerate(cols):
                l = tk.Label(root, text="{0}{1}".format(c, r), height=2, width=3)
                l.grid(row=x, column=y, sticky="NWES")
                self.coord_to_label[colrow_to_tile(c,r)] = l

        for name, _ in self.admin.players:
            l = tk.Label(root, text=name)
            self.name_to_label[name] = l
            l.grid(columnspan=5*len(cols), sticky="W")
        root.after(1000, self.render_game, root, self.game)
        root.mainloop()

    def render_state(self, gui, gamestate):
        """
        Method that renders a gamestate onto the given gui.
        Assumes that self.coord_to_label has been initialized.

        Arguments:
            gui - the Tkinter window that is being rendered to
            gamestate - the GameState that is being rendered

        """
        for tile in coords:
            square = gamestate.board[tile]
            label = self.coord_to_label[tile]
            if square in hotels:
                label.config(bg=hotel_color_map[square])
            elif square == NoHotel:
                label.config(bg='gray')
        for player in gamestate.players:
            label = self.name_to_label[player.name]
            label.config(text="{0}{1}\t{2}\t{3}\t{4}".format(
                "**" if player.name == gamestate.current_player.name else "  ",
                player.name, player.money, list(player.tiles),
                [player.shares_map[h] for h in hotels]))
        gui.update()

    def render_game(self, root, game):
        """
        Renders a game_state to the root

        Arguments:
            root - tkinter's root window object
            game - a game-state

        """
        # turns = list(game)
        for i, gs in enumerate(game):
            if isinstance(gs, str):
                print gs
            else:
                self.render_state(root, gs)
            # sleep(99/(len(turns)-i))


import unittest as ut
class TestManager(ut.TestCase):

    def test_run_acquire_game(self):
        gs = GameState("abc")
        a = Administrator()
        players = map(lambda n: RandomPlayer(n), "abc")
        map(lambda p: p.start(a), players)

        final_gs = list(a.run_acquire_game(10000))[-2]
        final_gs.printgs()
        self.assertTrue(Administrator.is_game_over(final_gs) or Administrator.is_game_over(final_gs, True))

    def test__generate_names_all_unique(self):
        a = Administrator()
        names = list(a._generate_names("name"))
        for i in range(len(names)):
            for j in range(i+1, len(names)):
                self.assertNotEqual(names[i], names[j])

    def test_is_game_over_NO(self):
        gs = GameState("abc")
        self.assertFalse(Administrator.is_game_over(gs))

    def test_is_game_over_ALLSAFE(self):
        gs = GameState("abc")
        b = Board._board_in_play([(T,['A1', 'A2', 'A3', 'A4', 'A5', 'A6',
                                      'B1', 'B2,', 'B3', 'B4', 'B5', 'B6'])])
        gs.board = b
        self.assertEqual(GameOverReason.ALLSAFE, Administrator.is_game_over(gs))

    def test_is_game_over_HOTELTOOBIG(self):
        gs = GameState("abc")
        b = Board._board_in_play([(T,['A1', 'A2', 'A3', 'A4', 'A5', 'A6',
                                      'B1', 'B2', 'B3', 'B4', 'B5', 'B6',
                                      'C1', 'C2', 'C3', 'C4', 'C5', 'C6',
                                      'D1', 'D2', 'D3', 'D4', 'D5', 'D6',
                                      'E1', 'E2', 'E3', 'E4', 'E5', 'E6',
                                      'F1', 'F2', 'F3', 'F4', 'F5', 'F6',
                                      'G1', 'G2', 'G3', 'G4', 'G5', 'G6']),
                                  (A, ['I11', 'I10'])])
        gs.board = b
        self.assertEqual(GameOverReason.HOTELTOOBIG, Administrator.is_game_over(gs))

    def test_is_game_over_OUTOFTURNS(self):
        gs = GameState("abc")
        a = Administrator()
        players = map(lambda n: RandomPlayer(n), "abc")
        map(lambda p: p.start(a), players)

        final_gs = list(a.run_acquire_game(10))[-1]
        self.assertEqual(final_gs, GameOverReason.OUTOFTURNS)

    def test_is_game_over_NOMORETILES(self):
        gs = GameState("abc")
        a = Administrator()
        players = map(lambda n: RandomPlayer(n), "abc")
        map(lambda p: p.start(a), players)

        final_gs = list(a.run_acquire_game(10000))[-1]
        print final_gs
        self.assertTrue(final_gs == GameOverReason.NOMORETILES or
                        final_gs == GameOverReason.ALLSAFE)


if __name__ == '__main__':
    from sys import argv
    if len(argv) > 1:
        gui = True
    else:
        gui = False

    admin = Administrator()
    names = ["Jim", "Sarah", "Lori"]
    players = [RandomPlayer(name) for name in names]
    map(lambda player: player.start(admin), players)
    game = admin.run_acquire_game(1000)
    if gui:
        renderer = GameRenderer(admin, game)
        renderer.display_acquire_game()
    else:
        for gs in game:
            if isinstance(gs, GameState):
                pass
            else:
                print gs

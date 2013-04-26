    _/_/_/                        _/                        _/
   _/    _/  _/  _/_/    _/_/          _/_/      _/_/_/  _/_/_/_/
  _/_/_/    _/_/      _/    _/  _/  _/_/_/_/  _/          _/
 _/        _/        _/    _/  _/  _/        _/          _/
_/        _/          _/_/    _/    _/_/_/    _/_/_/      _/_/
                             _/
                          _/

    _/    _/_/
 _/_/  _/    _/
  _/      _/
 _/    _/
_/  _/_/_/_/

This project was awesome and remote proxy patterns are THE SHIZ.

To Run:

    $ cd project12
    $ python run_admin.py IP PORT NUM_PLAYERS
    $ python run_player.py IP PORT &
        ## post should match for admin and players
        ## IP should be the IP of the administrator
        ## run enough players to start the game


    BONUS:
        to run the administrator with a gui run # B-)
        $ python run_admin.py IP PORT #PLAYERS gui
            ## (tkinter must be installed on the machine)

  - manager.py:
        Adding correct kicking behavior (this had not been implemented
        previously).

        Changing merger callback function to return a list of players
        instead of a list of player names. This was a bug on our end

        Sending players a message about their new tile, another bug on our
        end.

        Pulled our display code into its own class.

        Made some changes to accomodate a more general approach to
        handing out tiles. See state.py

  - proxymanager.py:
        A proxy manager which remote players use
        to send messages to the real admin.
  - state.py:
        Modified to make tile hand outs more general. This change
        has nothing to do with adding proxying, but was something
        we wanted to do after the last code walk.

  - Lib/remote_xml_interface.py:
        Set of functions for the translation from/to the spec's XML.
  - Lib/networking.py:
        Really cute little mixin class for basic XML communication over
        the protocol.

  - player/proxyplayer.py:
        A proxy player which the admin sends messages to
        in place of the actual players.
        It sends and recieves data over the network,
        and translates between xml and our object model.
  - player/keep_cheater.py:
        A player that sometimes cheats with their keeps.
  - player/share_cheater.py:
        A player that sometimes cheats with their shares-buying.
  - player/tile_cheater.py:
        A player that sometimes cheats with their tile placement.

  - project12/run_admin.py:
        See above, runs an administrator for NUM_PLAYERS remote players
  - project12/run_player.py:
        Runs a remote random player that connects to the given administrator
  - project12/run_cheater.py:
        Similiar to run_player, runs a cheating player.


  - basics.py:
        Nothing changed
  - board.py:
        Nothing changed
  - gametree.py:
        Nothing changed
  - Lib/acquire_xml_interface.py:
        Nothing changed
  - Lib/decontractors.py:
        Nothing changed
  - Lib/errors.py:
        Nothing changed
  - Lib/prettify.py:
        Nothing changed
  - Lib/stdin_harness.py:
        Nothing changed
  - player/ordered_player.py:
        Nothing changed
  - player/player.py:
        Nothing changed
  - player/random_player.py:
        Nothing changed
  - player/simpleplayer.py:
        Nothing changed

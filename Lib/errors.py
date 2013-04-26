class XMLError(Exception):
    def __init__(self, msg="error parsing XML"):
        self.msg = msg

class GameStateError(Exception):
    """ raised when bad things happen in GameState.
    Has a msg property with information. """
    def __init__(self, msg="generic error"):
        self.msg = msg

class PlayerError(Exception):
    """ Raised by players when something unexpected happens """
    def __init__(self, msg="generic error"):
        self.msg = msg
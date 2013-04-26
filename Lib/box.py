class Box(object):
    """ Small container for objects to be mutated in internal scopes """

    def __init__(self, value):
        """ Initialize this box with the given value """
        self._value = value

    def set(self, value):
        """ Set this box's value """
        self._value = value

    def get(self):
        """ Get this box's value. """
        return self._value

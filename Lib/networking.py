import xml.etree.ElementTree as et
from xml.parsers.expat import ExpatError
from socket import timeout
from Lib.errors import PlayerError
from Lib.remote_xml_interface import void_to_xml
from time import time

class AcquireNetworkMixin(object):
    """ A mixin-like class for simple internet communication """

    def __init__(self, connection, timeout=None):
        """ initializes this mixin with the given socket """
        self.connection = connection
        self.timeout = timeout
        if self.timeout:
            self.connection.settimeout(self.timeout)

    def recieve(self):
        """
        Recieve xml from the connection.

        Returns:
            ElementTree element representing the XML data we got over the wire.
        """
        # TODO harden against bad xml
        start_time = time()
        msg = ""
        while 1:
            # loop until we recieve a valid piece of xml
            recv = self.connection.recv(8192)
            msg += recv
            # print "recieved", msg
            try:
                return et.fromstring(msg)
            except ExpatError as e:
                if self.timeout is not None and time()-start_time > self.timeout:
                    raise PlayerError("connection timedout")
            except timeout as e:
                raise PlayerError("connection timedout")

    def respond_with_void(self):
        """ send a void reponse over the wire """
        self.send(void_to_xml())

    def send(self, elmt):
        """
        Send xml over this connection

        Arguments:
            elmt - elementtree, xml representation of data
        """
        # print "sending", et.tostring(elmt)
        self.connection.send(et.tostring(elmt))

    def send_and_accept_void_response(self, xml):
        """ send a message which expects a <void/> response """

        self.send(xml)
        ret = self.recieve()

        if ret.tag.lower() != 'void':
            raise PlayerError("bad xml response")

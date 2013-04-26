import xml.etree.ElementTree as et
from xml.dom import minidom as md
import re

def prettify(elem):
    """ Return a pretty-printed XML string for the Element..
        source modified from:
        http://blog.doughellmann.com/2010/03/pymotw-creating-xml-documents-with.html
    """
    rough_string = et.tostring(elem)
    reparsed = md.parseString(rough_string)
    # toprettyxml prints a metadata tag at the beginning of the xml, which we do not want
    #   so we sub it out.
    return re.sub('^.*\n', '', reparsed.toprettyxml(indent='\t'))

from optparse import OptionParser
import xml.etree.ElementTree as et
from basics import *
from errors  import *
from prettify import prettify
from acquire_xml_interface import *

class StdinXMLHarness:
    """ master class for xml harnesses that read from stdin and write to stdout"""

    @classmethod
    def process_xml_request(cls, e):
        """ returns the element-object result of the given xml request """
        pass

    @classmethod
    def run_from_stdin(cls):
        xml = sys.stdin.read()

        try:
            e = et.fromstring('<root>'+xml+'</root>')
        except Exception, err:
            return

        for child in e:
            try:
                print prettify(cls.process_xml_request(child))
            except XMLError, e:
                print prettify(error_to_xml('badly formatted xml: '+e.msg))
                return

    @classmethod
    def run_test_files(cls, d):
        ''' run all of the tests found in the directory. assumes there's a pair in/outX.xml for each test '''
        in_tests = [name for name in os.listdir(d) if os.path.isfile(os.path.join(d,name)) and 'in' in name]
        out_tests = [name for name in os.listdir(d) if os.path.isfile(os.path.join(d,name)) and 'out' in name]
        in_tests.sort(); out_tests.sort()

        for i, o in zip(in_tests, out_tests):
            with open(os.path.join(d,i)) as i_file:
                xml_i = i_file.read()
            try:
                e = et.fromstring('<root>'+xml_i+'</root>')
            except Exception:
                print "!!!!! SOMETHING TERRIBLE HAPPENED PARSING: " + i
                continue

            out = ''
            for child in e:
                try:
                    out += cls.process_xml_request(child) + '\n'
                except XMLError as err:
                    out += error_to_xml('badly formatted xml: '+err.msg) + '\n'
            print 'expected output for {0}:'.format(o)
            with open(os.path.join(d, o)) as o_file:
                print o_file.read()
            print 'output for {0}:'.format(i)
            print out


    @classmethod
    def parse_options_and_run(cls):
        parser = OptionParser()
        parser.add_option('-r', '--run-tests', help="run tests from given directory", action='store', dest='run_tests')
        opts, args = parser.parse_args()

        if opts.run_tests:
            cls.run_test_files(opts.run_tests)
        else:
            cls.run_from_stdin()


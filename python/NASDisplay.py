#!/usr/bin/env python

from __future__ import absolute_import
import fcntl
import atexit
import codecs
import sys
import threading
import socket
import serial
import sensors
from serial.tools.list_ports import comports
from serial.tools import hexlify_codec

LCDlines = []
receivedString = ''

codecs.register(lambda c: hexlify_codec.getregentry()
                if c == 'hexlify' else None)

try:
    raw_input
except NameError:
    # pylint: disable=redefined-builtin,invalid-name
    raw_input = input   # in python3 it's "raw"
    unichr = chr
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


class Transform(object):
    """do-nothing: forward all data unchanged"""

    def rx(self, text):
        """text received from serial port"""
        return text

    def tx(self, text):
        """text to be sent to serial port"""
        return text


class CRLF(Transform):
    """ENTER sends CR+LF"""

    def tx(self, text):
        return text.replace('\n', '\r\n')


class CR(Transform):
    """ENTER sends CR"""

    def rx(self, text):
        return text.replace('\r', '\n')

    def tx(self, text):
        return text.replace('\n', '\r')


class LF(Transform):
    """ENTER sends LF"""


class NoTerminal(Transform):
    """remove typical terminal control codes from input"""

    REPLACEMENT_MAP = dict((x, 0x2400 + x)
                           for x in range(32) if unichr(x) not in '\r\n\b\t')
    REPLACEMENT_MAP.update(
        {
            0x7F: 0x2421,  # DEL
            0x9B: 0x2425,  # CSI
        })

    def rx(self, text):
        return text.translate(self.REPLACEMENT_MAP)


class Printable(Transform):
    """Show decimal code for all non-ASCII characters and replace most control codes"""

    def rx(self, text):
        r = []
        for c in text:
            if ' ' <= c < '\x7f' or c in '\r\n\b\t':
                r.append(c)
            elif c < ' ':
                r.append(unichr(0x2400 + ord(c)))
            else:
                r.extend(unichr(0x2080 + ord(d) - 48)
                         for d in '{:d}'.format(ord(c)))
                r.append(' ')
        return ''.join(r)


class DebugIO(Transform):
    """Print what is sent and received"""

    def rx(self, text):
        sys.stderr.write(' [RX:{!r}] '.format(text))
        sys.stderr.flush()
        return text

    def tx(self, text):
        sys.stderr.write(' [TX:{!r}] '.format(text))
        sys.stderr.flush()
        return text


# other ideas:
# - add date/time for each newline
# - insert newline after: a) timeout b) packet end character

EOL_TRANSFORMATIONS = {
    'crlf': CRLF,
    'cr': CR,
    'lf': LF,
}

TRANSFORMATIONS = {
    'direct': Transform,    # no transformation
    'default': NoTerminal,
    'printable': Printable,
    'debug': DebugIO,
}


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class NASDisplay(object):
    """
    Show status on NAS and interpret button press
    """

    def __init__(self, serial_instance,  eol='crlf', filters=()):
        self.serial = serial_instance
        self.raw = False
        self.input_encoding = 'UTF-8'
        self.output_encoding = 'UTF-8'
        self.eol = eol
        self.filters = filters
        self.update_transformations()
        self.alive = None
        self._reader_alive = None
        self.receiver_thread = None
        self.rx_decoder = None
        self.tx_decoder = None
        sensors.init()

    def _start_reader(self):
        """Start reader thread"""
        self._reader_alive = True
        # start serial->console thread
        self.receiver_thread = threading.Thread(target=self.reader, name='rx')
        self.receiver_thread.daemon = True
        self.receiver_thread.start()

    def _stop_reader(self):
        """Stop reader thread only, wait for clean exit of thread"""
        self._reader_alive = False
        if hasattr(self.serial, 'cancel_read'):
            self.serial.cancel_read()
        self.receiver_thread.join()

    def start(self):
        """start worker threads"""
        self.alive = True
        self._start_reader()

    def stop(self):
        """set flag to stop worker threads"""
        self.alive = False

    def join(self, transmit_only=False):
        """wait for worker threads to terminate"""
        if not transmit_only:
            if hasattr(self.serial, 'cancel_read'):
                self.serial.cancel_read()
            self.receiver_thread.join()

    def close(self):
        self.serial.close()
        sensors.cleanup()

    def update_transformations(self):
        """take list of transformation classes and instantiate them for rx and tx"""
        transformations = [EOL_TRANSFORMATIONS[self.eol]] + [TRANSFORMATIONS[f]
                                                             for f in self.filters]
        self.tx_transformations = [t() for t in transformations]
        self.rx_transformations = list(reversed(self.tx_transformations))

    def set_rx_encoding(self, encoding, errors='replace'):
        """set encoding for received data"""
        self.input_encoding = encoding
        self.rx_decoder = codecs.getincrementaldecoder(encoding)(errors)

    def set_tx_encoding(self, encoding, errors='replace'):
        """set encoding for transmitted data"""
        self.output_encoding = encoding
        self.tx_encoder = codecs.getincrementalencoder(encoding)(errors)

    def reader(self):
        """loop and copy serial->console"""
        global receivedString

        print 'reader started \n'

        try:
            while self.alive and self._reader_alive:

                # read all that is there or wait for one byte
                data = self.serial.read(self.serial.in_waiting or 1)

                if data is not '':
                    receivedString += data
                    self.evaluateResponse(receivedString)

        except serial.SerialException:
            self.alive = False
            raise       # XXX handle instead of re-raise?

    def evaluateResponse(self, message):
        global receivedString
        global LCDlines
        # print 'evaluateResponse called \n'
        # print message

        if 'UP' in message:
            self.makeLCDLines()
            print 'UP found\n'
            receivedString = ''
            sendString = LCDlines[0]+';'+LCDlines[1]
            self.serial.write(sendString)

        if 'DOWN' in message:
            print 'DOWN found\n'
            receivedString = ''

        if 'SELECT' in message:
            print 'SELECT found\n'
            receivedString = ''
            sys.exit(1)

    def makeLCDLines(self):
        global LCDlines
        LCDlines = []
        host_name = socket.gethostname()
        myIP = socket.gethostbyname(host_name + ".local")
        print myIP
        LCDlines.append(myIP)
        #LCDlines.append("some text1")
        #LCDlines.append("some text2")
        sensors.init()
        #print sensors
        # mylist=sensors.iter_detected_chips()
        #print mylist
        try:
            for chip in sensors.iter_detected_chips():
                print '%s at %s' % (chip, chip.adapter_name)
                templine=''
#                if chip.has_key('feature') == 1:
 #                   for feature in chip:
  #                      if 'temp1' in feature.label:
   #                         templine = 'Temp %.2fC' % (feature.get_value())
    #                        print 'Temp %.2fC' % (feature.get_value())
                            #print ' %s: %.2f' % (feature.label, feature.get_value())
        finally:
            sensors.cleanup()
        LCDlines.append(templine)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# default args can be used to override when calling main() from an other script
# e.g to create a nasDisplay-my-device.py


def main(default_port='/dev/ttyACM0', default_baudrate=9600, default_rts=None, default_dtr=None):
    """Command line tool, entry point"""

    import argparse

    parser = argparse.ArgumentParser(
        description='NASDisplay - A simple terminal program for the serial port.')

    parser.add_argument(
        'port',
        nargs='?',
        help='serial port name ("-" to show port list)',
        default=default_port)

    parser.add_argument(
        'baudrate',
        nargs='?',
        type=int,
        help='set baud rate, default: %(default)s',
        default=default_baudrate)

    group = parser.add_argument_group('port settings')

    group.add_argument(
        '--parity',
        choices=['N', 'E', 'O', 'S', 'M'],
        type=lambda c: c.upper(),
        help='set parity, one of {N E O S M}, default: N',
        default='N')

    group.add_argument(
        '--rtscts',
        action='store_true',
        help='enable RTS/CTS flow control (default off)',
        default=False)

    group.add_argument(
        '--xonxoff',
        action='store_true',
        help='enable software flow control (default off)',
        default=False)

    group.add_argument(
        '--rts',
        type=int,
        help='set initial RTS line state (possible values: 0, 1)',
        default=default_rts)

    group.add_argument(
        '--dtr',
        type=int,
        help='set initial DTR line state (possible values: 0, 1)',
        default=default_dtr)

    group.add_argument(
        '--non-exclusive',
        dest='exclusive',
        action='store_false',
        help='disable locking for native ports',
        default=True)

    group.add_argument(
        '--ask',
        action='store_true',
        help='ask again for port when open fails',
        default=False)

    group.add_argument(
        '--encoding',
        dest='serial_port_encoding',
        metavar='CODEC',
        help='set the encoding for the serial port (e.g. hexlify, Latin1, UTF-8), default: %(default)s',
        default='UTF-8')

    group.add_argument(
        '-f', '--filter',
        action='append',
        metavar='NAME',
        help='add text transformation',
        default=[])

    group.add_argument(
        '--eol',
        choices=['CR', 'LF', 'CRLF'],
        type=lambda c: c.upper(),
        help='end of line mode',
        default='CRLF')

    group.add_argument(
        '--raw',
        action='store_true',
        help='Do no apply any encodings/transformations',
        default=False)

    group.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='suppress non-error messages',
        default=False)

    group.add_argument(
        '--develop',
        action='store_true',
        help='show Python traceback on error',
        default=False)

    args = parser.parse_args()

    if args.filter:
        if 'help' in args.filter:
            sys.stderr.write('Available filters:\n')
            sys.stderr.write('\n'.join(
                '{:<10} = {.__doc__}'.format(k, v)
                for k, v in sorted(TRANSFORMATIONS.items())))
            sys.stderr.write('\n')
            sys.exit(1)
        filters = args.filter
    else:
        filters = ['default']

    while True:
        try:
            serial_instance = serial.serial_for_url(
                args.port,
                args.baudrate,
                parity=args.parity,
                rtscts=args.rtscts,
                xonxoff=args.xonxoff,
                do_not_open=True)

            if not hasattr(serial_instance, 'cancel_read'):
                # enable timeout for alive flag polling if cancel_read is not available
                serial_instance.timeout = 1

            if args.dtr is not None:
                if not args.quiet:
                    sys.stderr.write(
                        '--- forcing DTR {}\n'.format('active' if args.dtr else 'inactive'))
                serial_instance.dtr = args.dtr
            if args.rts is not None:
                if not args.quiet:
                    sys.stderr.write(
                        '--- forcing RTS {}\n'.format('active' if args.rts else 'inactive'))
                serial_instance.rts = args.rts

            if isinstance(serial_instance, serial.Serial):
                serial_instance.exclusive = args.exclusive

            serial_instance.open()
        except serial.SerialException as e:
            sys.stderr.write(
                'could not open port {!r}: {}\n'.format(args.port, e))
            if args.develop:
                raise
            if not args.ask:
                sys.exit(1)
            else:
                args.port = '-'
        else:
            break

    nasDisplay = NASDisplay(
        serial_instance,
        eol=args.eol.lower(),
        filters=filters)
    nasDisplay.raw = args.raw
    nasDisplay.set_rx_encoding(args.serial_port_encoding)
    nasDisplay.set_tx_encoding(args.serial_port_encoding)

    if not args.quiet:
        sys.stderr.write('--- NASDisplay on {p.name}  {p.baudrate},{p.bytesize},{p.parity},{p.stopbits} ---\n'.format(
            p=nasDisplay.serial))

    nasDisplay.start()
    try:
        nasDisplay.join(True)
    except KeyboardInterrupt:
        pass
    if not args.quiet:
        sys.stderr.write('\n--- exit ---\n')
    nasDisplay.join()
    nasDisplay.close()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if __name__ == '__main__':
    main()

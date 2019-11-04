#!/usr/bin/env python

from __future__ import absolute_import
import fcntl
import atexit
import sys
import os
import threading
import socket
import serial
import sensors
from serial.tools.list_ports import comports
from serial.tools import hexlify_codec
from time import sleep

receivedString = ''
timerCount = 0


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class ShutDownTest(object):
    """
    Show status on NAS and interpret button press
    """

    def __init__(self, serial_instance,  eol='crlf'):
        self.serial = serial_instance
        self.eol = eol
        self.alive = None
        self._reader_alive = None
        self.receiver_thread = None
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
        # start timer thread
        self.Timer_thread = threading.Thread(target=self.myTimer)
        self.Timer_thread.setDaemon(1)
        self.Timer_thread.start()

    def stop(self):
        """set flag to stop worker threads"""
        self.alive = False
        sys.exit(1)

    def join(self, transmit_only=False):
        """wait for worker threads to terminate"""
        if not transmit_only:
            if hasattr(self.serial, 'cancel_read'):
                self.serial.cancel_read()
            self.receiver_thread.join()

    def myTimer(self):
        global spin
        global LCDlines
        global timerCount
        while True:
            sleep(2)
            timerCount = timerCount+1
            print 'timerCount %d' % timerCount
            if timerCount == 3:
                print 'Ive had enough'
                #self.close()
                #sys.exit(1)
                #print 'called sys.exit'

    def close(self):
        self.serial.close()
        sensors.cleanup()

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
                    # print 'receivedString before: %s' % receivedString
                    if self.evaluateResponse(receivedString) == 1:
                        receivedString = ''
                    # print 'receivedString after: %s' % receivedString

        except serial.SerialException:
            self.alive = False
            raise       # XXX handle instead of re-raise?

    def evaluateResponse(self, message):
        if 'SELECT' in message:
            sys.exit(1)
            return 1


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# default args can be used to override when calling main() from an other script
# e.g to create a shutDownTest-my-device.py


def main(default_port='/dev/ttyACM0', default_baudrate=9600, default_rts=None, default_dtr=None):
    """Command line tool, entry point"""

    import argparse

    parser = argparse.ArgumentParser(
        description='ShutDownTest - A simple terminal program for the serial port.')

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
        '--eol',
        choices=['CR', 'LF', 'CRLF'],
        type=lambda c: c.upper(),
        help='end of line mode',
        default='CRLF')

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

    while True:
        try:
            serial_instance = serial.serial_for_url(
                args.port,
                args.baudrate,
                parity=args.parity,
                rtscts=args.rtscts,
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

    shutDownTest = ShutDownTest(
        serial_instance,
        eol=args.eol.lower())

    if not args.quiet:
        sys.stderr.write('--- ShutDownTest create /tmp/sdyes to initiate shutdown---\n'.format(
            p=shutDownTest.serial))

    shutDownTest.start()
    try:
        shutDownTest.join(True)
    except KeyboardInterrupt:
        pass
    if not args.quiet:
        sys.stderr.write('\n--- exit ---\n')
    shutDownTest.join()
    shutDownTest.close()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if __name__ == '__main__':
    main()

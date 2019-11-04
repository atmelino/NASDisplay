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
    
    def __init__(self, serial_instance):
        self.serial = serial_instance
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
        global timerCount
        while True:
            sleep(2)
            timerCount = timerCount+1
            print 'timerCount %d' % timerCount
            if timerCount == 3:
                print 'Ive had enough'
                self._stop_reader()
                #self.close()
                sys.exit(1)
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
                print 'after read command \n'

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

    while True:
        try:
            serial_instance = serial.serial_for_url(
                '/dev/ttyACM0',
                9600,
                do_not_open=True)

            if not hasattr(serial_instance, 'cancel_read'):
                # enable timeout for alive flag polling if cancel_read is not available
                serial_instance.timeout = 1

            if isinstance(serial_instance, serial.Serial):
                serial_instance.exclusive = '--non-exclusive'

            serial_instance.open()
        except serial.SerialException as e:
            sys.stderr.write(
                'could not open port {!r}: {}\n'.format('/dev/ttyACM0', e))
        else:
            break

    shutDownTest = ShutDownTest(
        serial_instance)

    sys.stderr.write('--- ShutDownTest create /tmp/sdyes to initiate shutdown---\n')

    shutDownTest.start()
    try:
        shutDownTest.join(True)
    except KeyboardInterrupt:
        pass

    shutDownTest.join()
    shutDownTest.close()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if __name__ == '__main__':
    main()

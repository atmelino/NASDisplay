#!/usr/bin/env python

from __future__ import absolute_import
import fcntl
import atexit
import sys
import os
import threading
import socket
from time import sleep


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class ShutDownTest(object):
    def __init__(self):
        self.alive = None

    def start(self):
        """start worker threads"""
        self.alive = True
        # start timer thread
        self.Timer_thread = threading.Thread(target=self.myTimer)
        self.Timer_thread.setDaemon(1)
        self.Timer_thread.start()

    def stop(self):
        """set flag to stop worker threads"""
        self.alive = False
        sys.exit(1)

    def myTimer(self):
        global spin
        global LCDlines
        while True:
            sleep(2)
            print 'timer\n'

    def close(self):
        print 'closing\n'


def main():
    shutDownTest = ShutDownTest()

    sys.stderr.write(
        '--- ShutDownTest  create file /tmp/sdyes to activate ---\n')

    shutDownTest.start()
    #shutDownTest.join()
    # shutDownTest.close()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if __name__ == '__main__':
    main()


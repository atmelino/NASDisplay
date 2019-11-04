#!/usr/bin/env python

from __future__ import absolute_import
import fcntl
import atexit
import sys
import os
import threading
from time import sleep

timerCount = 0

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
        sleep(10)


    def stop(self):
        """set flag to stop worker threads"""
        self.alive = False
        sys.exit(1)

    def join(self, transmit_only=False):
        """wait for worker threads to terminate"""

    def myTimer(self):
        global timerCount
        while True:
            sleep(2)
            timerCount = timerCount+1
            print 'timerCount %d' % timerCount
            if timerCount == 3:
                print 'Ive had enough'
                self.stop()
                sys.exit(1)
                #print 'called sys.exit'

    def close(self):
        print 'close'

def main():

    shutDownTest = ShutDownTest()

    sys.stderr.write('--- ShutDownTest create /tmp/sdyes to initiate shutdown---\n')

    shutDownTest.start()
    shutDownTest.join()
    shutDownTest.close()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if __name__ == '__main__':
    main()

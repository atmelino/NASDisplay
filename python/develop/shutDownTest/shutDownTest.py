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
        global timerCount
        while True:
            sleep(2)

            if os.path.exists('/tmp/sdyes') == True:
                print 'file exists'
                #sys.exit(1)
                #os.system('shutdown /s /t 1');
                #os.system('shutdown -s -t 0') 
                
                #os.system('systemctl poweroff') 

                os.system('shutdown -h now')


            else:
                print 'file does not exist'

            timerCount = timerCount+1
            print 'timerCount %d' % timerCount        
            #if timerCount == 20:
                #print 'Ive had enough'
                #sys.exit(1)


def main():

    shutDownTest = ShutDownTest()

    sys.stderr.write(
        '--- ShutDownTest create /tmp/sdyes to initiate shutdown---\n')

    shutDownTest.start()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if __name__ == '__main__':
    main()

#!/usr/bin/env python3

import sys
from time import sleep
from subprocess import PIPE, STDOUT, Popen
from threading  import Thread
from queue import Queue, Empty


VALGRIND = '/usr/bin/valgrind'
XTERM = '/usr/bin/xterm'
LS = '/usr/bin/ls'
ON_POSIX = 'posix' in sys.builtin_module_names


def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

def main():
    p = Popen([VALGRIND, XTERM], stdout=PIPE, stderr=STDOUT, bufsize=1, universal_newlines=True, close_fds=ON_POSIX)
    q = Queue()
    t = Thread(target=enqueue_output, args=(p.stdout, q))
    t.daemon = True # thread dies with the program
    t.start()
    
    
    i = 0
    while True:
        print(i)
        # read line without blocking
        try:  line = q.get_nowait() # or q.get(timeout=.1)
        except Empty:
            pass
        else: # got line
            print(line)
        i += 1
        sleep(1)

if __name__ == '__main__':
    main()

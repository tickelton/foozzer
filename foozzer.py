#!/usr/bin/env python3

import sys
import subprocess
import pyautogui
from time import sleep
from subprocess import PIPE, STDOUT, Popen
from threading  import Thread
from queue import Queue, Empty


VALGRIND = '/usr/bin/valgrind'
XTERM = '/usr/bin/xterm'
LS = '/usr/bin/ls'
NEW_PLAYLIST = r'D:\Workspace\foozzer\images\new_playlist.png'
RM_PL = r'D:\Workspace\foozzer\images\remove_playlist.png'
TITLE_INFORMATION = r'D:\Workspace\foozzer\images\information.png'
PL_GARBAGE = r'D:\Workspace\foobar_fuzzing\in\garbage.fpl'
PL_GENERIC = r'D:\Workspace\foobar_fuzzing\in\generic.fpl'
FOOBAR = r'C:\Program Files (x86)\foobar2000\foobar2000.exe'
CMD_STOP = '/stop'
ON_POSIX = 'posix' in sys.builtin_module_names


def cmd_stop():
    subprocess.run([FOOBAR, CMD_STOP])

def pl_generic():
    subprocess.run([FOOBAR, PL_GENERIC])

def pl_garbage():
    subprocess.run([FOOBAR, PL_GARBAGE])

def del_new_pl():
    new_pl = pyautogui.locateOnScreen(NEW_PLAYLIST)
    if new_pl:
        new_pl_center = pyautogui.center(new_pl)
        pyautogui.click(button='right', x=new_pl_center.x, y=new_pl_center.y)
        del_pl = pyautogui.locateOnScreen(RM_PL)
        del_pl_center = pyautogui.center(del_pl)
        pyautogui.click(x=del_pl_center.x, y=del_pl_center.y)

def close_info():
    win_info = pyautogui.locateOnScreen(TITLE_INFORMATION)
    if win_info:
        pyautogui.click(x=win_info.left+win_info.width-5, y=win_info.top+5)

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

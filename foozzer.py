#!/usr/bin/env python3

import sys
import subprocess
import pyautogui
from time import sleep
from subprocess import PIPE, STDOUT, Popen
from threading  import Thread
from queue import Queue, Empty


# binaries
VALGRIND = '/usr/bin/valgrind'
XTERM = '/usr/bin/xterm'
LS = '/usr/bin/ls'
FOOBAR = r'C:\Program Files (x86)\foobar2000\foobar2000.exe'

# playlists
PL_GARBAGE = r'D:\Workspace\foobar_fuzzing\in\garbage.fpl'
PL_GENERIC = r'D:\Workspace\foobar_fuzzing\in\generic.fpl'
PL_FUZZ = r'D:\Workspace\foobar_fuzzing\in\fuzz_pl.fpl'

# buttons
NEW_PLAYLIST = r'D:\Workspace\foozzer\images\new_playlist.png'
RM_PL = r'D:\Workspace\foozzer\images\remove_playlist.png'
TITLE_INFORMATION = r'D:\Workspace\foozzer\images\information.png'
LOAD_PL = r'D:\Workspace\foozzer\images\load_playlist.png'
MENU_FILE = r'D:\Workspace\foozzer\images\file.png'
MENU_FUZZ_PL = r'D:\Workspace\foozzer\images\fuzz_pl.png'

# commands
CMD_STOP = '/stop'
CMD_LOAD_PL = '/command:"Load playlist..."'

# misc constants
PL_FUZZ_NAME = 'fuzz_pl.fpl'
ON_POSIX = 'posix' in sys.builtin_module_names


def run_cmd(cmd_str):
    subprocess.run([FOOBAR, cmd_str])

def del_pl(btn_pl_img):
    btn_pl = pyautogui.locateOnScreen(btn_pl_img)
    if btn_pl:
        btn_pl_center = pyautogui.center(btn_pl)
        pyautogui.click(button='right', x=btn_pl_center.x, y=btn_pl_center.y)
        del_pl = pyautogui.locateOnScreen(RM_PL)
        del_pl_center = pyautogui.center(del_pl)
        pyautogui.click(x=del_pl_center.x, y=del_pl_center.y)

def load_pl(pl_name):
    btn_file = pyautogui.locateOnScreen(MENU_FILE)
    if btn_file:
        btn_file_center = pyautogui.center(btn_file)
        pyautogui.click(x=btn_file_center.x, y=btn_file_center.y)
        btn_load = pyautogui.locateOnScreen(LOAD_PL)
        btn_load_center = pyautogui.center(btn_load)
        pyautogui.click(x=btn_load_center.x, y=btn_load_center.y)
        pyautogui.write(pl_name)
        pyautogui.press('enter')

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

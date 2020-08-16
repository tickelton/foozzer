#!/usr/bin/env python3

import os
import sys
import subprocess
import pyautogui
from time import sleep
from shutil import copyfile
from subprocess import PIPE, STDOUT, Popen
from threading  import Thread
from queue import Queue, Empty


# binaries
VALGRIND = '/usr/bin/valgrind'
XTERM = '/usr/bin/xterm'
LS = '/usr/bin/ls'
FOOBAR = r'C:\Program Files (x86)\foobar2000\foobar2000.exe'
DRMEMORY = r'C:\Program Files (x86)\Dr. Memory\bin\drmemory.exe'

# playlists
PL_GARBAGE = r'D:\Workspace\foobar_fuzzing\in\garbage.fpl'
PL_GENERIC = r'D:\Workspace\foobar_fuzzing\in\generic.fpl'
PL_FUZZ = r'D:\Workspace\foobar_fuzzing\in\fuzz_pl.fpl'
PL_TEMPLATE = r'D:\Workspace\foobar_fuzzing\in\fuzzing_base.fpl'

# buttons
NEW_PLAYLIST = r'D:\Workspace\foozzer\images\new_playlist.png'
RM_PL = r'D:\Workspace\foozzer\images\remove_playlist.png'
TITLE_INFORMATION = r'D:\Workspace\foozzer\images\information2.png'
LOAD_PL = r'D:\Workspace\foozzer\images\load_playlist.png'
MENU_FILE = r'D:\Workspace\foozzer\images\file.png'
MENU_FUZZ_PL = r'D:\Workspace\foozzer\images\fuzz_pl.png'

# commands
CMD_STOP = '/stop'
CMD_LOAD_PL = '/command:"Load playlist..."'

# misc constants
RUNFILE = r'D:\Temp\foozzer.run'
LOG_OUTFILE = r'D:\Workspace\foobar_fuzzing\out\log.txt'
PL_FUZZ_NAME = 'fuzz_pl.fpl'
ON_POSIX = 'posix' in sys.builtin_module_names


def run_cmd(cmd_str):
    subprocess.run([FOOBAR, cmd_str])

def del_pl(btn_pl_img):
    btn_pl = pyautogui.locateOnScreen(btn_pl_img)
    if btn_pl:
        btn_pl_center = pyautogui.center(btn_pl)
        pyautogui.click(button='right', x=btn_pl_center.x, y=btn_pl_center.y)
        sleep(1)
        del_pl = pyautogui.locateOnScreen(RM_PL)
        del_pl_center = pyautogui.center(del_pl)
        pyautogui.click(x=del_pl_center.x, y=del_pl_center.y)

def load_pl(pl_name):
    btn_file = pyautogui.locateOnScreen(MENU_FILE)
    if btn_file:
        btn_file_center = pyautogui.center(btn_file)
        pyautogui.click(x=btn_file_center.x, y=btn_file_center.y)
        sleep(1)
        btn_load = pyautogui.locateOnScreen(LOAD_PL)
        btn_load_center = pyautogui.center(btn_load)
        pyautogui.click(x=btn_load_center.x, y=btn_load_center.y)
        sleep(1)
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



def create_next_input(filename, template):
    outfile = open(filename, 'wb')
    infile = open(template, 'rb', buffering=0)

class FPLInFile:
    GARBAGE_PATTERN = b'Aa0Aa1Aa2Aa3Aa4Aa5Aa6Aa7Aa8Aa9Ab0Ab1Ab2Ab3Ab4Ab5Ab6Ab7Ab8Ab9Ac0Ac1Ac2Ac3Ac4Ac5Ac6Ac7Ac8Ac9Ad0Ad1Ad2Ad3Ad4Ad5Ad6Ad7Ad8Ad9Ae0Ae1Ae2Ae3Ae4Ae5Ae6Ae7Ae8Ae9Af0Af1Af2Af3Af4Af5Af6Af7Af8Af9Ag0Ag1Ag2Ag3Ag4Ag5Ag6Ag7Ag8Ag9Ah0Ah1Ah2Ah3Ah4Ah5Ah6Ah7Ah8Ah9Ai0Ai1Ai2Ai3Ai4Ai5Ai6Ai7Ai8Ai9Aj0Aj1Aj2Aj3Aj4Aj5Aj6Aj7Aj8Aj9Ak0Ak1Ak2Ak3Ak4Ak5Ak6Ak7Ak8Ak9Al0Al1Al2Al3Al4Al5Al6Al7Al8Al9Am0Am1Am2Am3Am4Am5Am6Am7Am8Am9An0An1An2An3An4An5An6An7An8An9Ao0Ao1Ao2Ao3Ao4Ao5Ao6Ao7Ao8Ao9Ap0Ap1Ap2Ap3Ap4Ap5Ap6Ap7Ap8Ap9Aq0Aq1Aq2Aq3Aq4Aq5Aq6Aq7Aq8Aq9Ar0Ar1Ar2Ar3Ar4Ar5Ar6Ar7Ar8Ar9As0As1As2As3As4As5As6As7As8As9At0At1At2At3At4At5At6At7At8At9Au0Au1Au2Au3Au4Au5Au6Au7Au8Au9Av0Av1Av2Av3Av4Av5Av6Av7Av8Av9Aw0Aw1Aw2Aw3Aw4Aw5Aw6Aw7Aw8Aw9Ax0Ax1Ax2Ax3Ax4Ax5Ax6Ax7Ax8Ax9Ay0Ay1Ay2Ay3Ay4Ay5Ay6Ay7Ay8Ay9Az0Az1Az2Az3Az4Az5Az6Az7Az8Az9Ba0Ba1Ba2Ba3Ba4Ba5Ba6Ba7Ba8Ba9Bb0Bb1Bb2Bb3Bb4Bb5Bb6Bb7Bb8Bb9Bc0Bc1Bc2Bc3Bc4Bc5Bc6Bc7Bc8Bc9Bd0Bd1Bd2Bd3Bd4Bd5Bd6Bd7Bd8Bd9Be0Be1Be2Be3Be4Be5Be6Be7Be8Be9Bf0Bf1Bf2Bf3Bf4Bf5Bf6Bf7Bf8Bf9Bg0Bg1Bg2Bg3Bg4Bg5Bg6Bg7Bg8Bg9Bh0Bh1Bh2Bh3Bh4Bh5Bh6Bh7Bh8Bh9Bi0B'

    byte_mods = [
        b'\x00',
        b'\x01',
        b'\xff',
        b'\x00\x00',
        b'\x00\x01',
        b'\x01\x00',
        b'\x00\xff',
        b'\xff\x00',
        b'\xff\xff',
        b'\x00\x00\x00',
        b'\x00\x00\x01',
        b'\x01\x00\x00',
        b'\x00\x00\xff',
        b'\xff\x00\x00',
        b'\x00\xff\xff',
        b'\xff\xff\x00',
        b'\xff\xff\xff',
        b'\x00\x00\x00\x00',
        b'\x00\x00\x00\x01',
        b'\x01\x00\x00\x00',
        b'\x00\x00\x00\xff',
        b'\xff\x00\x00\x00',
        b'\x00\x00\xff\xff',
        b'\xff\xff\x00\x00',
        b'\xff\xff\xff\x00',
        b'\x00\xff\xff\xff',
        b'\xff\xff\xff\xff',
    ]

    template_offset = 0
    mod_offset = 0

    def __init__(self, outpath, template_path):
        self.outpath = outpath
        with open(template_path, 'rb') as infile:
            self.template = infile.read()
        self.template_size = len(self.template)

    def next(self):
        if self.template_offset > self.template_size - 1:
            return (-1, -1)

        t_cur = self.template_offset
        m_cur = self.mod_offset

        with open(self.outpath, 'wb') as outfile:

            outfile.write(self.template)
            outfile.write(self.GARBAGE_PATTERN)
            outfile.seek(self.template_offset)
            outfile.write(self.byte_mods[self.mod_offset])

        self.mod_offset = (self.mod_offset + 1 ) % len(self.byte_mods)
        if self.mod_offset == 0:
            self.template_offset += 1

        return (t_cur, m_cur)

def main():
    p = Popen([DRMEMORY, FOOBAR], stdout=PIPE, stderr=STDOUT, bufsize=1, universal_newlines=True, close_fds=ON_POSIX)
    q = Queue()
    t = Thread(target=enqueue_output, args=(p.stdout, q))
    t.daemon = True # thread dies with the program
    t.start()
    
    sleep(25)
    if p.poll() != None:
        print('SOMETHING WENT WRONG!!')
        sys.exit(1)

    print('Opening logfile')
    log_outfile = open(LOG_OUTFILE, 'a')
    print('FPLInFILE()')
    fpl = FPLInFile(PL_FUZZ, PL_TEMPLATE)

    i = 0
    print('Clearing queue initially')
    while True:
        # read line without blocking
        try:  line = q.get_nowait() # or q.get(timeout=.1)
        except Empty:
            break
        else: # got line
            log_outfile.write(line)

    print('Waiting for start')
    while not pyautogui.locateOnScreen(MENU_FILE):
        sleep(1)
    print('Dry run')
    log_outfile.flush()
    log_outfile.write('FOOZZER: DRY RUN\n')
    log_outfile.flush()
    print('copying generic playlist')
    copyfile(PL_GENERIC, PL_FUZZ)
    print('loading playlist')
    load_pl(PL_FUZZ_NAME)
    sleep(30)
    print('checking for info window')
    close_info()
    sleep(5)
    print('closing playlist')
    del_pl(MENU_FUZZ_PL)

    print('MAINLOOP START')
    while os.path.isfile(RUNFILE):
        print('clearing queue')
        while True:
            try:  line = q.get_nowait()
            except Empty:
                break
            else:
                log_outfile.write(line)

        print('checking if Dr.Memory is still running')
        if p.poll() != None:
            print('RESTARTING Dr.Memory')
            t.join()
            p = Popen([DRMEMORY, FOOBAR], stdout=PIPE, stderr=STDOUT, bufsize=1, universal_newlines=True, close_fds=ON_POSIX)
            t = Thread(target=enqueue_output, args=(p.stdout, q))
            t.daemon = True
            t.start()

        print('fpl.next()')
        fpl_iteration = fpl.next()
        if fpl_iteration == (-1, -1):
            print('mutations exhausted; exitin')
            break
        print('Iteration: t_offset={} mod_offset={}\n'.format(fpl_iteration[0], fpl_iteration[1]))
        log_outfile.flush()
        log_outfile.write('FOOZZER: Iteration: t_offset={} mod_offset={}\n'.format(fpl_iteration[0], fpl_iteration[1]))
        log_outfile.flush()
        print('loading playlist')
        load_pl(PL_FUZZ_NAME)
        sleep(10)
        print('closing info window')
        close_info()
        sleep(3)
        print('closing playlist')
        del_pl(MENU_FUZZ_PL)

        i += 1

    print('MAINLOOP END')
    if p.poll() == None:
        print('terminating')
        p.terminate()
    sleep(2)
    print('joining')
    t.join()
    log_outfile.flush()
    log_outfile.write('FOOZZER: FINISHED')
    log_outfile.close()
    print('FINISHED')



if __name__ == '__main__':
    main()

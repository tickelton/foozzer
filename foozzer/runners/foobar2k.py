#!/usr/bin/env python3

import os
import argparse
import logging
import pyautogui
from time import sleep

RUNNER_NAME = 'foobar2k'
FOOBAR_EXE = 'foobar2000.exe'

# commands
CMD_STOP = '/stop'
CMD_LOAD_PL = '/command:"Load playlist..."'

# misc constants
GUI_CHECK_INTERVAL = 0.1 # time to wait in between checks for UI element
GUI_CHECK_TIMEOUT = 30 # max number of GUI_CHECK_INTERVAL iterations

log = logging.getLogger(__name__)

def get_module_info():
    return {RUNNER_NAME: ('foobar2000 playlist fuzzer', FB2KRunner)}

class FoozzerUIError(Exception):

    def __init__(self, message):
        self.message = message

class FB2KRunner():

    def _del_pl(self, btn_pl_img):
        btn_pl = self._gui_wait_for(btn_pl_img)
        btn_pl_center = pyautogui.center(btn_pl)
        pyautogui.click(button='right', x=btn_pl_center.x, y=btn_pl_center.y)
        del_pl = self._gui_wait_for(self._RM_PL)
        del_pl_center = pyautogui.center(del_pl)
        pyautogui.click(x=del_pl_center.x, y=del_pl_center.y)

    def _load_pl(self, pl_name):
        btn_file = self._gui_wait_for(self._MENU_FILE)
        btn_file_center = pyautogui.center(btn_file)
        pyautogui.click(x=btn_file_center.x, y=btn_file_center.y)
        btn_load = self._gui_wait_for(self._LOAD_PL)
        btn_load_center = pyautogui.center(btn_load)
        pyautogui.click(x=btn_load_center.x, y=btn_load_center.y)
        self._gui_wait_for(self._WINDOW_LOAD_PL)
        pyautogui.write(pl_name)
        pyautogui.press('enter')

    def _close_info(self):
        for i in range(3):
            win_info = pyautogui.locateOnScreen(self._TITLE_INFORMATION)
            if win_info:
                pyautogui.click(x=win_info.left+win_info.width-5, y=win_info.top+5)
                return

    def _reset_playlists(self):
        while pyautogui.locateOnScreen(self._MENU_FUZZ_PL):
            self._del_pl(self._MENU_FUZZ_PL)
            sleep(1)

    def _gui_wait_start(self):
        i = 0

        while not pyautogui.locateOnScreen(self._MENU_FILE) and not pyautogui.locateOnScreen(self._START_NORMALLY):
            if i > GUI_CHECK_TIMEOUT:
                raise FoozzerUIError('start failed')
            i += 1
            # initial start takes a while, so we just use triple the regular timeout
            sleep(GUI_CHECK_INTERVAL * 3)

        pos = pyautogui.locateOnScreen(self._START_NORMALLY)
        if pos:
            log.warning('ABNORMAL TERMINATION ! POTENTIAL BUG !!')
            pos_center = pyautogui.center(pos)
            pyautogui.click(x=pos_center.x, y=pos_center.y)
            self._gui_wait_for(self._MENU_FILE)

    def _gui_wait_for(self, element):
        i = 0

        while i < GUI_CHECK_TIMEOUT:
            pos = pyautogui.locateOnScreen(element)
            if pos:
                return pos
            i += 1
            sleep(GUI_CHECK_INTERVAL)

        raise FoozzerUIError('failed to locate {}'.format(element))

    def __init__(self, args):
        parser = argparse.ArgumentParser(prog=RUNNER_NAME)
        parser.add_argument(
            '-F',
            required=True,
            help='directory containing {}'.format(FOOBAR_EXE)
        )
        parser.add_argument(
            '-R',
            required=True,
            help='resource directory'
        )
        self._args = parser.parse_args(args)

        self._RM_PL = os.path.join(self._args.R, 'remove_playlist.png')
        self._START_NORMALLY = os.path.join(self._args.R, 'start_normally.png')
        self._TITLE_INFORMATION = os.path.join(self._args.R, 'information3.png')
        self._LOAD_PL = os.path.join(self._args.R, 'load_playlist.png')
        self._WINDOW_LOAD_PL = os.path.join(self._args.R, 'window_load_playlist.png')
        self._MENU_FILE = os.path.join(self._args.R, 'file.png')
        self._MENU_FUZZ_PL = os.path.join(self._args.R, 'fuzz_pl.png')

    def get_process_name(self):
        return FOOBAR_EXE

    def get_cmdline(self):
        return [os.path.join(self._args.F, FOOBAR_EXE)]

    def setup(self):
        log.info('Waiting for start')
        self._gui_wait_start()
        log.debug('Resetting playlists')
        self._reset_playlists()

    def run(self, input_file):
        try:
            log.debug('loading playlist')
            self._load_pl(input_file)
            log.debug('closing info window')
            self._close_info()
            log.debug('closing playlist')
            self._del_pl(self._MENU_FUZZ_PL)
        except FoozzerUIError as e:
            log.warning('Encountered UIError: {}'.format(e))
            return False

        return True

    def terminate(self):
        pass


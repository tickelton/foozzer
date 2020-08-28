#!/usr/bin/env python3
"""
A runner to fuzz the playlist loader of Foobar2000.

Usage: ... [-h] -F F -R R

Options:
    -h
    --help      show this help message and exit

    -F F        directory containing foobar2000.exe

    -R R        resource directory

"""

# Copyright (c) 2020 tick <tickelton@gmail.com>
# SPDX-License-Identifier:	ISC

import os
import argparse
import logging
from time import sleep

import pyautogui

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
    """Returns data used by main function to discover plugins."""

    return {RUNNER_NAME: ('foobar2000 playlist fuzzer', FB2KRunner)}

class FoozzerUIError(Exception):
    """Custom Exception to indicate unexpected GUI behavior."""

    def __init__(self, message):
        self.message = message
        super().__init__(message)


class FB2KRunner():
    """
    Provides methods to automate various GUI interactions with Foobar2000.

    In particular loading and removal of playlists and closing any
    error dialogues caused by malformed input due to fuzzing.
    """

    def _del_pl(self, btn_pl_img):
        """Deletes a single playlist by reference image."""

        btn_pl = self._gui_wait_for(btn_pl_img)
        btn_pl_center = pyautogui.center(btn_pl)
        pyautogui.click(button='right', x=btn_pl_center.x, y=btn_pl_center.y)
        del_pl = self._gui_wait_for(self._rm_pl)
        del_pl_center = pyautogui.center(del_pl)
        pyautogui.click(x=del_pl_center.x, y=del_pl_center.y)

    def _load_pl(self, pl_name):
        """Loads a playlist by name."""

        btn_file = self._gui_wait_for(self._menu_file)
        btn_file_center = pyautogui.center(btn_file)
        pyautogui.click(x=btn_file_center.x, y=btn_file_center.y)
        btn_load = self._gui_wait_for(self._load_pl_btn)
        btn_load_center = pyautogui.center(btn_load)
        pyautogui.click(x=btn_load_center.x, y=btn_load_center.y)
        self._gui_wait_for(self._window_load_pl)
        pyautogui.write(pl_name)
        pyautogui.press('enter')

    def _close_info(self):
        """Closes the information window caused by a malformed playlist."""

        for i in range(3):
            win_info = pyautogui.locateOnScreen(self._title_information)
            if win_info:
                pyautogui.click(x=win_info.left+win_info.width-5, y=win_info.top+5)
                return

    def _reset_playlists(self):
        """Closes all opened playlists."""

        while pyautogui.locateOnScreen(self._menu_fuzz_pl):
            self._del_pl(self._menu_fuzz_pl)
            sleep(1)

    def _gui_wait_start(self):
        """Wait until the 'File' button in the main menu is visible."""

        i = 0

        while (not pyautogui.locateOnScreen(self._menu_file) and
               not pyautogui.locateOnScreen(self._start_normally)):
            if i > GUI_CHECK_TIMEOUT:
                raise FoozzerUIError('start failed')
            i += 1
            # initial start takes a while, so we just use triple the regular timeout
            sleep(GUI_CHECK_INTERVAL * 3)

        pos = pyautogui.locateOnScreen(self._start_normally)
        if pos:
            log.warning('ABNORMAL TERMINATION ! POTENTIAL BUG !!')
            pos_center = pyautogui.center(pos)
            pyautogui.click(x=pos_center.x, y=pos_center.y)
            self._gui_wait_for(self._menu_file)

    @staticmethod
    def _gui_wait_for(element):
        """Waits until a given GUI element is visible."""

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

        self._rm_pl = os.path.join(self._args.R, 'remove_playlist.png')
        self._start_normally = os.path.join(self._args.R, 'start_normally.png')
        self._title_information = os.path.join(self._args.R, 'information3.png')
        self._load_pl_btn = os.path.join(self._args.R, 'load_playlist.png')
        self._window_load_pl = os.path.join(self._args.R, 'window_load_playlist.png')
        self._menu_file = os.path.join(self._args.R, 'file.png')
        self._menu_fuzz_pl = os.path.join(self._args.R, 'fuzz_pl.png')

    @staticmethod
    def get_process_name():
        """Returns the name of the process to be started."""

        return FOOBAR_EXE

    def get_cmdline(self):
        """Returns the command line arguments the target process is to be started with."""

        return [os.path.join(self._args.F, FOOBAR_EXE)]

    def setup(self):
        """Wait for GUI to be available and delete old playlists."""

        log.info('Waiting for start')
        self._gui_wait_start()
        log.debug('Resetting playlists')
        self._reset_playlists()

    def run(self, input_file):
        """
        Runs a single fuzzing iteration.

            * Loads a playlist.
            * Closes error messages, if any.
            * Deletes playlist.
            * Raises exception on unexpected GUI behaviour.
        """

        try:
            log.debug('loading playlist')
            self._load_pl(input_file)
            log.debug('closing info window')
            self._close_info()
            log.debug('closing playlist')
            self._del_pl(self._menu_fuzz_pl)
        except FoozzerUIError as e:
            log.warning('Encountered UIError: %s', e)
            return False

        return True

    def terminate(self):
        """
        Terminates auxiliary processes.

        Currently unused.
        """
        return

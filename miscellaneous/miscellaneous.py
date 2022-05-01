"""
    This file is part of Taskbar Notifier.

    Copyright (C) 2018-2022 Ralf Dauberschmidt <ralf@dauberschmidt.de>

    Taskbar Notifier is free software; you can redistribute it and/or modify it under the terms of the GNU General
    Public License as published by the Free Software Foundation; either version 3 of the License, or (at your option)
    any later version.

    Taskbar Notifier is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
    implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
    details.

    You should have received a copy of the GNU General Public License along with Taskbar Notifier. If not, see
    <http://www.gnu.org/licenses/>.
"""

import ctypes
import logging
import os
import sys

from typing import List

# Define the logger
LOG = logging.getLogger(os.path.basename(__file__).split('.')[0])


def get_active_applications(excluded_titles: List[str]) -> List[str]:
    """
    Get a list of active applications on the taskbar.
    :param excluded_titles: List of titles to exclude.
    :return: List of active applications on the taskbar.
    """
    enum_windows = ctypes.windll.user32.EnumWindows
    enum_windows_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))

    active_applications = []

    def process_window_handle(hwnd, _) -> bool:
        """
        Callback function for EnumWindows.
        :param hwnd: Handle to a top-level window.
        :param _: Application defined value, unused.
        :return: True to continue enumeration, false otherwise.
        """
        get_window_text = ctypes.windll.user32.GetWindowTextW
        get_window_text_length = ctypes.windll.user32.GetWindowTextLengthW
        is_window_visible = ctypes.windll.user32.IsWindowVisible

        if is_window_visible(hwnd):
            length = get_window_text_length(hwnd)
            buffer = ctypes.create_unicode_buffer(length + 1)
            get_window_text(hwnd, buffer, length + 1)
            if buffer.value and buffer.value not in ["MainWindow", "Program Manager"] + excluded_titles:
                active_applications.append(buffer.value)

        return True

    enum_windows(enum_windows_proc(process_window_handle), 0)

    return active_applications


if __name__ == "__main__":
    LOG.critical("This module is not supposed to be executed.")
    sys.exit(1)

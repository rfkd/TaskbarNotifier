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

import logging
import os
import sys

from PyQt5.QtWidgets import QApplication

from gui.main_window import MainWindow

# pylint: disable=unused-import
from resources import resources

# Define the logger
LOG = logging.getLogger(os.path.basename(__file__).split('.')[0])

if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s [%(levelname)s] <%(name)s> %(message)s", level=logging.INFO)
    LOG.info("Taskbar Notifier starting.")

    application = QApplication(sys.argv)
    application.setQuitOnLastWindowClosed(False)
    main_window = MainWindow()
    exit_code = application.exec_()

    main_window.tray_icon.setVisible(False)
    LOG.info("Taskbar Notifier terminating with exit code %d.", exit_code)
    sys.exit(exit_code)

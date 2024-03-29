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

import os
import zipfile

import PyInstaller.__main__

from miscellaneous.version import GIT_SHORT_HASH, VERSION

# Name of the application
APPLICATION_NAME = "TaskbarNotifier"

# File name of the application
APPLICATION_FILE = "taskbar_notifier.py"

# Location of the application icon
APPLICATION_ICON = os.path.join("resources", "Yellow.ico")

if __name__ == "__main__":
    # Write version and hash to file
    with open(f"{APPLICATION_NAME}.ver", "w", encoding="utf-8") as file:
        file.writelines(f"{VERSION}\n")
        file.writelines(f"{GIT_SHORT_HASH}\n")

    # Create executable
    PyInstaller.__main__.run([
        "--clean",
        "--noconfirm",
        "--windowed",
        f"--add-data={APPLICATION_NAME}.ver;data",
        f"--icon={APPLICATION_ICON}",
        f"--name={APPLICATION_NAME}",
        f"{APPLICATION_FILE}"
    ])

    # Create distribution archive
    os.chdir("dist")
    with zipfile.ZipFile(f"{APPLICATION_NAME}-{VERSION}-g{GIT_SHORT_HASH}.zip", "w") as archive:
        for root, dirs, files in os.walk(APPLICATION_NAME):
            for file in files:
                archive.write(os.path.join(root, file))
    os.chdir("..")

    # Remove version file
    try:
        os.remove(f"{APPLICATION_NAME}.ver")
    except FileNotFoundError:
        pass

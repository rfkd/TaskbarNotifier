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

# Define the logger
LOG = logging.getLogger(os.path.basename(__file__).split('.')[0])

# Default version string
VERSION = "unknown"

# Default short Git hash
GIT_SHORT_HASH = ""


def load_from_file():
    """
    Try to load the version and Git hash from the 'TaskbarNotifier.ver' file and write them to the global variables.
    Leave the global variables untouched if the file cannot be found.
    :return: Tuple consisting of
    """
    global VERSION
    global GIT_SHORT_HASH

    versionfile_name = "TaskbarNotifier.ver"
    versionfile_search_paths = [".", "data"]

    for path in versionfile_search_paths:
        versionfile = os.path.join(path, versionfile_name)
        if os.path.isfile(versionfile):
            with open(versionfile, "r") as file:
                VERSION = file.readline().rstrip()
                GIT_SHORT_HASH = file.readline().rstrip()
            break


# Check if a Git client is available
try:
    import git

    # Check if the application is called from a Git repository
    try:
        # Get version and Git hash from the repository
        repo = git.Repo()
        VERSION = next((str(tag) for tag in repo.tags if tag.commit == repo.head.commit), "0.0.0")
        GIT_SHORT_HASH = repo.git.rev_parse(repo.head.object.hexsha, short=4)
        if repo.is_dirty():
            GIT_SHORT_HASH += " (dirty)"
    except git.InvalidGitRepositoryError:
        LOG.warning("Application is not started within a Git repository, loading version from file.")
        load_from_file()
except ImportError:
    LOG.warning("Git module cannot be imported, loading version from file.")
    load_from_file()

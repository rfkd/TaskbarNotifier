"""
This file is part of Taskbar Notifier.

Copyright (C) 2018 Ralf Dauberschmidt <ralf@dauberschmidt.de>

Taskbar Notifier is free software; you can redistribute it and/or modify it under the terms of the GNU General Public
License as published by the Free Software Foundation; either version 3 of the License, or (at your option) any later
version.

Taskbar Notifier is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Taskbar Notifier. If not, see
<http://www.gnu.org/licenses/>.
"""

import git
import os

# Default version string
VERSION = "0.0.0"

# Default short Git hash
GIT_SHORT_HASH = ""

# Update version and hash from repository or file if possible
try:
	# Get information from repository
	repo = git.Repo()
	VERSION = next((str(tag) for tag in repo.tags if tag.commit == repo.head.commit), "0.0.0")
	GIT_SHORT_HASH = repo.git.rev_parse(repo.head.object.hexsha, short=4)
	if repo.is_dirty():
		GIT_SHORT_HASH += " (dirty)"
except git.exc.InvalidGitRepositoryError:
	# Load version information from file if available
	__version_locations = [".", "data"]
	for location in __version_locations:
		if os.path.isfile(os.path.join(location, "TaskbarNotifier.ver")):
			__version_file = os.path.join(location, "TaskbarNotifier.ver")
			break
	if __version_file:
		with open(__version_file, "r") as file:
			VERSION = file.readline().rstrip()
			GIT_SHORT_HASH = file.readline().rstrip()

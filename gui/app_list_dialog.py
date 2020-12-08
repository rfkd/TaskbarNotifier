"""
    This file is part of Taskbar Notifier.

    Copyright (C) 2018-2020 Ralf Dauberschmidt <ralf@dauberschmidt.de>

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

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QWidget, QDialog, QListWidget, QHBoxLayout, QVBoxLayout, QPushButton, QAbstractItemView,
                             QListWidgetItem, QGroupBox)

from miscellaneous.miscellaneous import get_active_applications

# Define the logger
LOG = logging.getLogger(os.path.basename(__file__).split('.')[0])


class AppListDialog(QDialog):
    """
    Window listing all open applications on the taskbar.
    """
    # Dialog window title
    WINDOW_TITLE = "List of open applications"

    def __init__(self, parent: QWidget) -> None:
        """
        Class constructor.
        :param parent: MainWindow self.
        """
        self.parent = parent

        # Call parent constructor
        super().__init__()

        # Build the user interface
        self.__build_user_interface()

    def __build_user_interface(self) -> None:
        """
        Build the user interface.
        """
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setWindowIcon(QIcon(":/Yellow.png"))
        self.setMinimumSize(600, 250)
        self.resize(600, 250)

        self.list_widget = QListWidget()
        self.__populate_list()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_widget.selectionModel().selectionChanged.connect(self.__on_list_widget_selection_changed)
        self.list_widget.doubleClicked.connect(self.__on_list_widget_double_clicked)

        self.add_button = QPushButton("Add selected")
        self.add_button.setToolTip("Add selected entries")
        self.add_button.clicked.connect(self.__on_add_button_clicked)
        self.add_button.setDisabled(True)

        refresh_button = QPushButton("Refresh list")
        refresh_button.setToolTip("Refresh the list of open applications")
        refresh_button.clicked.connect(self.__on_refresh_button_clicked)

        vbox = QVBoxLayout()
        vbox.addWidget(self.list_widget)

        hbox = QHBoxLayout()
        hbox.addWidget(self.add_button)
        hbox.addWidget(refresh_button)
        hbox.addStretch(1)
        vbox.addLayout(hbox)

        group_box = QGroupBox()
        group_box.setTitle("Open applications")
        group_box.setLayout(vbox)

        layout = QHBoxLayout()
        layout.addWidget(group_box)

        self.setLayout(layout)

    def __populate_list(self) -> None:
        """
        Populate the list widget with the active applications on the taskbar.
        """
        for app in get_active_applications([self.WINDOW_TITLE, self.parent.WINDOW_TITLE]):
            self.list_widget.addItem(app)

    def __add_selected_items_to_parent_list(self) -> None:
        """
        Add all selected items to the parent list widget.
        """
        main_items = []
        for i in range(self.parent.list_widget.count()):
            main_items.append(self.parent.list_widget.item(i).text())

        for item in self.list_widget.selectedItems():
            if item.text() not in main_items:
                editable_item = QListWidgetItem(item)
                editable_item.setFlags(item.flags() | Qt.ItemIsEditable)
                self.parent.list_widget.addItem(editable_item)

    def __on_list_widget_selection_changed(self) -> None:
        """
        Selection changed event handler for the list widget.
        """
        self.add_button.setDisabled(len(self.list_widget.selectedIndexes()) == 0)

    def __on_list_widget_double_clicked(self) -> None:
        """
        Double clicked event handler for the list widget.
        """
        self.__add_selected_items_to_parent_list()
        self.close()

    def __on_add_button_clicked(self) -> None:
        """
        Clicked event handler for the add button.
        """
        self.__add_selected_items_to_parent_list()
        self.close()

    def __on_refresh_button_clicked(self) -> None:
        """
        Clicked event handler for the refresh button.
        """
        self.list_widget.clear()
        self.__populate_list()

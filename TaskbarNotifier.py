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

import ctypes
import sys

from typing import List

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QFont, QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QListWidget, QHBoxLayout, QVBoxLayout, QPushButton, \
    QAbstractItemView, QSystemTrayIcon, QAction, QStyle, QMenu, QListWidgetItem, QGroupBox, QLineEdit, QShortcut, \
    QCheckBox, QLabel, QSpinBox, qApp

from resources import Resources


def get_active_applications() -> List[str]:
    """
    Get a list of active applications on the taskbar.
    :return: List of active applications on the taskbar.
    """

    # noinspection PyPep8Naming
    EnumWindows = ctypes.windll.user32.EnumWindows
    # noinspection PyPep8Naming
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))

    active_applications = []

    def process_window_handle(hwnd, _) -> bool:
        """
        Callback function for EnumWindows.
        :param hwnd: Handle to a top-level window.
        :param _: Application defined value, unused.
        :return: True to continue enumeration, false otherwise.
        """

        # noinspection PyPep8Naming
        GetWindowText = ctypes.windll.user32.GetWindowTextW
        # noinspection PyPep8Naming
        GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
        # noinspection PyPep8Naming
        IsWindowVisible = ctypes.windll.user32.IsWindowVisible

        if IsWindowVisible(hwnd):
            length = GetWindowTextLength(hwnd)
            buffer = ctypes.create_unicode_buffer(length + 1)
            GetWindowText(hwnd, buffer, length + 1)
            if buffer.value and buffer.value not in ["MainWindow", "Taskbar Notifier", "Program Manager"]:
                active_applications.append(buffer.value)

        return True

    EnumWindows(EnumWindowsProc(process_window_handle), 0)

    return active_applications


# noinspection PyArgumentList,PyUnresolvedReferences
class AppListDialog(QDialog):
    """
    Window listing all open applications on the taskbar.
    """

    def __init__(self, parent: QWidget) -> None:
        """
        Class constructor.
        :param parent: MainWindow self.
        """

        self.parent = parent

        # Call parent constructor
        # noinspection PyArgumentList
        super().__init__()

        # Build the user interface
        self.__build_user_interface()

    def __build_user_interface(self) -> None:
        """
        Build the user interface.
        """

        self.setWindowTitle("Taskbar Notifier")
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

        for app in get_active_applications():
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


# noinspection PyArgumentList,PyUnresolvedReferences
class MainWindow(QWidget):
    """
    Main application window class.
    """

    # File in which the list data is stored persistently
    DATA_FILE_NAME = "TaskbarNotifier.dat"

    # Data file version
    DATA_FILE_VERSION = 1

    # Timer interval used for taskbar polling (unit: milliseconds)
    TIMER_INVTERVAL_POLLING_MS = 500

    # Minimum timer interval for toast notifications (unit: seconds)
    TIMER_INTERVAL_TOAST_MIN_S = 6

    # Maximum timer interval for toast notifications (unit: seconds)
    TIMER_INTERVAL_TOAST_MAX_S = 3600

    # Default timer interval for toast notifications (unit: seconds)
    TIMER_INTERVAL_TOAST_DEFAULT_S = 10

    # Active applications currently listed on a toast notification
    applications_on_toast = []

    def __init__(self) -> None:
        """
        Class constructor.
        """

        # Call parent constructor
        super().__init__()

        # Build the user interface
        self.__build_user_interface()
        self.__setup_tray_icon()

        # Setup the timers
        self.timer_toast = QTimer(self)
        self.timer_toast.setSingleShot(True)
        self.timer_polling = QTimer(self)
        self.timer_polling.timeout.connect(self.__on_timer_polling_expired)
        self.timer_polling.start(self.TIMER_INVTERVAL_POLLING_MS)

    def __build_user_interface(self) -> None:
        """
        Build the user interface.
        """

        self.setWindowTitle("Taskbar Notifier")
        self.setWindowIcon(QIcon(":/Yellow.png"))
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(700, 300)
        self.resize(700, 300)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_widget.selectionModel().selectionChanged.connect(self.__on_list_widget_selection_changed)
        self.list_widget.setToolTip("Double click to edit")

        shortcut = QShortcut(Qt.Key_Delete, self.list_widget)
        shortcut.activated.connect(self.__on_delete_button_clicked)

        self.add_edit = QLineEdit()
        self.add_edit.textChanged.connect(self.__on_add_edit_text_changed)
        self.add_edit.returnPressed.connect(self.__on_add_button_clicked)

        self.add_button = QPushButton("Add")
        self.add_button.setDisabled(True)
        self.add_button.setToolTip("Add the entry from the left edit field")
        self.add_button.clicked.connect(self.__on_add_button_clicked)

        list_button = QPushButton("List open apps")
        list_button.setMinimumWidth(100)
        list_button.setToolTip("List currently open applications")
        list_button.clicked.connect(self.__on_list_button_clicked)

        self.delete_button = QPushButton("Delete selected")
        self.delete_button.setMinimumWidth(100)
        self.delete_button.setDisabled(True)
        self.delete_button.setToolTip("Delete selected entries")
        self.delete_button.clicked.connect(self.__on_delete_button_clicked)

        self.repeat_check_box = QCheckBox("Repeat active notifications every")
        self.repeat_check_box.stateChanged.connect(self.__on_repeat_check_box_state_changed)

        self.repeat_spin = QSpinBox()
        self.repeat_spin.setMaximumWidth(65)
        self.repeat_spin.setAlignment(Qt.AlignHCenter)
        self.repeat_spin.setDisabled(True)
        self.repeat_spin.setMinimum(self.TIMER_INTERVAL_TOAST_MIN_S)
        self.repeat_spin.setMaximum(self.TIMER_INTERVAL_TOAST_MAX_S)
        self.repeat_spin.setValue(self.TIMER_INTERVAL_TOAST_DEFAULT_S)
        self.repeat_spin.setToolTip(f"Value in seconds between {self.TIMER_INTERVAL_TOAST_MIN_S} "
                                    f"and {self.TIMER_INTERVAL_TOAST_MAX_S}")

        repeat_label = QLabel("seconds")

        self.__deserialize_data()

        vbox_list = QVBoxLayout()

        hbox_add = QHBoxLayout()
        hbox_add.addWidget(self.add_edit)
        hbox_add.addWidget(self.add_button)
        vbox_list.addLayout(hbox_add)

        vbox_list.addWidget(self.list_widget)

        hbox_buttons = QHBoxLayout()
        hbox_buttons.addWidget(self.delete_button)
        hbox_buttons.addWidget(list_button)
        hbox_buttons.addStretch(1)
        vbox_list.addLayout(hbox_buttons)

        group_watch_expressions = QGroupBox()
        group_watch_expressions.setTitle("Watch expressions")
        group_watch_expressions.setLayout(vbox_list)

        vbox_settings = QVBoxLayout()
        hbox_repeat = QHBoxLayout()
        hbox_repeat.addWidget(self.repeat_check_box)
        hbox_repeat.addWidget(self.repeat_spin)
        hbox_repeat.addWidget(repeat_label)
        hbox_repeat.addStretch(1)
        vbox_settings.addLayout(hbox_repeat)

        group_settings = QGroupBox()
        group_settings.setTitle("Settings")
        group_settings.setLayout(vbox_settings)

        layout = QVBoxLayout()
        layout.addWidget(group_watch_expressions)
        layout.addWidget(group_settings)

        self.setLayout(layout)

    def __setup_tray_icon(self) -> None:
        """
        Setup the tray icon.
        """

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(":/Grey.png"))
        self.tray_icon.activated.connect(self.__on_tray_icon_activated)
        tray_menu = QMenu()

        show_action_font = QFont()
        show_action_font.setBold(True)

        show_action = QAction("Show", self)
        show_action.setFont(show_action_font)
        show_action.setIcon(self.style().standardIcon(QStyle.SP_TitleBarNormalButton))
        show_action.triggered.connect(self.__on_show)
        tray_menu.addAction(show_action)

        quit_action = QAction("Exit", self)
        quit_action.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
        quit_action.triggered.connect(self.__on_exit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def __on_tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self.__on_show()

    def __serialize_data(self) -> None:
        """
        Serialize the list entries to the data file.
        """

        with open(self.DATA_FILE_NAME, "w") as file:
            file.writelines(str(self.DATA_FILE_VERSION) + "\n")
            file.writelines(f"1 {self.repeat_spin.value()}\n" if self.repeat_check_box.checkState() == Qt.Checked
                            else f"0 {self.repeat_spin.value()}\n")
            file.writelines(map(lambda x: x + "\n", [str(self.list_widget.item(i).text())
                                                     for i in range(self.list_widget.count())]))

    def __deserialize_data(self) -> None:
        """
        Deserialize the list entries from tbe data file.
        """

        try:
            with open(self.DATA_FILE_NAME, "r") as file:
                version = file.readline()
                if int(version) != self.DATA_FILE_VERSION:
                    return

                repeat, repeat_value = file.readline().split(" ", 1)
                self.repeat_check_box.setCheckState(Qt.Checked if int(repeat) > 0 else Qt.Unchecked)
                self.repeat_spin.setValue(int(repeat_value))

                for line in file:
                    item = QListWidgetItem(line.rstrip())
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    self.list_widget.addItem(item)
        except FileNotFoundError:
            pass

    def __on_timer_polling_expired(self) -> None:
        """
        Timer expired event handler.
        """

        if len(self.list_widget) == 0:
            return

        # Check whether a listed application is active
        applications_to_be_toasted = []
        active_applications = get_active_applications()
        for expression in [str(self.list_widget.item(i).text()) for i in range(self.list_widget.count())]:
            for app in active_applications:
                if expression in app:
                    applications_to_be_toasted.append(app)

        # Create a toast notification for active applications
        if len(applications_to_be_toasted):
            repeat_toast = self.repeat_check_box.checkState() == Qt.Checked

            if (repeat_toast and not self.timer_toast.isActive()) \
                    or applications_to_be_toasted != self.applications_on_toast:
                self.tray_icon.showMessage("Taskbar Notifier", "\n".join(applications_to_be_toasted),
                                           QIcon(":/Yellow.png"))
                if repeat_toast:
                    self.timer_toast.start(self.repeat_spin.value() * 1000)

        # Change the tray icon depending on the notification state
        if len(self.applications_on_toast) > 0 and len(applications_to_be_toasted) == 0:
            self.tray_icon.setIcon(QIcon(":/Grey.png"))
        elif len(self.applications_on_toast) == 0 and len(applications_to_be_toasted) > 0:
            self.tray_icon.setIcon(QIcon(":/Yellow.png"))

        self.applications_on_toast = applications_to_be_toasted

    def __on_list_widget_selection_changed(self) -> None:
        """
        Selection changed event handler for the list widget.
        """

        self.delete_button.setDisabled(len(self.list_widget.selectedIndexes()) == 0)

    def __on_add_edit_text_changed(self, text: str) -> None:
        """
        Text changed event handler for the add edit field.
        :param text: Edit field text.
        """

        self.add_button.setDisabled(len(text) == 0)

    def __on_add_button_clicked(self) -> None:
        """
        Clicked event handler for the add button.
        """

        if len(self.add_edit.text()):
            item = QListWidgetItem(self.add_edit.text())
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.list_widget.addItem(item)
            self.add_edit.clear()

    def __on_list_button_clicked(self) -> None:
        """
        Clicked event handler for the list button.
        """

        AppListDialog(self).exec_()

    def __on_delete_button_clicked(self) -> None:
        """
        Clicked event handler for the delete button.
        """

        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))

    def __on_repeat_check_box_state_changed(self, state: Qt.CheckState) -> None:
        """
        Check state event handler for the repeat notifications check box.
        :param state: Check box state.
        """

        self.repeat_spin.setEnabled(state == Qt.Checked)

    def __on_show(self) -> None:
        """
        Event handler for the tray show action.
        """

        self.timer_polling.stop()
        self.show()
        self.activateWindow()

    def __on_exit(self) -> None:
        """
        Event handler for the tray exit action.
        """

        self.__serialize_data()
        qApp.quit()

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        On close event handler.
        :param event: Close event.
        """

        # Prevent that the app closes upon closing the main window
        event.ignore()

        self.__serialize_data()
        self.hide()
        self.timer_polling.start(self.TIMER_INVTERVAL_POLLING_MS)


if __name__ == "__main__":
    application = QApplication(sys.argv)
    main_window = MainWindow()
    exit_code = application.exec_()

    main_window.tray_icon.setVisible(False)
    sys.exit(exit_code)

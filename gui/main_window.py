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
import winreg

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (QAbstractItemView, QAction, QCheckBox, QComboBox, QDialog, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem, QMenu, QMessageBox, QPushButton, QShortcut,
                             QSpinBox, QStyle, QSystemTrayIcon, QVBoxLayout, QWidget, qApp)

from gui.app_list_dialog import AppListDialog
from miscellaneous.flash_screen import FlashScreen
from miscellaneous.miscellaneous import get_active_applications
from miscellaneous.notification import Notification
from miscellaneous.version import GIT_SHORT_HASH, VERSION

# Define the logger
LOG = logging.getLogger(os.path.basename(__file__).split('.')[0])


class MainWindow(QWidget):
    """
    Main application window class.
    """
    # Full version string
    FULL_VERSION = f"{VERSION}-g{GIT_SHORT_HASH}" if GIT_SHORT_HASH else VERSION

    # Dialog window title
    WINDOW_TITLE = f"Taskbar Notifier {FULL_VERSION}"

    # File in which the application data is stored persistently
    DATA_FILE_NAME = "TaskbarNotifier.dat"

    # Data file version
    DATA_FILE_VERSION = 2

    # Registry key for the auto-start entry
    AUTOSTART_REGISTRY_KEY = "TaskbarNotifier"

    # Duration until a notification will expire (unit: seconds)
    NOTIFICATION_DURATION_S = 5

    # Timer interval used for taskbar polling (unit: milliseconds)
    TIMER_INVTERVAL_POLLING_MS = 500

    # Minimum timer interval for notifications (unit: seconds)
    TIMER_INTERVAL_NOTIFICATION_MIN_S = NOTIFICATION_DURATION_S + 2

    # Maximum timer interval for notifications (unit: seconds)
    TIMER_INTERVAL_NOTIFICATION_MAX_S = 3600

    # Default timer interval for notifications (unit: seconds)
    TIMER_INTERVAL_NOTIFICATION_DEFAULT_S = 30

    # Active applications currently listed on a notification
    applications_on_notification = []

    def __init__(self) -> None:
        """
        Class constructor.
        """
        super().__init__()

        self.__applications_on_notification = []
        self.__flash_screen = None
        self.__notification = None

        # Build the user interface
        self.__build_user_interface()
        self.__setup_tray_icon()

        # Set up the timers
        self.__timer_repeat_notification = QTimer(self)
        self.__timer_repeat_notification.setSingleShot(True)
        self.__timer_polling = QTimer(self)
        self.__timer_polling.timeout.connect(self.__on_timer_polling_expired)
        self.__timer_polling.start(self.TIMER_INVTERVAL_POLLING_MS)

    # pylint: disable=too-many-locals, too-many-statements
    def __build_user_interface(self) -> None:
        """
        Build the user interface.
        """
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setWindowIcon(QIcon(":/Yellow.png"))
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(700, 300)
        self.resize(700, 300)

        self.__list_widget = QListWidget()
        self.__list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.__list_widget.selectionModel().selectionChanged.connect(self.__on_list_widget_selection_changed)
        self.__list_widget.setToolTip("Double click to edit")

        shortcut = QShortcut(Qt.Key_Delete, self.__list_widget)
        shortcut.activated.connect(self.__on_delete_button_clicked)

        self.__add_edit = QLineEdit()
        self.__add_edit.textChanged.connect(self.__on_add_edit_text_changed)
        self.__add_edit.returnPressed.connect(self.__on_add_button_clicked)

        self.__add_button = QPushButton("Add")
        self.__add_button.setDisabled(True)
        self.__add_button.setToolTip("Add the entry from the left edit field")
        self.__add_button.clicked.connect(self.__on_add_button_clicked)

        list_button = QPushButton("List open apps")
        list_button.setMinimumWidth(100)
        list_button.setToolTip("List currently open applications")
        list_button.clicked.connect(self.__on_list_button_clicked)

        self.__delete_button = QPushButton("Delete selected")
        self.__delete_button.setMinimumWidth(100)
        self.__delete_button.setDisabled(True)
        self.__delete_button.setToolTip("Delete selected entries")
        self.__delete_button.clicked.connect(self.__on_delete_button_clicked)

        self.__autostart_check_box = QCheckBox("Automatically start after login")
        self.__autostart_check_box.stateChanged.connect(self.__on_autostart_check_box_state_changed)
        self.__set_autostart_check_box()
        if sys.executable.endswith("python.exe"):
            self.__autostart_check_box.setDisabled(True)
            self.__autostart_check_box.setToolTip("Taskbar Notifier needs to be compiled as a binary to use this "
                                                "feature.")

        self.__flash_screen_check_box = QCheckBox("Flash screen on notifications")

        self.__repeat_check_box = QCheckBox("Repeat active notifications every")
        self.__repeat_check_box.stateChanged.connect(self.__on_repeat_check_box_state_changed)
        self.__repeat_spin = QSpinBox()
        self.__repeat_spin.setMaximumWidth(65)
        self.__repeat_spin.setAlignment(Qt.AlignHCenter)
        self.__repeat_spin.setDisabled(True)
        self.__repeat_spin.setMinimum(self.TIMER_INTERVAL_NOTIFICATION_MIN_S)
        self.__repeat_spin.setMaximum(self.TIMER_INTERVAL_NOTIFICATION_MAX_S)
        self.__repeat_spin.setValue(self.TIMER_INTERVAL_NOTIFICATION_DEFAULT_S)
        self.__repeat_spin.setToolTip(f"Value in seconds between {self.TIMER_INTERVAL_NOTIFICATION_MIN_S} "
                                    f"and {self.TIMER_INTERVAL_NOTIFICATION_MAX_S}")
        repeat_label = QLabel("seconds")

        notification_location_label = QLabel("Location of notifications: ")
        self.__notification_location = QComboBox()
        self.__notification_location.addItem("Bottom left", Notification.Location.BOTTOM_LEFT)
        self.__notification_location.addItem("Bottom right", Notification.Location.BOTTOM_RIGHT)
        self.__notification_location.addItem("Top left", Notification.Location.TOP_LEFT)
        self.__notification_location.addItem("Top right", Notification.Location.TOP_RIGHT)
        self.__notification_location.setCurrentIndex(1)

        self.__deserialize_data()

        vbox_list = QVBoxLayout()

        hbox_add = QHBoxLayout()
        hbox_add.addWidget(self.__add_edit)
        hbox_add.addWidget(self.__add_button)
        vbox_list.addLayout(hbox_add)

        vbox_list.addWidget(self.__list_widget)

        hbox_buttons = QHBoxLayout()
        hbox_buttons.addWidget(self.__delete_button)
        hbox_buttons.addWidget(list_button)
        hbox_buttons.addStretch(1)
        vbox_list.addLayout(hbox_buttons)

        group_watch_expressions = QGroupBox()
        group_watch_expressions.setTitle("Watch expressions")
        group_watch_expressions.setLayout(vbox_list)

        vbox_settings = QVBoxLayout()

        hbox_autostart = QHBoxLayout()
        hbox_autostart.addWidget(self.__autostart_check_box)
        hbox_autostart.addStretch(1)
        vbox_settings.addLayout(hbox_autostart)

        hbox_flash_screen = QHBoxLayout()
        hbox_flash_screen.addWidget(self.__flash_screen_check_box)
        hbox_flash_screen.addStretch(1)
        vbox_settings.addLayout(hbox_flash_screen)

        hbox_repeat = QHBoxLayout()
        hbox_repeat.addWidget(self.__repeat_check_box)
        hbox_repeat.addWidget(self.__repeat_spin)
        hbox_repeat.addWidget(repeat_label)
        hbox_repeat.addStretch(1)
        vbox_settings.addLayout(hbox_repeat)

        hbox_notification_location = QHBoxLayout()
        hbox_notification_location.addWidget(notification_location_label)
        hbox_notification_location.addWidget(self.__notification_location)
        hbox_notification_location.addStretch(1)
        vbox_settings.addLayout(hbox_notification_location)

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
        self.__tray_icon = QSystemTrayIcon(self)
        self.__tray_icon.setIcon(QIcon(":/Grey.png"))
        self.__tray_icon.activated.connect(self.__on_tray_icon_activated)
        tray_menu = QMenu()

        show_action_font = QFont()
        show_action_font.setBold(True)

        show_action = QAction("Show", self)
        show_action.setFont(show_action_font)
        show_action.setIcon(self.style().standardIcon(QStyle.SP_ArrowUp))
        show_action.triggered.connect(self.__on_show)
        tray_menu.addAction(show_action)

        self.__tray_enable_disable_action = QAction("Disable", self)
        self.__tray_enable_disable_action.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.__tray_enable_disable_action.triggered.connect(self.__on_enable_disable)
        tray_menu.addAction(self.__tray_enable_disable_action)

        about_action = QAction("About", self)
        about_action.setIcon(self.style().standardIcon(QStyle.SP_FileDialogInfoView))
        about_action.triggered.connect(self.__on_about)
        tray_menu.addAction(about_action)

        quit_action = QAction("Exit", self)
        quit_action.setIcon(self.style().standardIcon(QStyle.SP_BrowserStop))
        quit_action.triggered.connect(self.__on_exit)
        tray_menu.addAction(quit_action)

        self.__tray_icon.setContextMenu(tray_menu)
        self.__tray_icon.show()

    def __on_tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """
        Tray icon activated event handler.
        :param reason: Reason for activation.
        """
        if reason == QSystemTrayIcon.DoubleClick:
            self.__on_show()
            LOG.info("Main window shown.")

    def __serialize_data(self) -> None:
        """
        Serialize the list entries to the data file.
        """
        with open(self.DATA_FILE_NAME, mode="w", encoding="utf-8") as file:
            file.writelines(str(self.DATA_FILE_VERSION) + "\n")
            file.writelines("1\n" if self.__flash_screen_check_box.checkState() == Qt.Checked else "0\n")
            file.writelines(f"1 {self.__repeat_spin.value()}\n" if self.__repeat_check_box.checkState() == Qt.Checked
                            else f"0 {self.__repeat_spin.value()}\n")
            file.writelines(f"{self.__notification_location.currentIndex()}\n")
            file.writelines(map(lambda x: x + "\n", [str(self.__list_widget.item(i).text())
                                                     for i in range(self.__list_widget.count())]))

    def __deserialize_data(self) -> None:
        """
        Deserialize the list entries from tbe data file.
        """
        try:
            with open(self.DATA_FILE_NAME, mode="r", encoding="utf-8") as file:
                data_file_version = file.readline()
                if int(data_file_version) != self.DATA_FILE_VERSION:
                    return

                flash_screen = file.readline()
                self.__flash_screen_check_box.setCheckState(Qt.Checked if int(flash_screen) > 0 else Qt.Unchecked)

                repeat, repeat_value = file.readline().split(" ", 1)
                self.__repeat_check_box.setCheckState(Qt.Checked if int(repeat) > 0 else Qt.Unchecked)
                self.__repeat_spin.setValue(int(repeat_value))

                notification_location_index = file.readline()
                self.__notification_location.setCurrentIndex(int(notification_location_index))

                for line in file:
                    item = QListWidgetItem(line.rstrip())
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    self.__list_widget.addItem(item)
        except FileNotFoundError:
            pass

    def __on_timer_polling_expired(self) -> None:
        """
        Polling timer expired event handler.
        """
        if len(self.__list_widget) == 0:
            return

        # Check whether a listed application is active
        applications_to_be_notified = []
        active_applications = get_active_applications([self.WINDOW_TITLE])
        for expression in [str(self.__list_widget.item(i).text()) for i in range(self.__list_widget.count())]:
            for app in active_applications:
                if expression in app:
                    applications_to_be_notified.append(app)

        # Create a notification for active applications
        if applications_to_be_notified:
            repeat_notification = self.__repeat_check_box.checkState() == Qt.Checked

            if (repeat_notification and not self.__timer_repeat_notification.isActive()) \
                    or applications_to_be_notified != self.__applications_on_notification:
                if self.__flash_screen_check_box.checkState() == Qt.Checked:
                    if self.__flash_screen:
                        self.__flash_screen.stop()
                        self.__flash_screen.deleteLater()
                    LOG.info("Flashing the screen.")
                    self.__flash_screen = FlashScreen()

                if self.__notification:
                    self.__notification.stop()
                    self.__notification.deleteLater()
                LOG.info("Showing notification for: %s", ", ".join(applications_to_be_notified))
                self.__notification = Notification("Taskbar Notifier", "\n".join(applications_to_be_notified),
                                                   self.NOTIFICATION_DURATION_S,
                                                   self.__notification_location.currentData())

                if repeat_notification:
                    self.__timer_repeat_notification.start(self.__repeat_spin.value() * 1000)

        # Change the tray icon depending on the notification state
        if len(self.__applications_on_notification) > 0 and len(applications_to_be_notified) == 0:
            self.__tray_icon.setIcon(QIcon(":/Grey.png"))
        elif len(self.__applications_on_notification) == 0 and len(applications_to_be_notified) > 0:
            self.__tray_icon.setIcon(QIcon(":/Yellow.png"))

        self.__applications_on_notification = applications_to_be_notified

    def __on_list_widget_selection_changed(self) -> None:
        """
        Selection changed event handler for the list widget.
        """
        self.__delete_button.setDisabled(len(self.__list_widget.selectedIndexes()) == 0)

    def __on_add_edit_text_changed(self, text: str) -> None:
        """
        Text changed event handler for the add edit field.
        :param text: Edit field text.
        """
        self.__add_button.setDisabled(len(text) == 0)

    def __on_add_button_clicked(self) -> None:
        """
        Clicked event handler for the add button.
        """
        if self.__add_edit.text():
            item = QListWidgetItem(self.__add_edit.text())
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.__list_widget.addItem(item)
            self.__add_edit.clear()

    def __on_list_button_clicked(self) -> None:
        """
        Clicked event handler for the list button.
        """
        AppListDialog(self).exec_()

    def __on_delete_button_clicked(self) -> None:
        """
        Clicked event handler for the delete button.
        """
        for item in self.__list_widget.selectedItems():
            self.__list_widget.takeItem(self.__list_widget.row(item))

    def __set_autostart_check_box(self) -> None:
        """
        Set the state of the auto-start check box based on the registry.
        """
        # noinspection PyBroadException
        try:
            handle = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0,
                                    winreg.KEY_QUERY_VALUE)
            winreg.QueryValueEx(handle, self.AUTOSTART_REGISTRY_KEY)
        # pylint: disable=broad-except
        except Exception:
            self.__autostart_check_box.setCheckState(Qt.Unchecked)
        else:
            self.__autostart_check_box.setCheckState(Qt.Checked)

    def __on_autostart_check_box_state_changed(self, state: Qt.CheckState) -> None:
        """
        Check state event handler for the auto-start check box.
        :param state: Check box state.
        """
        try:
            handle = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0,
                                    winreg.KEY_SET_VALUE)
            if state == Qt.Checked:
                winreg.SetValueEx(handle, self.AUTOSTART_REGISTRY_KEY, 0, winreg.REG_SZ, sys.executable)
                LOG.debug("Auto-start enabled.")
            else:
                winreg.DeleteValue(handle, self.AUTOSTART_REGISTRY_KEY)
                LOG.debug("Auto-start disabled.")
        # pylint: disable=broad-except
        except Exception as exception:
            # Show an error message box
            box = QMessageBox()
            box.setIcon(QMessageBox.Warning)
            box.setWindowIcon(QIcon(":/Yellow.png"))
            box.setWindowTitle("Error")
            box.setText(str(exception))
            box.exec_()

            # Restore previous box state (without triggering another event)
            self.__autostart_check_box.blockSignals(True)
            self.__autostart_check_box.setCheckState(Qt.Unchecked if state == Qt.Checked else Qt.Checked)
            self.__autostart_check_box.blockSignals(False)

    def __on_repeat_check_box_state_changed(self, state: Qt.CheckState) -> None:
        """
        Check state event handler for the repeat notifications check box.
        :param state: Check box state.
        """
        self.__repeat_spin.setEnabled(state == Qt.Checked)

    def __on_show(self) -> None:
        """
        Event handler for the tray show action.
        """
        self.__timer_polling.stop()
        self.show()
        self.activateWindow()

    def __on_enable_disable(self) -> None:
        """
        Event handler for the tray enable/disable action.
        """
        if self.__timer_polling.isActive():
            self.__applications_on_notification = []
            self.__tray_icon.setIcon(QIcon(":/Disabled.png"))
            self.__tray_enable_disable_action.setText("Enable")
            self.__tray_enable_disable_action.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.__timer_polling.stop()
            LOG.info("Application disabled.")
        else:
            self.__tray_icon.setIcon(QIcon(":/Grey.png"))
            self.__tray_enable_disable_action.setText("Disable")
            self.__tray_enable_disable_action.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            self.__timer_polling.start(self.TIMER_INVTERVAL_POLLING_MS)
            LOG.info("Application enabled.")

    @staticmethod
    def __on_about() -> None:
        """
        Event handler for the tray about action.
        """
        about_dialog = QDialog()
        about_dialog.setWindowTitle("About")
        about_dialog.setWindowIcon(QIcon(":/Yellow.png"))
        about_dialog.setWindowFlag(Qt.WindowStaysOnTopHint)

        icon = QLabel()
        pixmap = QPixmap(":/Yellow.png").scaled(60, 60, Qt.KeepAspectRatio)
        icon.setPixmap(pixmap)

        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)

        title = QLabel("Taskbar Notifier")
        title.setFont(title_font)

        url = QLabel("<a href='https://github.com/rfkd/TaskbarNotifier'>"
                     "https://github.com/rfkd/TaskbarNotifier</a>")
        url.setOpenExternalLinks(True)

        vbox_left = QVBoxLayout()
        vbox_left.setContentsMargins(0, 0, 25, 0)
        vbox_left.addWidget(icon)
        vbox_left.addStretch(1)

        vbox_right = QVBoxLayout()
        vbox_right.addWidget(title)
        vbox_right.addWidget(QLabel(f"Version: {MainWindow.FULL_VERSION}\n"))
        vbox_right.addWidget(url)
        vbox_right.addWidget(QLabel("Copyright © 2018-2022 Ralf Dauberschmidt"))
        vbox_right.addWidget(QLabel("\nThis application is licensed under the GPL."))

        hbox = QHBoxLayout()
        hbox.addLayout(vbox_left)
        hbox.addLayout(vbox_right)

        about_dialog.setLayout(hbox)
        about_dialog.show()
        about_dialog.setFixedSize(about_dialog.size())
        about_dialog.exec_()

    def __on_exit(self) -> None:
        """
        Event handler for the tray exit action.
        """
        self.__serialize_data()
        self.__tray_icon.setVisible(False)
        qApp.quit()

    # pylint: disable=invalid-name
    def closeEvent(self, event: QCloseEvent) -> None:
        """
        On close event handler.
        :param event: Close event.
        """
        # Prevent that the app closes upon closing the main window
        event.ignore()

        self.__serialize_data()
        self.hide()
        self.__timer_polling.start(self.TIMER_INVTERVAL_POLLING_MS)

        LOG.info("Main window hidden.")

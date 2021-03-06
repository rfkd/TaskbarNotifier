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

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (QWidget, QDialog, QListWidget, QHBoxLayout, QVBoxLayout, QPushButton, QAbstractItemView,
                             QSystemTrayIcon, QAction, QStyle, QMenu, QListWidgetItem, QGroupBox, QLineEdit, QShortcut,
                             QCheckBox, QLabel, QSpinBox, qApp)

from gui.app_list_dialog import AppListDialog
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
    DATA_FILE_VERSION = 1

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

        self.__notification = None

        # Build the user interface
        self.__build_user_interface()
        self.__setup_tray_icon()

        # Setup the timers
        self.timer_repeat_notification = QTimer(self)
        self.timer_repeat_notification.setSingleShot(True)
        self.timer_polling = QTimer(self)
        self.timer_polling.timeout.connect(self.__on_timer_polling_expired)
        self.timer_polling.start(self.TIMER_INVTERVAL_POLLING_MS)

    # pylint: disable=too-many-statements
    def __build_user_interface(self) -> None:
        """
        Build the user interface.
        """
        self.setWindowTitle(self.WINDOW_TITLE)
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
        self.repeat_spin.setMinimum(self.TIMER_INTERVAL_NOTIFICATION_MIN_S)
        self.repeat_spin.setMaximum(self.TIMER_INTERVAL_NOTIFICATION_MAX_S)
        self.repeat_spin.setValue(self.TIMER_INTERVAL_NOTIFICATION_DEFAULT_S)
        self.repeat_spin.setToolTip(f"Value in seconds between {self.TIMER_INTERVAL_NOTIFICATION_MIN_S} "
                                    f"and {self.TIMER_INTERVAL_NOTIFICATION_MAX_S}")

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
        show_action.setIcon(self.style().standardIcon(QStyle.SP_ArrowUp))
        show_action.triggered.connect(self.__on_show)
        tray_menu.addAction(show_action)

        self.tray_enable_disable_action = QAction("Disable", self)
        self.tray_enable_disable_action.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.tray_enable_disable_action.triggered.connect(self.__on_enable_disable)
        tray_menu.addAction(self.tray_enable_disable_action)

        about_action = QAction("About", self)
        about_action.setIcon(self.style().standardIcon(QStyle.SP_FileDialogInfoView))
        about_action.triggered.connect(self.__on_about)
        tray_menu.addAction(about_action)

        quit_action = QAction("Exit", self)
        quit_action.setIcon(self.style().standardIcon(QStyle.SP_BrowserStop))
        quit_action.triggered.connect(self.__on_exit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

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
                data_file_version = file.readline()
                if int(data_file_version) != self.DATA_FILE_VERSION:
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
        Polling timer expired event handler.
        """
        if len(self.list_widget) == 0:
            return

        # Check whether a listed application is active
        applications_to_be_notified = []
        active_applications = get_active_applications([self.WINDOW_TITLE])
        for expression in [str(self.list_widget.item(i).text()) for i in range(self.list_widget.count())]:
            for app in active_applications:
                if expression in app:
                    applications_to_be_notified.append(app)

        # Create a notification for active applications
        if applications_to_be_notified:
            repeat_notification = self.repeat_check_box.checkState() == Qt.Checked

            if (repeat_notification and not self.timer_repeat_notification.isActive()) \
                    or applications_to_be_notified != self.applications_on_notification:
                if self.__notification:
                    self.__notification.stop()
                    self.__notification.deleteLater()
                LOG.info("Showing notification for: %s", ", ".join(applications_to_be_notified))
                self.__notification = Notification("Taskbar Notifier", "\n".join(applications_to_be_notified),
                                                   self.NOTIFICATION_DURATION_S)

                if repeat_notification:
                    self.timer_repeat_notification.start(self.repeat_spin.value() * 1000)

        # Change the tray icon depending on the notification state
        if len(self.applications_on_notification) > 0 and len(applications_to_be_notified) == 0:
            self.tray_icon.setIcon(QIcon(":/Grey.png"))
        elif len(self.applications_on_notification) == 0 and len(applications_to_be_notified) > 0:
            self.tray_icon.setIcon(QIcon(":/Yellow.png"))

        self.applications_on_notification = applications_to_be_notified

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
        if self.add_edit.text():
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

    def __on_enable_disable(self) -> None:
        """
        Event handler for the tray enable/disable action.
        """
        if self.timer_polling.isActive():
            self.applications_on_notification = []
            self.tray_icon.setIcon(QIcon(":/Disabled.png"))
            self.tray_enable_disable_action.setText("Enable")
            self.tray_enable_disable_action.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.timer_polling.stop()
            LOG.info("Application disabled.")
        else:
            self.tray_icon.setIcon(QIcon(":/Grey.png"))
            self.tray_enable_disable_action.setText("Disable")
            self.tray_enable_disable_action.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            self.timer_polling.start(self.TIMER_INVTERVAL_POLLING_MS)
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
        vbox_right.addWidget(QLabel("Copyright © 2018-2020 Ralf Dauberschmidt"))
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
        self.timer_polling.start(self.TIMER_INVTERVAL_POLLING_MS)

        LOG.info("Main window hidden.")

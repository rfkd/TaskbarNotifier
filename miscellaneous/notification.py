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

from enum import Enum

from PyQt5.QtCore import Qt, QEasingCurve, QPoint, QPropertyAnimation, QRectF, QSequentialAnimationGroup, pyqtProperty
from PyQt5.QtGui import QColor, QFont, QMouseEvent, QPainter, QPainterPath, QPalette, QPen, QPixmap
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QVBoxLayout, QWidget

# Define the logger
LOG = logging.getLogger(os.path.basename(__file__).split('.')[0])


class Notification(QWidget):
    """
    Class representing a notification.
    """
    # Notification title color
    TITLE_COLOR = QColor(255, 255, 255)

    # Notification text color
    TEXT_COLOR = QColor(170, 170, 170)

    # Notification background color
    BACKGROUND_COLOR = QColor(117, 16, 0)

    # Minimum height of the notifcation (unit: pixels)
    MINIMUM_HEIGHT = 100

    # Minimum width of the notifcation (unit: pixels)
    MINIMUM_WIDTH = 360

    # Fading duration (unit: milliseconds)
    FADING_DURATION = 500

    class Location(Enum):
        """
        Enumeration representing the location of the notification.
        """
        BOTTOM_LEFT = 0
        BOTTOM_RIGHT = 1
        TOP_LEFT = 2
        TOP_RIGHT = 3

    def __init__(self, title: str, text: str, duration_s: int, location: Location) -> None:
        """
        Class constructor.
        :param title: Notification title.
        :param text: Notification text.
        :param duration_s: Notification duration in seconds.
        :param location: Location of the notification.
        """
        super().__init__()

        self.__animation_group = None
        self.__duration_ms = duration_s * 1000
        assert self.__duration_ms > 2 * self.FADING_DURATION
        self.__location = location

        self.__build_user_interface(title, text)
        self.__show()

    # pylint: disable=invalid-name
    def mousePressEvent(self, _: QMouseEvent) -> None:
        """
        Mouse event handler.
        :param _: Captured mouse event.
        """
        # Close the notification on any mouse event
        self.stop()

    # pylint: disable=invalid-name
    def paintEvent(self, event) -> None:
        """
        Paint event handler.
        :param event: Paint event.
        """
        super().paintEvent(event)

        rectangle_path = QPainterPath()
        rectangle_path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 5, 5)

        painter = QPainter(self)
        painter.setPen(QPen(self.BACKGROUND_COLOR, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(self.BACKGROUND_COLOR)
        painter.drawPath(rectangle_path)

    # pylint: disable=invalid-name
    def windowOpacity(self) -> float:
        """
        Get the window opacity.
        :return: Window opacity.
        """
        return super().windowOpacity()

    # pylint: disable=invalid-name
    def setWindowOpacity(self, opacity: float):
        """
        Set the window opacity.
        :param opacity: Window opacity.
        :return:
        """
        super().setWindowOpacity(opacity)

    def __build_user_interface(self, title: str, text: str) -> None:
        """
        Build the user interface.
        :param title: Notification title.
        :param text: Notification text.
        """
        # Window behavior
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMinimumWidth(self.MINIMUM_WIDTH)
        self.setMinimumHeight(self.MINIMUM_HEIGHT)

        # Icon
        icon_element = QLabel()
        icon_element.setPixmap(QPixmap(":/Yellow.png").scaled(40, 40, Qt.KeepAspectRatio))
        icon_element.setContentsMargins(0, 0, 10, 0)

        # Title
        title_element = QLabel(title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_element.setFont(title_font)
        title_palette = QPalette()
        title_palette.setColor(QPalette.WindowText, self.TITLE_COLOR)
        title_element.setPalette(title_palette)
        title_element.setContentsMargins(0, 5, 0, 0)

        # Text
        text_element = QLabel(text)
        text_font = QFont()
        text_font.setPointSize(10)
        text_element.setFont(text_font)
        text_palette = QPalette()
        text_palette.setColor(QPalette.WindowText, self.TEXT_COLOR)
        text_element.setPalette(text_palette)
        text_element.setContentsMargins(0, 5, 0, 15)

        # Right vertical layout
        vbox_right = QVBoxLayout()
        vbox_right.addWidget(title_element)
        vbox_right.addWidget(text_element)
        vbox_right.addStretch(1)

        # Horizonal layout
        hbox = QHBoxLayout(self)
        hbox.addWidget(icon_element)
        hbox.addLayout(vbox_right, 1)

    def __animate_opacity(self) -> None:
        """
        Animate the opacity by fading-in, waiting and fading-out.
        """
        fade_in_animation = QPropertyAnimation(self, b"opacity")
        fade_in_animation.setStartValue(0.0)
        fade_in_animation.setEndValue(1.0)
        fade_in_animation.setEasingCurve(QEasingCurve.InQuad)
        fade_in_animation.setDuration(self.FADING_DURATION)

        fade_out_animation = QPropertyAnimation(self, b"opacity")
        fade_out_animation.setStartValue(1.0)
        fade_out_animation.setEndValue(0.0)
        fade_out_animation.setEasingCurve(QEasingCurve.InQuad)
        fade_out_animation.setDuration(self.FADING_DURATION)

        self.__animation_group = QSequentialAnimationGroup(self)
        self.__animation_group.addAnimation(fade_in_animation)
        self.__animation_group.addPause(self.__duration_ms - (2 * self.FADING_DURATION))
        self.__animation_group.addAnimation(fade_out_animation)
        self.__animation_group.finished.connect(self.close)
        self.__animation_group.start()

    def __show(self) -> None:
        """
        Show the notification.
        """
        super().show()

        desktop = QApplication.instance().desktop()
        offset = 10
        if self.__location == Notification.Location.BOTTOM_LEFT:
            origin = QPoint(offset, desktop.availableGeometry().height() - self.height() - offset)
        elif self.__location == Notification.Location.BOTTOM_RIGHT:
            origin = QPoint(desktop.screenGeometry().width() - self.width() - offset,
                            desktop.availableGeometry().height() - self.height() - offset)
        elif self.__location == Notification.Location.TOP_LEFT:
            origin = QPoint(offset, offset)
        else:
            assert self.__location == Notification.Location.TOP_RIGHT
            origin = QPoint(desktop.screenGeometry().width() - self.width() - offset, offset)
        self.move(origin)

        self.__animate_opacity()

    def stop(self) -> None:
        """
        Stop the notification.
        """
        self.hide()
        self.__animation_group.stop()
        self.close()

    # Redefine the opacity property
    opacity = pyqtProperty(float, windowOpacity, setWindowOpacity)


if __name__ == "__main__":
    LOG.critical("This module is not supposed to be executed.")
    sys.exit(1)

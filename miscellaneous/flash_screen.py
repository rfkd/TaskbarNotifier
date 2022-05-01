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

from PyQt5.QtCore import Qt, QEasingCurve,  QPropertyAnimation, QRectF, QSequentialAnimationGroup, pyqtProperty
from PyQt5.QtGui import QColor, QMouseEvent, QPainter, QPainterPath
from PyQt5.QtWidgets import QWidget

# Define the logger
LOG = logging.getLogger(os.path.basename(__file__).split('.')[0])


class FlashScreen(QWidget):
    """
    Class representing a flash screen.
    """
    # Flash screen color
    FLASH_COLOR = QColor(117, 16, 0)

    # Flash duration (unit: milliseconds)
    FLASH_DURATION = 400

    # Flash window opacity (0..1)
    FLASH_OPACITY = 0.4

    def __init__(self) -> None:
        """
        Class constructor.
        """
        super().__init__()

        self.__animation_group = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

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
        rectangle_path.addRect(QRectF(0, 0, self.width(), self.height()))

        painter = QPainter(self)
        painter.setBrush(self.FLASH_COLOR)
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

    def __animate_opacity(self) -> None:
        """
        Animate the opacity by fading-out.
        """
        fade_out_animation = QPropertyAnimation(self, b"opacity")
        fade_out_animation.setStartValue(self.FLASH_OPACITY)
        fade_out_animation.setEndValue(0.0)
        fade_out_animation.setEasingCurve(QEasingCurve.InQuad)
        fade_out_animation.setDuration(self.FLASH_DURATION)

        self.__animation_group = QSequentialAnimationGroup(self)
        self.__animation_group.addAnimation(fade_out_animation)
        self.__animation_group.finished.connect(self.close)
        self.__animation_group.start()

    def __show(self) -> None:
        """
        Show the notification.
        """
        super().show()

        self.showMaximized()
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

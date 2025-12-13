from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QCursor, QFocusEvent, QFont
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

STYLE_POPUP_CONTAINER = """
    QFrame {
        background-color: #FFFFFF;
        border: none;
        border-radius: 6px;
    }
"""

STYLE_HEADER = """
    QWidget {
        background-color: #F1F1F1;
        border-bottom: 1px solid #D9D9D9;
    }
    QLabel {
        color: #5E5E5E;
        background-color: transparent;
        border: none;
        padding: 0px 8px;
        font-family: "Noto Sans", Sans-Serif;
        font-size: 13px;
        font-weight: bold;
    }
"""

STYLE_ITEM = """
    QPushButton {
        color: #5E5E5E;
        background-color: #FFFFFF;
        border: none;
        border-radius: 0px;
        text-align: left;
        padding: 0px 8px;
        font-family: "Noto Sans", Sans-Serif;
        font-size: 13px;
    }
    QPushButton:hover {
        background-color: #B1D6F1;
    }
    /* Rounded corners for the last item handled logically or via generic if needed */
"""

# Specific style for bottom rounded corners
STYLE_ITEM_LAST = """
    QPushButton {
        border-bottom-left-radius: 6px;
        border-bottom-right-radius: 6px;
    }
"""


class PopupMenu(QFrame):
    def __init__(
        self,
        *,
        parent: Optional[QWidget] = None,
        font: Optional[QFont] = None,
        title: Optional[str] = None,
    ) -> None:
        super().__init__(parent, Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.icon_font = font if font else QFont()
        # Ensure icon font size is appropriate if not set
        if font is None:
            self.icon_font.setPixelSize(16)

        self.layout_main = QVBoxLayout(self)
        self.layout_main.setContentsMargins(10, 10, 10, 10)
        self.layout_main.setSpacing(0)

        # Container to hold everything and provide background/border radius
        self.container = QFrame()
        self.container.setStyleSheet(STYLE_POPUP_CONTAINER)
        self.layout_container = QVBoxLayout(self.container)
        self.layout_container.setContentsMargins(0, 0, 0, 0)
        self.layout_container.setSpacing(0)

        self.layout_main.addWidget(self.container)

        self.header_widget: Optional[QWidget] = None
        self.items: list[QPushButton] = []

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 50))
        self.container.setGraphicsEffect(shadow)

        self.set_title(title)

    def set_title(self, text: Optional[str] = None) -> None:
        if self.header_widget:
            self.header_widget.deleteLater()
            self.layout_container.removeWidget(self.header_widget)

        if not text:
            # Empty header, just a small spacer
            self.header_widget = QWidget()
            self.header_widget.setFixedHeight(15)
            self.header_widget.setStyleSheet(STYLE_HEADER)
            self.layout_container.insertWidget(0, self.header_widget)
            return

        self.header_widget = QWidget()
        self.header_widget.setFixedHeight(37)
        self.header_widget.setStyleSheet(STYLE_HEADER)

        bg_layout = QHBoxLayout(self.header_widget)
        bg_layout.setContentsMargins(0, 0, 0, 0)
        bg_layout.setSpacing(5)

        # Move Text - Centered
        lbl_text = QLabel(text)
        lbl_text.setStyleSheet("color: #5E5E5E;")
        lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bg_layout.addWidget(lbl_text)

        # Insert at top
        self.layout_container.insertWidget(0, self.header_widget)

    def add_item(
        self, text: str, icon_data: Optional[str], callback: Callable[[], None]
    ) -> None:
        btn = QPushButton()
        btn.setFixedHeight(33)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QHBoxLayout(btn)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(10)

        if icon_data:
            lbl_icon = QLabel(icon_data)
            # Make icon smaller
            font = QFont(self.icon_font)
            current_size = font.pixelSize()
            if current_size == -1:
                # If pixel size not set, try point size or default
                current_size = 16
            font.setPixelSize(max(1, current_size - 4))  # Reduce by 4

            lbl_icon.setFont(font)
            lbl_icon.setStyleSheet(
                "background-color: transparent; border: none; color: #5E5E5E;"
            )
            # Fix hover issue
            lbl_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            layout.addWidget(lbl_icon)

        lbl_text = QLabel(text)
        lbl_text.setStyleSheet(
            "background-color: transparent; border: none; color: #5E5E5E;"
        )
        # Fix hover issue
        lbl_text.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(lbl_text)

        layout.addStretch()

        btn.clicked.connect(self._on_item_clicked(callback))
        btn.setStyleSheet(STYLE_ITEM)

        self.layout_container.addWidget(btn)
        self.items.append(btn)

        self._update_corners()

    def _on_item_clicked(self, callback: Callable[[], None]) -> Callable[[], None]:
        def wrapper() -> None:
            self.close()
            callback()

        return wrapper

    def _update_corners(self) -> None:
        # Apply rounded corners to the last item if it exists
        if not self.items:
            return

        # Reset styles for all items to default
        for btn in self.items:
            btn.setStyleSheet(STYLE_ITEM)

        # Apply special style to the last one
        last_btn = self.items[-1]
        # Combine default style and last item style
        last_btn.setStyleSheet(STYLE_ITEM + STYLE_ITEM_LAST)

    def show_at_cursor(self) -> None:
        self.adjustSize()
        self.move(QCursor.pos())
        self.show()

    def focusOutEvent(self, event: QFocusEvent) -> None:
        self.close()
        super().focusOutEvent(event)

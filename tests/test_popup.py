from typing import Any

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QFocusEvent, QFont
from PySide6.QtWidgets import QWidget

from chess_widgets.popup import PopupMenu


def test_popup_menu(qtbot: Any) -> None:
    """Test the PopupMenu widget functionality."""
    # Create the widget
    widget = QWidget()
    popup = PopupMenu(parent=widget)
    qtbot.addWidget(popup)
    popup.show()

    # Check default header state (None -> empty header spacer created)
    assert popup.header_widget is not None
    assert popup.header_widget.height() == 15

    # Test constructor with title
    popup_titled = PopupMenu(parent=widget, title="Init Title")
    qtbot.addWidget(popup_titled)
    assert popup_titled.header_widget is not None
    assert popup_titled.header_widget.height() == 37

    # Set header with text (on the first popup)
    popup.set_title("1. e4")
    assert popup.header_widget is not None
    # Height should be 37 for text header
    assert popup.header_widget.height() == 37

    # Check header content via children (quick simple check)
    # The header has a QLabel child
    popup.header_widget.findChildren(QWidget)
    # Actually header widget has labels in layout

    # Set empty header
    popup.set_title("")
    assert popup.header_widget is not None
    # Height should be reduced for empty header
    assert popup.header_widget.height() == 15

    # Set None header (should be same as empty)
    popup.set_title(None)
    assert popup.header_widget is not None
    assert popup.header_widget.height() == 15

    # Add items
    callback_called = False

    def my_callback() -> None:
        nonlocal callback_called
        callback_called = True

    popup.add_item("Test Item", None, my_callback)

    assert len(popup.items) == 1

    # Test item click
    btn = popup.items[0]
    qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)
    assert callback_called
    assert not popup.isVisible()  # Should close on click

    # Reset
    popup.show()
    assert popup.isVisible()

    # Test focus out
    popup.focusOutEvent(QFocusEvent(QEvent.Type.FocusOut))
    # It calls close(), so it should be hidden
    assert not popup.isVisible()

    # Test with custom font and icon
    popup2 = PopupMenu(parent=widget, font=None)
    qtbot.addWidget(popup2)
    # Testing icon font logic when pixel size is -1
    # QFont() default pixelSize is -1
    popup2.icon_font = QFont()
    assert popup2.icon_font.pixelSize() == -1
    popup2.add_item("Icon Item", "X", lambda: None)

    # Test show_at_cursor
    popup2.show_at_cursor()
    assert popup2.isVisible()

    # Test _update_corners with empty items
    popup3 = PopupMenu(parent=widget)
    qtbot.addWidget(popup3)
    popup3._update_corners()  # Should return early

    # Test corners update
    popup2.add_item("Item 2", "Y", lambda: None)
    # 2 items, last one should have rounded corners

    # Update corners called internally, we trust styles are applied
    # but we can check if execution paths are covered.


def test_popup_styling_and_logic(qtbot: Any) -> None:
    """Additional coverage for styling logic."""
    popup = PopupMenu()
    qtbot.addWidget(popup)

    # Add multiple items to trigger styling update loops
    popup.add_item("1", None, lambda: None)
    popup.add_item("2", None, lambda: None)
    popup.add_item("3", None, lambda: None)

    assert len(popup.items) == 3

import chess
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QMouseEvent
from pytestqt.qtbot import QtBot

from chess_widgets.board import BoardWidget


def test_undo_empty_board(qtbot: QtBot) -> None:
    """Test that undoing on an empty board does nothing."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Ensure no moves have been played
    assert len(widget._board.move_stack) == 0

    # Try to undo - should return early without error
    # This tests: if not self._board.move_stack: return
    widget.undo_move(animate=False)

    # Board should still be in starting position
    assert len(widget._board.move_stack) == 0
    assert widget._board.fen() == chess.STARTING_FEN


def test_undo_empty_board_with_animation(qtbot: QtBot) -> None:
    """Test that undoing on an empty board with animation does nothing."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Ensure no moves have been played
    assert len(widget._board.move_stack) == 0

    # Try to undo with animation - should return early without error
    widget.undo_move(animate=True)

    # Board should still be in starting position
    assert len(widget._board.move_stack) == 0
    assert widget._board.fen() == chess.STARTING_FEN

    # No animation should be active
    assert not widget._anim_timer.isActive()


def test_pos_to_square_outside_board(qtbot: QtBot) -> None:
    """Test that _pos_to_square returns None for positions outside the board."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.resize(400, 400)
    widget.show()
    qtbot.waitExposed(widget)

    # Get board rect to know the boundaries
    rect = widget._get_board_rect()

    # Test position outside to the left
    pos_left = QPointF(rect.x() - 10, rect.y() + 100)
    result = widget._pos_to_square(pos_left)
    assert (
        result is None
    ), f"Expected None for position outside board (left), got {result}"

    # Test position outside to the right
    pos_right = QPointF(rect.x() + rect.width() + 10, rect.y() + 100)
    result = widget._pos_to_square(pos_right)
    assert (
        result is None
    ), f"Expected None for position outside board (right), got {result}"

    # Test position outside above
    pos_top = QPointF(rect.x() + 100, rect.y() - 10)
    result = widget._pos_to_square(pos_top)
    assert (
        result is None
    ), f"Expected None for position outside board (top), got {result}"

    # Test position outside below
    pos_bottom = QPointF(rect.x() + 100, rect.y() + rect.height() + 10)
    result = widget._pos_to_square(pos_bottom)
    assert (
        result is None
    ), f"Expected None for position outside board (bottom), got {result}"


def test_pos_to_square_edge_cases(qtbot: QtBot) -> None:
    """Test edge cases in _pos_to_square coordinate calculations."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.resize(400, 400)
    widget.show()
    qtbot.waitExposed(widget)

    rect = widget._get_board_rect()

    # Test exact corner positions (should be valid)
    pos_topleft = QPointF(rect.x() + 1, rect.y() + 1)
    result = widget._pos_to_square(pos_topleft)
    assert result is not None, "Top-left corner should be valid"

    # Test position at exact edge (should still be inside)
    pos_edge = QPointF(rect.x(), rect.y())
    result = widget._pos_to_square(pos_edge)
    # This might be None or valid depending on implementation
    # The key is it doesn't crash

    # Test with flipped board
    widget.set_flipped(True)
    pos_center = QPointF(rect.x() + rect.width() / 2, rect.y() + rect.height() / 2)
    result = widget._pos_to_square(pos_center)
    assert result is not None, "Center position should always be valid"


def test_click_outside_then_outside_again(qtbot: QtBot) -> None:
    """Test clicking outside board multiple times."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.resize(400, 400)
    widget.show()
    qtbot.waitExposed(widget)

    # First select a piece
    rect = widget._get_board_rect()
    square_size = rect.width() / 8

    # Click e2 (white pawn)
    e2_x = rect.x() + 4 * square_size + square_size / 2
    e2_y = rect.y() + 6 * square_size + square_size / 2
    e2_pos = QPointF(e2_x, e2_y)

    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        e2_pos,
        e2_pos,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mousePressEvent(event)

    # Verify selection
    assert widget._selected_square == chess.E2

    # Click outside board - this should clear selection and trigger lines 206-207
    outside_pos = QPointF(0, 0)
    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        outside_pos,
        outside_pos,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mousePressEvent(event)

    # Verify selection cleared
    assert widget._selected_square is None

    # Click outside again when nothing is selected
    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        outside_pos,
        outside_pos,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mousePressEvent(event)

    # Should still be None
    assert widget._selected_square is None


def test_mouse_release_outside_after_invalid_drag(qtbot: QtBot) -> None:
    """Test releasing mouse outside board after dragging."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.resize(400, 400)
    widget.show()
    qtbot.waitExposed(widget)

    rect = widget._get_board_rect()
    square_size = rect.width() / 8

    # Start drag on e2
    e2_x = rect.x() + 4 * square_size + square_size / 2
    e2_y = rect.y() + 6 * square_size + square_size / 2
    e2_pos = QPointF(e2_x, e2_y)

    press_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        e2_pos,
        e2_pos,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mousePressEvent(press_event)

    assert widget._is_dragging is True

    # Release outside board - this should trigger lines 275-276
    outside_pos = QPointF(-10, -10)
    release_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        outside_pos,
        outside_pos,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mouseReleaseEvent(release_event)

    # Verify dragging stopped
    assert widget._is_dragging is False
    # Board should not have changed
    assert widget._board.fen() == chess.STARTING_FEN

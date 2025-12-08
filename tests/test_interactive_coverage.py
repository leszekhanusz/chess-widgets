import chess
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QMouseEvent
from pytestqt.qtbot import QtBot

from chess_widgets import BoardWidget


def test_interactive_flag(qtbot: QtBot) -> None:
    """Test the interactive flag behavior on BoardWidget."""
    widget = BoardWidget(interactive=False)
    qtbot.addWidget(widget)
    widget.resize(400, 400)
    widget.show()
    qtbot.waitExposed(widget)

    rect = widget._get_board_rect()
    square_size = rect.width() / 8

    # Coordinates for e2 (white pawn)
    e2_x = rect.x() + 4 * square_size + square_size / 2
    e2_y = rect.y() + 6 * square_size + square_size / 2
    e2_pos = QPointF(e2_x, e2_y)

    # 1. Test Mouse Press when interactive=False (Line 218 coverage)
    press_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        e2_pos,
        e2_pos,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mousePressEvent(press_event)

    # Should NOT be selected
    assert widget._selected_square is None
    assert widget._is_dragging is False

    # 2. Test Mouse Move when interactive=False (Line 255 coverage)
    # Move mouse over e4
    e4_x = rect.x() + 4 * square_size + square_size / 2
    e4_y = rect.y() + 4 * square_size + square_size / 2
    e4_pos = QPointF(e4_x, e4_y)

    move_event = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        e4_pos,
        e4_pos,
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    # We need to set hover square to something first to verify it *doesn't* change?
    # Actually, hover square defaults to None.
    # If move event works, it updates hover_square.
    # If it returns early, hover_square remains None.

    widget.mouseMoveEvent(move_event)
    assert widget._hover_square is None

    # 3. Test Mouse Release when interactive=False (Line 271 coverage)
    release_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        e2_pos,
        e2_pos,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mouseReleaseEvent(release_event)
    # Should execute safely and do nothing
    assert widget._selected_square is None

    # -------------------------------------------------------------
    # Enable interactivity
    widget.interactive = True

    # 1. Test Mouse Press (Should work now)
    widget.mousePressEvent(press_event)
    assert widget._selected_square == chess.E2
    assert widget._is_dragging is True

    # 2. Test Mouse Move (Should work now)
    widget.mouseMoveEvent(move_event)
    assert widget._hover_square == chess.E4

    # 3. Test Mouse Release
    # Release on e4 (legal move)
    release_event_e4 = QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        e4_pos,
        e4_pos,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )

    # We need to connect to signal to verify move played
    move_played = False

    def on_move_played(move, info):
        nonlocal move_played
        move_played = True

    widget.move_played.connect(on_move_played)

    widget.mouseReleaseEvent(release_event_e4)

    assert move_played
    assert widget._board.piece_at(chess.E4) is not None

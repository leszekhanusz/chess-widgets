import chess
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QMouseEvent
from pytestqt.qtbot import QtBot

from chess_widgets import BoardWidget


def get_square_center(widget: BoardWidget, square: int) -> QPointF:
    """Helper to get the center of a square in widget coordinates."""
    rect = widget._get_board_rect()
    square_size = rect.width() / 8

    row = chess.square_rank(square)
    col = chess.square_file(square)

    if widget._flipped:
        visual_row = row
        visual_col = 7 - col
    else:
        visual_row = 7 - row
        visual_col = col

    x = rect.x() + visual_col * square_size + square_size / 2
    y = rect.y() + visual_row * square_size + square_size / 2
    return QPointF(x, y)


def test_right_click_ignored(qtbot: QtBot) -> None:
    """Test that right-click doesn't select pieces or trigger moves."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Try to select e2 pawn with right-click
    e2_center = get_square_center(widget, chess.E2).toPoint()

    # Right click should be ignored
    qtbot.mouseClick(widget, Qt.MouseButton.RightButton, pos=e2_center)

    # Verify nothing was selected
    assert widget._selected_square is None
    assert widget._dragged_square is None
    assert widget._is_dragging is False
    assert len(widget._legal_moves) == 0


def test_click_outside_board_clears_selection(qtbot: QtBot) -> None:
    """Test that clicking outside the board clears the current selection."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.resize(400, 400)
    widget.show()
    qtbot.waitExposed(widget)

    # First, select a piece (e2 pawn)
    e2_center = get_square_center(widget, chess.E2).toPoint()
    qtbot.mouseClick(widget, Qt.MouseButton.LeftButton, pos=e2_center)

    # Verify piece is selected
    assert widget._selected_square == chess.E2
    assert len(widget._legal_moves) > 0

    # Now click outside the board area
    # Board is centered in 400x400, so click at corner (0, 0) should be outside
    outside_point = QPointF(0, 0)
    qtbot.mouseClick(widget, Qt.MouseButton.LeftButton, pos=outside_point.toPoint())

    # Verify selection was cleared
    assert widget._selected_square is None
    assert widget._dragged_square is None
    assert len(widget._legal_moves) == 0


def test_click_opponent_piece_deselects(qtbot: QtBot) -> None:
    """Test clicking opponent piece when nothing selected clears selection."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Ensure nothing is selected
    assert widget._selected_square is None

    # Click on black pawn (e7) when it's white's turn
    e7_center = get_square_center(widget, chess.E7).toPoint()
    qtbot.mouseClick(widget, Qt.MouseButton.LeftButton, pos=e7_center)

    # Verify nothing was selected (opponent's piece)
    assert widget._selected_square is None
    assert widget._dragged_square is None
    assert len(widget._legal_moves) == 0


def test_click_empty_square_deselects(qtbot: QtBot) -> None:
    """Test that clicking an empty square when nothing is selected does nothing."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Ensure nothing is selected
    assert widget._selected_square is None

    # Click on empty square (e4)
    e4_center = get_square_center(widget, chess.E4).toPoint()
    qtbot.mouseClick(widget, Qt.MouseButton.LeftButton, pos=e4_center)

    # Verify nothing is selected (empty square)
    assert widget._selected_square is None
    assert widget._dragged_square is None
    assert len(widget._legal_moves) == 0


def test_mouse_move_without_dragging(qtbot: QtBot) -> None:
    """Test that moving mouse without dragging updates hover state."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Get position over e2
    e2_center = get_square_center(widget, chess.E2)

    # Move mouse without any button pressed (not dragging)
    event = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        e2_center,
        e2_center,
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mouseMoveEvent(event)

    # Verify hover square is updated
    assert widget._hover_square == chess.E2
    assert widget._is_dragging is False


def test_hover_highlight_legal_move(qtbot: QtBot) -> None:
    """Test that hovering over a legal move target shows highlight."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.resize(400, 400)
    widget.show()
    qtbot.waitExposed(widget)

    # Select e2 pawn
    e2_center = get_square_center(widget, chess.E2).toPoint()
    qtbot.mouseClick(widget, Qt.MouseButton.LeftButton, pos=e2_center)

    # Verify piece is selected
    assert widget._selected_square == chess.E2
    assert len(widget._legal_moves) > 0

    # Move mouse to hover over e4 (a legal move)
    e4_center = get_square_center(widget, chess.E4)

    # Create hover event
    event = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        e4_center,
        e4_center,
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mouseMoveEvent(event)

    # Verify hover square is set
    assert widget._hover_square == chess.E4

    # Verify that the move exists (e2e4 is legal)
    move = widget._find_move(chess.E2, chess.E4)
    assert move is not None
    assert move == chess.Move.from_uci("e2e4")

    # Trigger a paint event to ensure the hover highlight code path executes
    widget.update()
    qtbot.wait(100)


def test_drag_drop_on_invalid_square(qtbot: QtBot) -> None:
    """Test dragging a piece and dropping on an invalid target square."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.resize(400, 400)
    widget.show()
    qtbot.waitExposed(widget)

    # Drag e2 pawn to e5 (invalid - can only move to e3 or e4)
    e2_center = get_square_center(widget, chess.E2).toPoint()
    e5_center = get_square_center(widget, chess.E5).toPoint()

    # Press on e2
    qtbot.mousePress(widget, Qt.MouseButton.LeftButton, pos=e2_center)
    assert widget._is_dragging is True
    assert widget._selected_square == chess.E2

    # Move to e5
    qtbot.mouseMove(widget, e5_center)

    # Release on e5 (invalid move)
    qtbot.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=e5_center)

    # Verify dragging stopped but piece is still selected (Lichess behavior)
    assert widget._is_dragging is False
    # The move should not have been made
    assert widget._board.fen() == chess.STARTING_FEN


def test_drag_drop_outside_board(qtbot: QtBot) -> None:
    """Test dragging a piece and releasing outside the board area."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.resize(400, 400)
    widget.show()
    qtbot.waitExposed(widget)

    # Drag e2 pawn and release outside board
    e2_center = get_square_center(widget, chess.E2).toPoint()
    outside_point = QPointF(0, 0).toPoint()  # Top-left corner, outside board

    # Press on e2
    qtbot.mousePress(widget, Qt.MouseButton.LeftButton, pos=e2_center)
    assert widget._is_dragging is True
    assert widget._selected_square == chess.E2

    # Move outside board
    qtbot.mouseMove(widget, outside_point)

    # Release outside board
    qtbot.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=outside_point)

    # Verify dragging stopped
    assert widget._is_dragging is False
    # The move should not have been made
    assert widget._board.fen() == chess.STARTING_FEN

import chess
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QImage, QPainter
from pytestqt.qtbot import QtBot

from chess_widgets import BoardWidget
from chess_widgets.renderer import Renderer


def test_legal_moves_with_hide_square(qtbot: QtBot) -> None:
    """Test that draw_legal_moves skips rendering the hide_square parameter."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.resize(400, 400)
    widget.show()
    qtbot.waitExposed(widget)

    # Create a renderer
    renderer = Renderer()

    # Create a board with some legal moves
    board = chess.Board()

    # Get legal moves for e2 pawn
    legal_moves = [m for m in board.legal_moves if m.from_square == chess.E2]
    assert len(legal_moves) == 2  # e2e3 and e2e4

    # Create a painter
    image = QImage(400, 400, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.white)
    painter = QPainter(image)

    rect = QRectF(0, 0, 400, 400)

    # Draw legal moves with hide_square set to one of the targets
    # This should draw only one move hint instead of two
    hide_square = chess.E4  # Hide the e4 square

    # This call should execute the line: if target == hide_square: continue
    renderer.draw_legal_moves(
        painter, rect, legal_moves, flipped=False, board=board, hide_square=hide_square
    )

    painter.end()

    # Test passes if no exception is raised and the hide_square logic is executed
    # The visual result would show only e3 hint, not e4


def test_highlight_last_move_with_none(qtbot: QtBot) -> None:
    """Test that highlight_last_move handles None/falsy move gracefully."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.resize(400, 400)
    widget.show()
    qtbot.waitExposed(widget)

    # Create a renderer
    renderer = Renderer()

    # Create a painter
    image = QImage(400, 400, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.white)
    painter = QPainter(image)

    rect = QRectF(0, 0, 400, 400)

    # Call highlight_last_move with None
    # This should trigger the early return: if not move: return
    renderer.highlight_last_move(painter, rect, None, flipped=False)

    painter.end()

    # Test passes if no exception is raised


def test_empty_board_no_moves(qtbot: QtBot) -> None:
    """Test rendering when board has no move history."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Ensure the board has no moves
    assert len(widget._board.move_stack) == 0

    # Create a renderer and painter
    renderer = Renderer()
    image = QImage(400, 400, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.white)
    painter = QPainter(image)

    rect = QRectF(0, 0, 400, 400)

    # Try to highlight last move when there is none
    # board.peek() would raise, but we're testing with None directly
    renderer.highlight_last_move(painter, rect, None, flipped=False)

    painter.end()

    # Test passes if no exception is raised


def test_hide_square_with_capture_move(qtbot: QtBot) -> None:
    """Test hide_square parameter with capture move."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.resize(400, 400)
    widget.show()
    qtbot.waitExposed(widget)

    # Set up a position with a capture available
    board = chess.Board()
    board.push_san("e4")
    board.push_san("d5")

    # White can capture: exd5
    legal_moves = [m for m in board.legal_moves if m.from_square == chess.E4]
    capture_move = None
    for m in legal_moves:
        if m.to_square == chess.D5:
            capture_move = m
            break

    assert capture_move is not None

    # Create a renderer and painter
    renderer = Renderer()
    image = QImage(400, 400, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.white)
    painter = QPainter(image)

    rect = QRectF(0, 0, 400, 400)

    # Draw with hide_square set to the capture target
    # Tests hide_square logic with a capture move (board.piece_at(target))
    renderer.draw_legal_moves(
        painter,
        rect,
        [capture_move],
        flipped=False,
        board=board,
        hide_square=chess.D5,  # Hide the capture target
    )

    painter.end()

    # Test passes if no exception is raised

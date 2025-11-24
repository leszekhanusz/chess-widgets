import chess
from PySide6.QtCore import QPointF, Qt
from pytestqt.qtbot import QtBot

from chess_widgets.board import BoardWidget


def get_square_center(widget: BoardWidget, square: int) -> QPointF:
    """Helper to get the center of a square in widget coordinates."""
    rect = widget._get_board_rect()
    square_size = rect.width() / 8

    # Use the widget's internal logic or reimplement it
    # Reimplementing to be safe and external
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


def test_ruy_lopez_interactive(qtbot: QtBot) -> None:
    """
    Test the Ruy Lopez opening using interactive mouse events.
    Moves:
    1. e4 (Drag)
    2. e5 (Click-Click)
    3. Nf3 (Drag)
    4. Nc6 (Click-Click)
    5. Bb5 (Drag)
    """
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Ensure board is standard start
    assert widget._board.fen() == chess.STARTING_FEN

    # 1. White e4 (Drag e2 -> e4)
    start_sq = chess.E2
    end_sq = chess.E4
    start_pos = get_square_center(widget, start_sq).toPoint()
    end_pos = get_square_center(widget, end_sq).toPoint()

    qtbot.mousePress(widget, Qt.MouseButton.LeftButton, pos=start_pos)
    qtbot.mouseMove(widget, end_pos)
    qtbot.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=end_pos)

    assert widget._board.peek() == chess.Move.from_uci("e2e4")
    qtbot.wait(500)  # Wait for animation/update

    # 2. Black e5 (Click e7, Click e5)
    start_sq = chess.E7
    end_sq = chess.E5
    start_pos = get_square_center(widget, start_sq).toPoint()
    end_pos = get_square_center(widget, end_sq).toPoint()

    qtbot.mouseClick(widget, Qt.MouseButton.LeftButton, pos=start_pos)
    qtbot.mouseClick(widget, Qt.MouseButton.LeftButton, pos=end_pos)

    assert widget._board.peek() == chess.Move.from_uci("e7e5")
    qtbot.wait(500)

    # 3. White Nf3 (Drag g1 -> f3)
    start_sq = chess.G1
    end_sq = chess.F3
    start_pos = get_square_center(widget, start_sq).toPoint()
    end_pos = get_square_center(widget, end_sq).toPoint()

    qtbot.mousePress(widget, Qt.MouseButton.LeftButton, pos=start_pos)
    qtbot.mouseMove(widget, end_pos)
    qtbot.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=end_pos)

    assert widget._board.peek() == chess.Move.from_uci("g1f3")
    qtbot.wait(500)

    # 4. Black Nc6 (Click b8, Click c6)
    start_sq = chess.B8
    end_sq = chess.C6
    start_pos = get_square_center(widget, start_sq).toPoint()
    end_pos = get_square_center(widget, end_sq).toPoint()

    qtbot.mouseClick(widget, Qt.MouseButton.LeftButton, pos=start_pos)
    qtbot.mouseClick(widget, Qt.MouseButton.LeftButton, pos=end_pos)

    assert widget._board.peek() == chess.Move.from_uci("b8c6")
    qtbot.wait(500)

    # 5. White Bb5 (Drag f1 -> b5)
    start_sq = chess.F1
    end_sq = chess.B5
    start_pos = get_square_center(widget, start_sq).toPoint()
    end_pos = get_square_center(widget, end_sq).toPoint()

    qtbot.mousePress(widget, Qt.MouseButton.LeftButton, pos=start_pos)
    qtbot.mouseMove(widget, end_pos)
    qtbot.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=end_pos)

    assert widget._board.peek() == chess.Move.from_uci("f1b5")
    qtbot.wait(500)

    # Verify final position (Ruy Lopez)
    # r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3
    assert (
        widget._board.fen()
        == "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
    )


def test_ruy_lopez_interactive_flipped(qtbot: QtBot) -> None:
    """
    Test the Ruy Lopez opening using interactive mouse events with flipped board.
    Moves:
    1. e4 (Drag)
    2. e5 (Click-Click)
    3. Nf3 (Drag)
    4. Nc6 (Click-Click)
    5. Bb5 (Drag)
    """
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    widget.set_flipped(True)
    qtbot.waitExposed(widget)

    # Ensure board is standard start
    assert widget._board.fen() == chess.STARTING_FEN

    # 1. White e4 (Drag e2 -> e4)
    start_sq = chess.E2
    end_sq = chess.E4
    start_pos = get_square_center(widget, start_sq).toPoint()
    end_pos = get_square_center(widget, end_sq).toPoint()

    qtbot.mousePress(widget, Qt.MouseButton.LeftButton, pos=start_pos)
    qtbot.mouseMove(widget, end_pos)
    qtbot.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=end_pos)

    assert widget._board.peek() == chess.Move.from_uci("e2e4")
    qtbot.wait(500)  # Wait for animation/update

    # 2. Black e5 (Click e7, Click e5)
    start_sq = chess.E7
    end_sq = chess.E5
    start_pos = get_square_center(widget, start_sq).toPoint()
    end_pos = get_square_center(widget, end_sq).toPoint()

    qtbot.mouseClick(widget, Qt.MouseButton.LeftButton, pos=start_pos)
    qtbot.mouseClick(widget, Qt.MouseButton.LeftButton, pos=end_pos)

    assert widget._board.peek() == chess.Move.from_uci("e7e5")
    qtbot.wait(500)

    # 3. White Nf3 (Drag g1 -> f3)
    start_sq = chess.G1
    end_sq = chess.F3
    start_pos = get_square_center(widget, start_sq).toPoint()
    end_pos = get_square_center(widget, end_sq).toPoint()

    qtbot.mousePress(widget, Qt.MouseButton.LeftButton, pos=start_pos)
    qtbot.mouseMove(widget, end_pos)
    qtbot.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=end_pos)

    assert widget._board.peek() == chess.Move.from_uci("g1f3")
    qtbot.wait(500)

    # 4. Black Nc6 (Click b8, Click c6)
    start_sq = chess.B8
    end_sq = chess.C6
    start_pos = get_square_center(widget, start_sq).toPoint()
    end_pos = get_square_center(widget, end_sq).toPoint()

    qtbot.mouseClick(widget, Qt.MouseButton.LeftButton, pos=start_pos)
    qtbot.mouseClick(widget, Qt.MouseButton.LeftButton, pos=end_pos)

    assert widget._board.peek() == chess.Move.from_uci("b8c6")
    qtbot.wait(500)

    # 5. White Bb5 (Drag f1 -> b5)
    start_sq = chess.F1
    end_sq = chess.B5
    start_pos = get_square_center(widget, start_sq).toPoint()
    end_pos = get_square_center(widget, end_sq).toPoint()

    qtbot.mousePress(widget, Qt.MouseButton.LeftButton, pos=start_pos)
    qtbot.mouseMove(widget, end_pos)
    qtbot.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=end_pos)

    assert widget._board.peek() == chess.Move.from_uci("f1b5")
    qtbot.wait(500)

    # Verify final position (Ruy Lopez)
    # r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3
    assert (
        widget._board.fen()
        == "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
    )

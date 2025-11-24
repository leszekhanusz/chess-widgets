import sys

import chess
from pytestqt.qtbot import QtBot

from chess_widgets.board import BoardWidget


def test_check_indicator(qtbot: QtBot) -> None:
    """Test that check indicator is displayed when king is in check."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    widget.resize(600, 600)

    # Set up a position where black is in check
    # Scholar's mate position
    board = chess.Board()
    board.push_san("e4")
    board.push_san("e5")
    board.push_san("Bc4")
    board.push_san("Nc6")
    board.push_san("Qh5")
    board.push_san("Nf6")
    board.push_san("Qxf7+")  # Check!

    widget.set_board(board)

    # Verify the board is in check
    assert board.is_check()
    king_square = board.king(board.turn)
    assert king_square is not None

    # Wait for widget to render
    qtbot.wait(1000)


if __name__ == "__main__":
    # For manual testing
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = BoardWidget()
    widget.show()
    widget.resize(600, 600)

    board = chess.Board()
    board.push_san("e4")
    board.push_san("e5")
    board.push_san("Bc4")
    board.push_san("Nc6")
    board.push_san("Qh5")
    board.push_san("Nf6")
    board.push_san("Qxf7+")

    widget.set_board(board)

    print("Board is in check:", board.is_check())
    king_square = board.king(board.turn)
    if king_square is not None:
        print("King square:", chess.square_name(king_square))

    QTimer.singleShot(3000, app.quit)
    app.exec()
    print("Test finished")

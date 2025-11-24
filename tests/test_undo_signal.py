import sys
import unittest
from unittest.mock import MagicMock

import chess
from PySide6.QtWidgets import QApplication

from chess_widgets.board import BoardWidget

# Ensure QApplication exists
app = QApplication.instance() or QApplication(sys.argv)


class TestUndoSignal(unittest.TestCase):
    def test_move_undone_signal(self) -> None:
        board = chess.Board()
        widget = BoardWidget(board=board)

        # Mock the signal receiver
        mock_receiver = MagicMock()
        widget.move_undone.connect(mock_receiver)

        # Play a move
        move = chess.Move.from_uci("e2e4")
        widget.play_move(move, animate=False)

        # Undo the move
        widget.undo_move(animate=False)

        # Verify signal was emitted with the correct move
        mock_receiver.assert_called_once_with(move)
        print("Signal move_undone verified successfully!")


if __name__ == "__main__":
    unittest.main()

import sys

import chess
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

from chess_widgets import BoardWidget


class RecordingDemo(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Fool's Mate Recording Demo")
        self.resize(600, 650)

        # Layout
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.setCentralWidget(widget)

        # Instructions
        label = QLabel("Play as White: 1. f3 ... 2. g4 ...")
        label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(label)

        # Board
        self.board_widget = BoardWidget()
        layout.addWidget(self.board_widget)

        self.board_widget.move_played.connect(self.on_move_played)

    def on_move_played(self, move: chess.Move) -> None:
        # Check if it's Black's turn to respond
        board = self.board_widget._board

        if board.turn == chess.BLACK:
            # Determine response based on history
            if len(board.move_stack) == 1 and board.move_stack[0].uci() == "f2f3":
                # Respond to f3 with e5
                QTimer.singleShot(500, lambda: self.play_response("e7e5"))
            elif len(board.move_stack) == 3 and board.move_stack[2].uci() == "g2g4":
                # Respond to g4 with Qh4#
                QTimer.singleShot(500, lambda: self.play_response("d8h4"))

    def play_response(self, move_uci: str) -> None:
        move = chess.Move.from_uci(move_uci)
        self.board_widget.play_move(move, animate=True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RecordingDemo()
    window.show()
    sys.exit(app.exec())

import os
import sys

import chess.pgn
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from chess_widgets import AnalysisBoardWidget


def main() -> None:
    app = QApplication(sys.argv)

    # Load the example PGN
    pgn_path = os.path.join(os.path.dirname(__file__), "lichess_study_example.pgn")
    with open(pgn_path) as f:
        game = chess.pgn.read_game(f)

    window = QMainWindow()
    window.setWindowTitle("Analysis Board Demo")
    window.setFixedWidth(400)
    window.resize(400, 600)

    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)
    layout.setContentsMargins(0, 0, 0, 0)

    analysis_widget = AnalysisBoardWidget(game)
    layout.addWidget(analysis_widget)

    # Connect signal to print clicked move
    analysis_widget.move_clicked.connect(lambda node: print(f"Clicked: {node.san()}"))

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

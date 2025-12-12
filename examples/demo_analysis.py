import os
import signal
import sys

import chess.pgn
from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from chess_widgets import AnalysisBoardWidget


def main() -> None:
    app = QApplication(sys.argv)

    # Load the example PGN
    pgn_path = os.path.join(os.path.dirname(__file__), "pgn/lichess_study_example.pgn")
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

    # Control buttons
    btn_layout = QHBoxLayout()
    btn_collapse = QPushButton("Collapse All")
    btn_expand = QPushButton("Expand All")

    btn_layout.addWidget(btn_collapse)
    btn_layout.addWidget(btn_expand)
    layout.addLayout(btn_layout)

    analysis_widget = AnalysisBoardWidget(game)
    layout.addWidget(analysis_widget)

    btn_collapse.clicked.connect(lambda: analysis_widget.collapse(True))
    btn_expand.clicked.connect(lambda: analysis_widget.collapse(False))

    # Connect signal to set active node
    def on_move_clicked(
        node: chess.pgn.ChildNode, event: QMouseEvent | None = None
    ) -> None:
        click_type = "Clicked"
        if event:
            if event.button() == Qt.MouseButton.LeftButton:
                analysis_widget.set_active_node(node)
                click_type = "Left clicked"
            elif event.button() == Qt.MouseButton.RightButton:
                click_type = "Right clicked"
        print(f"{click_type}: {node.san()}")

    analysis_widget.move_clicked.connect(on_move_clicked)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    # Enable Ctrl-C to close the application
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    main()

import os
import random
import signal
import sys
from typing import Any, Dict, List

import chess
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont, QFontDatabase, QResizeEvent, QWheelEvent
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from chess_widgets.board import BoardWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Python Chess Board Example")
        self.resize(600, 700)

        # Load Lichess font
        font_path = os.path.join(os.path.dirname(__file__), "assets", "lichess.ttf")
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            self.icon_font = QFont(font_family)
            self.icon_font.setPixelSize(24)
        else:
            print("Failed to load Lichess font")
            self.icon_font = QFont()  # Fallback

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(0)
        layout.setContentsMargins(20, 20, 20, 20)

        # Flip button at the top
        flip_widget = QWidget()
        flip_widget.setFixedHeight(50)  # Same height as nav bar
        flip_layout = QHBoxLayout(flip_widget)
        flip_layout.setContentsMargins(0, 0, 0, 10)
        flip_layout.setSpacing(0)

        # Stylesheet for flip button (same as navigation buttons)
        button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:enabled {
                color: rgba(94, 94, 94, 0.9); /* 90% opacity */
            }
            QPushButton:disabled {
                color: rgba(94, 94, 94, 0.5); /* 50% opacity */
            }
            QPushButton:hover:enabled {
                background-color: hsl(209, 66%, 84%);
                color: white;
            }
            QPushButton:pressed {
                background-color: hsl(209, 66%, 70%);
            }
        """

        # Flip icon using standard Unicode symbol
        self.flip_btn = QPushButton("⇅ Flip Board")
        flip_font = QFont(self.icon_font)
        flip_font.setBold(True)
        self.flip_btn.setFont(flip_font)
        self.flip_btn.setStyleSheet(button_style)
        self.flip_btn.clicked.connect(self.toggle_flip)
        self.flip_btn.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )

        # Center the flip button horizontally
        flip_layout.addStretch()
        flip_layout.addWidget(self.flip_btn)
        flip_layout.addStretch()

        layout.addWidget(flip_widget)

        # Board
        self.board_widget = BoardWidget()
        layout.addWidget(self.board_widget)

        # Navigation Bar
        nav_widget = QWidget()
        nav_widget.setFixedHeight(50)  # Restricted height
        nav_layout = QHBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 10, 0, 0)
        nav_layout.setSpacing(5)  # Small spacing between buttons

        # Navigation buttons use the same button_style defined above

        # Icons from Lichess font:
        # First: \ue035
        # Prev: \ue027
        # Next: \ue026
        # Last: \ue034

        self.btn_first = QPushButton("\ue035")
        self.btn_first.setFont(self.icon_font)
        self.btn_first.setStyleSheet(button_style)
        self.btn_first.clicked.connect(self.go_first)
        self.btn_first.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.btn_prev = QPushButton("\ue027")
        self.btn_prev.setFont(self.icon_font)
        self.btn_prev.setStyleSheet(button_style)
        self.btn_prev.clicked.connect(self.go_prev)
        self.btn_prev.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.btn_next = QPushButton("\ue026")
        self.btn_next.setFont(self.icon_font)
        self.btn_next.setStyleSheet(button_style)
        self.btn_next.clicked.connect(self.go_next)
        self.btn_next.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.btn_last = QPushButton("\ue034")
        self.btn_last.setFont(self.icon_font)
        self.btn_last.setStyleSheet(button_style)
        self.btn_last.clicked.connect(self.go_last)
        self.btn_last.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # Add buttons to layout with equal stretch
        nav_layout.addWidget(self.btn_first, 1)
        nav_layout.addWidget(self.btn_prev, 1)
        nav_layout.addWidget(self.btn_next, 1)
        nav_layout.addWidget(self.btn_last, 1)

        layout.addWidget(nav_widget)

        self.board_widget.move_played.connect(self.on_move_played)
        self.board_widget.move_undone.connect(self.on_move_undone)

        self.flipped = False
        self.player_color = chess.WHITE

        # Game history
        self.move_history: List[chess.Move] = []
        self.current_move_index = 0  # 0 means start of game (no moves made)

        self.update_buttons()

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Maintain aspect ratio to keep board square and fill horizontal space."""
        super().resizeEvent(event)

        # Calculate the required height based on width
        # Width includes margins (20px left + 20px right = 40px)
        # Height includes: top margin (20px) + flip button (50px) + board
        # + nav bar (50px) + bottom margin (20px)
        width = self.width()
        board_size = width - 40  # Subtract horizontal margins

        # Total height needed:
        # - Top margin: 20
        # - Flip button: 50
        # - Board: board_size (square)
        # - Nav bar: 50
        # - Bottom margin: 20
        required_height = 20 + 50 + board_size + 50 + 20

        # Adjust height if needed (tolerance to avoid infinite loops)
        if abs(self.height() - required_height) > 5:
            self.resize(width, int(required_height))

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle mouse wheel events to navigate moves."""
        delta = event.angleDelta().y()
        if delta > 0:
            self.go_prev()
        elif delta < 0:
            self.go_next()

    def toggle_flip(self) -> None:
        self.flipped = not self.flipped
        self.board_widget.set_flipped(self.flipped)
        self.player_color = chess.BLACK if self.flipped else chess.WHITE

        # Only trigger opponent move if we are at the last position
        if self.is_at_last_move():
            self.check_opponent_move()

    def on_move_played(self, move: chess.Move, move_info: Dict[str, Any]) -> None:
        interactive = move_info.get("interactive", False)
        print(f"{'Interactive Move' if interactive else 'Move'} played: {move}")

        # If we made an interactive move from a previous position,
        # we truncate the history
        if self.current_move_index < len(self.move_history):
            if interactive:
                self.move_history = self.move_history[: self.current_move_index]
                self.move_history.append(move)
        else:
            self.move_history.append(move)

        self.current_move_index += 1
        self.check_opponent_move()

        print(
            f"Move history: {self.move_history} at position {self.current_move_index}"
        )
        self.update_buttons()

    def on_move_undone(self, move: chess.Move) -> None:
        print(f"Move undone: {move}")
        self.current_move_index -= 1
        print(
            f"Move history: {self.move_history} at position {self.current_move_index}"
        )
        self.update_buttons()

    def check_opponent_move(self) -> None:
        board = self.board_widget._board
        if board.is_game_over():
            print("Game over!")
            return

        if board.turn != self.player_color:
            QTimer.singleShot(500, self.make_opponent_move)

    def make_opponent_move(self) -> None:
        # Ensure we are still at the last position before making a move
        if not self.is_at_last_move():
            return

        board = self.board_widget._board
        if board.turn == self.player_color:
            return

        legal_moves = list(board.legal_moves)
        if legal_moves:
            random_move = random.choice(legal_moves)
            print(f"Opponent plays: {random_move}")
            self.board_widget.play_move(random_move, animate=True)

    def is_at_last_move(self) -> bool:
        return self.current_move_index == len(self.move_history)

    def is_at_first_move(self) -> bool:
        return self.current_move_index == 0

    def update_buttons(self) -> None:
        has_prev = not self.is_at_first_move()
        has_next = not self.is_at_last_move()

        self.btn_first.setEnabled(has_prev)
        self.btn_prev.setEnabled(has_prev)
        self.btn_next.setEnabled(has_next)
        self.btn_last.setEnabled(has_next)

    def go_first(self) -> None:
        while not self.is_at_first_move():
            self.board_widget.undo_move(animate=False)

    def go_prev(self) -> None:
        if not self.is_at_first_move():
            self.board_widget.undo_move(animate=True)

    def go_next(self) -> None:
        if not self.is_at_last_move():
            move = self.move_history[self.current_move_index]
            self.board_widget.play_move(move, animate=True)

    def go_last(self) -> None:
        while not self.is_at_last_move():
            move = self.move_history[self.current_move_index]
            self.board_widget.play_move(move, animate=False)


if __name__ == "__main__":
    # Enable Ctrl-C to close the application
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

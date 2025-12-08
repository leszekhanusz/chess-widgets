import os
import random
import signal
import sys
from typing import Any, Dict

import chess
import chess.pgn
from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QCursor, QFont, QFontDatabase, QResizeEvent, QWheelEvent
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from chess_widgets import AnalysisBoardWidget, BoardWidget


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

        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left container for Board
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setSpacing(0)
        left_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addWidget(left_container, stretch=1)

        # Right container for controls and moves
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setSpacing(0)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_container.setFixedWidth(300)

        main_layout.addWidget(right_container, stretch=0)

        # Board
        self.board_widget = BoardWidget()
        self.board_widget.move_played.connect(self.on_move_played)
        self.board_widget.move_undone.connect(self.on_move_undone)

        left_layout.addWidget(self.board_widget)

        # Stylesheet for buttons
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

        # Flip board button
        flip_widget = self._make_flip_board_button(button_style)
        right_layout.addWidget(flip_widget)

        # Analysis widget
        self.analysis_widget = self._make_analysis_widget()
        right_layout.addWidget(self.analysis_widget)

        # Navigation buttons bar
        nav_widget = self._make_nav_widget(button_style)
        right_layout.addWidget(nav_widget)

        # Create hover preview board (initially hidden)
        self.hover_preview = BoardWidget()
        self.hover_preview.setParent(self)
        self.hover_preview.setFixedSize(120, 120)
        self.hover_preview.hide()
        self.hover_preview.setWindowFlags(
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint
        )
        self.hover_preview.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Disable interaction on preview board
        self.hover_preview.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Initialize attributes
        self.flipped = False
        self.player_color = chess.WHITE

        self.game = chess.pgn.Game()
        self.current_node: chess.pgn.GameNode = self.game

        self.update_buttons()

    def _make_analysis_widget(self) -> AnalysisBoardWidget:
        analysis_widget = AnalysisBoardWidget()

        # Give it a minimum width and let it expand
        """
        analysis_widget.setMinimumWidth(300)
        analysis_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        """

        analysis_widget.move_clicked.connect(self.on_analysis_move_clicked)
        analysis_widget.move_hovered.connect(self.on_analysis_move_hovered)

        return analysis_widget

    def _make_flip_board_button(self, button_style: str) -> QWidget:
        # Flip button at the top
        flip_widget = QWidget()
        flip_widget.setFixedHeight(50)  # Same height as nav bar
        flip_layout = QHBoxLayout(flip_widget)
        flip_layout.setContentsMargins(0, 0, 0, 10)
        flip_layout.setSpacing(0)

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

        return flip_widget

    def _make_nav_widget(self, button_style: str) -> QWidget:
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

        return nav_widget

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Maintain aspect ratio to keep board square and fill horizontal space."""
        super().resizeEvent(event)
        # Calculate the required width based on height
        # Width includes the board + 300px for the right column
        height = self.height()

        required_height = max(height, 300)
        required_width = required_height + 300

        # Adjust width if needed (tolerance to avoid infinite loops)
        if abs(self.width() - required_width) > 2:
            self.resize(int(required_width), required_height)

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

        if interactive:
            # If interactive move, we need to handle branching or overwriting
            # For this simple demo, we'll append to current node
            # Create a new node
            new_node = self.current_node.add_variation(move)
            self.current_node = new_node

            # Sync to analysis widget
            # We call set_game to refresh the whole view for simplicity
            # when structure changes
            self.analysis_widget.set_game(self.game)
            self.analysis_widget.set_active_node(self.current_node)

        # For programmatic moves (replay), we don't assume we are creating
        # new nodes immediately unless handling a replay loop. But here 'move_played'
        # usually comes from BoardWidget which only plays what we tell it
        # or what user does.
        # If it's replay (go_next), we just update state.

        # Actually go_next calls board_widget.play_move(animate=True).
        # So it triggers this signal.
        # But we only want to ADD to PGN if it was INTERACTIVE.
        # If it wasn't interactive, we assume we are just traversing
        # the existing game tree.

        self.check_opponent_move()
        self.update_buttons()

    def on_analysis_move_clicked(self, node: chess.pgn.ChildNode) -> None:
        """Handle click on move in analysis widget."""
        # Update board to this position
        self.board_widget.set_board(node.board())
        self.current_node = node
        self.analysis_widget.set_active_node(node)
        self.update_buttons()
        # Also need to check if we should trigger opponent move? Maybe not on review.

        self.update_buttons()

    def on_analysis_move_hovered(self, node: chess.pgn.ChildNode | None) -> None:
        """Handle hover on move in analysis widget."""
        if node is None:
            self.hover_preview.hide()
        else:
            # Update preview board with the position after this move
            self.hover_preview.set_board(node.board())

            # Position the preview near the cursor
            cursor_pos = QCursor.pos()
            # Offset to the right and down a bit so it doesn't obscure the move
            preview_pos = cursor_pos + QPoint(15, 15)
            self.hover_preview.move(self.mapFromGlobal(preview_pos))
            self.hover_preview.show()
            self.hover_preview.raise_()

    def on_move_undone(self, move: chess.Move) -> None:
        print(f"Move undone: {move}")
        # Move up the tree
        if self.current_node.parent:
            self.current_node = self.current_node.parent
            self.analysis_widget.set_active_node(self.current_node)

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

            # Manually update PGN and analysis board
            new_node = self.current_node.add_variation(random_move)
            self.current_node = new_node

            self.analysis_widget.set_game(self.game)
            self.analysis_widget.set_active_node(self.current_node)
            self.update_buttons()

    def is_at_last_move(self) -> bool:
        return len(self.current_node.variations) == 0

    def is_at_first_move(self) -> bool:
        return self.current_node.parent is None

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
            # Get next move from current node
            # Default to main variation
            next_node = self.current_node.variations[0]
            move = next_node.move
            # Play move WITHOUT triggering interactive logic, but animating
            self.board_widget.play_move(move, animate=True, interactive=False)
            self.current_node = next_node
            self.analysis_widget.set_active_node(self.current_node)

    def go_last(self) -> None:
        while not self.is_at_last_move():
            # Optimization: just set board to final position if too long?
            # For now, step through
            self.go_next()  # Helper that plays one move
            # To make it fast/instant without animation:
            # next_node = self.current_node.variations[0]
            # self.current_node = next_node
            # self.board_widget.play_move(next_node.move, animate=False)
            # self.analysis_widget.set_active_node(self.current_node)


if __name__ == "__main__":
    # Enable Ctrl-C to close the application
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

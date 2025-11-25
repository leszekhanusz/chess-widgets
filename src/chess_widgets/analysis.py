from typing import Optional, cast

import chess
import chess.pgn
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QMouseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from chess_widgets.flow_layout import FlowLayout

# Styling constants based on Lichess light mode
COLOR_BG = "#FFFFFF"
COLOR_BG_ROW = "#FFFFFF"
COLOR_BG_ROW_HOVER = "#E8F2FF"  # Light blueish hover
COLOR_TEXT = "#333333"
COLOR_TEXT_DIM = "#888888"
COLOR_TEXT_NUMBER = "#A0A0A0"
COLOR_HIGHLIGHT = "#1b78d0"
COLOR_BORDER = "#E0E0E0"
COLOR_VARIATION_BAR = "#E0E0E0"

STYLE_SCROLL_AREA = f"""
    QScrollArea {{
        background-color: {COLOR_BG};
        border: none;
    }}
    QWidget {{
        background-color: {COLOR_BG};
        color: {COLOR_TEXT};
        font-family: "Noto Sans", Sans-Serif;
        font-size: 14px;
    }}
"""

STYLE_MOVE_ROW = f"""
    .MoveRowWidget {{
        background-color: {COLOR_BG};
    }}
    .MoveRowWidget:hover {{
        background-color: {COLOR_BG_ROW_HOVER};
    }}
    QLabel {{
        padding: 2px 5px;
    }}
"""

STYLE_MOVE_LABEL = f"""
    QLabel {{
        color: {COLOR_TEXT};
        padding: 2px 4px;
        border-radius: 3px;
    }}
    QLabel:hover {{
        background-color: {COLOR_BG_ROW_HOVER};
        color: #ffffff;
    }}
"""

STYLE_MOVE_NUMBER = f"""
    color: {COLOR_TEXT_NUMBER};
    background-color: #F0F0F0;
    border-right: 1px solid {COLOR_BORDER};
"""

STYLE_ANNOTATION = f"""
    color: {COLOR_TEXT};
    background-color: {COLOR_BG_ROW};
    padding: 4px 8px;
    font-style: italic;
"""


class ClickableLabel(QLabel):
    clicked = Signal(object)  # Emits the node

    def __init__(
        self, text: str, node: chess.pgn.ChildNode, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(text, parent)
        self.node = node
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(STYLE_MOVE_LABEL)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.clicked.emit(self.node)


class MoveRowWidget(QFrame):
    move_clicked = Signal(object)

    def __init__(
        self,
        number_text: str,
        white_node: Optional[chess.pgn.ChildNode] = None,
        black_node: Optional[chess.pgn.ChildNode] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.white_node = white_node
        self.black_node = black_node

        self.setLayout(QHBoxLayout())
        layout = cast(QHBoxLayout, self.layout())
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Move Number (13%)
        self.lbl_number = QLabel(number_text)
        self.lbl_number.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_number.setStyleSheet(STYLE_MOVE_NUMBER)
        # self.lbl_number.setFixedWidth(50)

        layout.addWidget(self.lbl_number, 13)

        # White Move (43.5%)
        self.lbl_white: QLabel
        if white_node:
            self.lbl_white = ClickableLabel(white_node.san(), white_node)
            self.lbl_white.clicked.connect(self.move_clicked.emit)
        else:
            self.lbl_white = QLabel("...")
            self.lbl_white.setStyleSheet(f"color: {COLOR_TEXT_DIM}; padding: 2px 5px;")
        self.lbl_white.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        layout.addWidget(self.lbl_white, 43)

        # Separator
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.VLine)
        line1.setStyleSheet(f"color: {COLOR_BORDER};")
        layout.addWidget(line1)

        # Black Move (43.5%)
        self.lbl_black: QLabel
        if black_node:
            self.lbl_black = ClickableLabel(black_node.san(), black_node)
            self.lbl_black.clicked.connect(self.move_clicked.emit)
        else:
            self.lbl_black = QLabel("")
        self.lbl_black.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        layout.addWidget(self.lbl_black, 43)

        # Styling
        self.setStyleSheet(
            f"""
            MoveRowWidget {{
                border-bottom: 1px solid {COLOR_BORDER};
            }}
        """
        )

    def set_black_move(self, node: chess.pgn.ChildNode) -> None:
        # Replace the placeholder black label
        layout = cast(QHBoxLayout, self.layout())
        layout.removeWidget(self.lbl_black)
        self.lbl_black.deleteLater()

        self.black_node = node
        self.lbl_black = ClickableLabel(node.san(), node)
        self.lbl_black.clicked.connect(self.move_clicked.emit)
        layout.addWidget(self.lbl_black, 43)


class InlineMovesWidget(QWidget):
    move_clicked = Signal(object)

    def __init__(
        self, start_node: chess.pgn.ChildNode, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)

        # Indentation line
        self.indent_bar = QFrame(self)
        self.indent_bar.setStyleSheet(
            f"background-color: {COLOR_VARIATION_BAR}; width: 2px;"
        )
        self.indent_bar.setFixedWidth(2)

        # Container for flow content
        self.content_widget = QWidget()
        self.content_layout = FlowLayout(
            self.content_widget, margin=4, h_spacing=4, v_spacing=2
        )

        # Main layout: Indent Bar + Content
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)
        self.main_layout.addWidget(self.indent_bar)
        self.main_layout.addWidget(self.content_widget, 1)

        self.populate(start_node)

    def populate(self, node: chess.pgn.ChildNode) -> None:
        current: chess.pgn.ChildNode = node
        while current:
            # Add move
            move_text = current.san()
            if current.parent and current.parent.board().turn == chess.WHITE:
                move_text = f"{current.parent.board().fullmove_number}. {move_text}"
            else:
                move_text = f"{current.parent.board().fullmove_number}... {move_text}"

            lbl = ClickableLabel(move_text, current)
            lbl.clicked.connect(self.move_clicked.emit)
            lbl.setStyleSheet(
                f"""
                QLabel {{
                    color: {COLOR_TEXT};
                    background-color: transparent;
                    border-radius: 3px;
                    padding: 1px 3px;
                }}
                QLabel:hover {{
                    background-color: {COLOR_BG_ROW_HOVER};
                }}
            """
            )
            self.content_layout.addWidget(lbl)

            # Add comment if any
            if current.comment:
                comment_lbl = QLabel(current.comment)
                comment_lbl.setWordWrap(True)
                comment_lbl.setStyleSheet(
                    f"color: {COLOR_TEXT_DIM}; font-style: italic;"
                )
                self.content_layout.addWidget(comment_lbl)

            # Handle nested variations (simple recursion for now)
            if len(current.variations) > 1:
                for variation in current.variations[1:]:
                    # For inline, we usually wrap in parens
                    paren_start = QLabel("(")
                    paren_start.setStyleSheet(f"color: {COLOR_TEXT_DIM};")
                    self.content_layout.addWidget(paren_start)

                    # Recursive inline widget? Or just flatten?
                    # Flattening is easier for FlowLayout
                    self.populate_inline(variation)

                    paren_end = QLabel(")")
                    paren_end.setStyleSheet(f"color: {COLOR_TEXT_DIM};")
                    self.content_layout.addWidget(paren_end)

            if current.variations:
                current = current.variations[0]
            else:
                current = None  # type: ignore

    def populate_inline(self, node: chess.pgn.ChildNode) -> None:
        # Helper to add moves to the SAME layout for nested variations
        current: chess.pgn.ChildNode = node
        while current:
            move_text = current.san()
            if current.parent and current.parent.board().turn == chess.WHITE:
                move_text = f"{current.parent.board().fullmove_number}. {move_text}"
            else:
                move_text = f"{current.parent.board().fullmove_number}... {move_text}"

            lbl = ClickableLabel(move_text, current)
            lbl.clicked.connect(self.move_clicked.emit)
            lbl.setStyleSheet(
                f"color: {COLOR_TEXT_DIM};"
            )  # Nested variations often dimmer
            self.content_layout.addWidget(lbl)

            if current.variations:
                current = current.variations[0]
            else:
                current = None  # type: ignore


class AnalysisBoardWidget(QScrollArea):
    move_clicked = Signal(object)

    def __init__(
        self, game: Optional[chess.pgn.Game] = None, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(STYLE_SCROLL_AREA)

        self.container = QWidget()
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setWidget(self.container)

        if game:
            self.process_game(game)

    def process_game(self, game: chess.pgn.Game) -> None:
        # Add initial comment if any
        if game.comment:
            self.add_annotation(game.comment)

        current_node: chess.pgn.ChildNode = game  # type: ignore
        current_row_widget: Optional[MoveRowWidget] = None

        while current_node.variations:
            main_next = current_node.variations[0]
            variations = current_node.variations[1:]

            is_white = current_node.board().turn == chess.WHITE
            move_number = current_node.board().fullmove_number

            # Handle Variations (Alternatives to main_next)
            # Variations are usually displayed AFTER the move they branch from.
            # But here they branch from `current_node`.

            if variations:
                # If it's Black's turn (played White), variations for Black...
                # The variations should appear after the White move.
                pass

            if is_white:
                # Start new row
                current_row_widget = MoveRowWidget(
                    str(move_number), white_node=main_next
                )
                current_row_widget.move_clicked.connect(self.move_clicked.emit)
                self.main_layout.addWidget(current_row_widget)

                # If there are variations for this White move (siblings of main_next)
                if variations:
                    # Add them as InlineMovesWidget
                    for var_node in variations:
                        var_widget = InlineMovesWidget(var_node)
                        var_widget.move_clicked.connect(self.move_clicked.emit)
                        self.main_layout.addWidget(var_widget)

                # If comment
                if main_next.comment:
                    self.add_annotation(main_next.comment)
                    # Close row because annotation breaks flow
                    current_row_widget = None

            else:  # Black's turn
                # Try to append to existing row
                if current_row_widget and current_row_widget.black_node is None:
                    current_row_widget.set_black_move(main_next)
                else:
                    # Create new row with empty white
                    current_row_widget = MoveRowWidget(
                        str(move_number), white_node=None, black_node=main_next
                    )
                    current_row_widget.move_clicked.connect(self.move_clicked.emit)
                    self.main_layout.addWidget(current_row_widget)

                # If there are variations for this Black move
                if variations:
                    for var_node in variations:
                        var_widget = InlineMovesWidget(var_node)
                        var_widget.move_clicked.connect(self.move_clicked.emit)
                        self.main_layout.addWidget(var_widget)

                # If comment
                if main_next.comment:
                    self.add_annotation(main_next.comment)
                    current_row_widget = None

            current_node = main_next

    def add_annotation(self, text: str) -> None:
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(STYLE_ANNOTATION)
        self.main_layout.addWidget(lbl)

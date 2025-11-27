import re
from typing import Optional, cast

import chess
import chess.pgn
from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QCursor, QEnterEvent, QKeyEvent, QMouseEvent, QResizeEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QScrollBar,
    QVBoxLayout,
    QWidget,
)

from chess_widgets.flow_layout import FlowLayout

# Styling constants based on Lichess light mode
COLOR_BG = "#F7F6F5"
COLOR_BG_ROW = "#FFFFFF"
COLOR_BG_ROW_HOVER = "#E4E4E4"
COLOR_TEXT = "#4D4D4D"
COLOR_TEXT_DIM = "#888888"
COLOR_TEXT_NUMBER = "#A0A0A0"
COLOR_HIGHLIGHT = "#1b78d0"
# COLOR_BORDER_LIGHT = "#4D4D4D1F"
COLOR_BORDER_LIGHT = "#E2E1E0"
COLOR_BORDER = "#D9D9D9"
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
        font-size: 13px;
    }}
    /* Scrollbar styling - initially invisible */
    QScrollBar:vertical {{
        background-color: transparent;
        width: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background-color: transparent;
        border-radius: 4px;
        min-height: 50px;
    }}
    QScrollBar::add-line:vertical {{
        height: 0px;
    }}
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
"""

STYLE_MOVE_ROW = f"""
    QFrame{{
        background-color: {COLOR_BG_ROW};
        font-family: "Noto Sans", sans-serif;
    }}
"""

STYLE_MOVE_LABEL = f"""
    QLabel {{
        color: {COLOR_TEXT};
        padding: 4px 4px;
        border-radius: 3px;
        font-size: 15px;
    }}
    QLabel:hover {{
        background-color: {COLOR_BG_ROW_HOVER};
        color: #1F1F1F;
    }}
"""

STYLE_MOVE_NUMBER = f"""
    color: {COLOR_TEXT_NUMBER};
    background-color: #F0F0F0;
    border-right: 1px solid {COLOR_BORDER};
    padding: 4px 0px;
"""

STYLE_ANNOTATION = f"""
    color: {COLOR_TEXT};
    background-color: {COLOR_BG};
    padding: 1px 1px;
    border-bottom: 1px solid {COLOR_BORDER_LIGHT};
    border-top: 1px solid {COLOR_BORDER_LIGHT};
"""


STYLE_MOVE_LABEL_ACTIVE = """
    QLabel {
        background-color: #3d8cd7 !important;
        color: #ffffff !important;
    }
    QLabel:hover {
        background-color: #3d8cd7 !important;
        color: #ffffff !important;
    }
"""


def _filter_comment(text: str) -> str:
    """Remove [%...] annotations from comment text."""
    # Remove [%...] blocks
    text = re.sub(r"\[%[^]]+\]", "", text)
    # Trim whitespace from the beginning and end
    text = text.strip()
    return text


class MoveLabel(QLabel):
    clicked = Signal(object)  # Emits the node

    def __init__(
        self,
        text: str,
        node: chess.pgn.ChildNode,
        base_style: str,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(text, parent)
        self.node = node
        self.base_style = base_style
        self.is_active = False
        self.setStyleSheet(self.base_style)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self.is_active:
            self.clicked.emit(self.node)

    def set_active(self, active: bool) -> None:
        self.is_active = active
        if active:
            # Append active style to base style (or replace relevant parts)
            # Using a simple concatenation or specific override
            # We need to ensure the active style overrides the base style properties
            # The simplest way is to append the active style string
            self.setStyleSheet(self.base_style + STYLE_MOVE_LABEL_ACTIVE)
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        else:
            self.setStyleSheet(self.base_style)
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))


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
            self.lbl_white = MoveLabel(white_node.san(), white_node, STYLE_MOVE_LABEL)
            self.lbl_white.clicked.connect(self.move_clicked.emit)
        else:
            self.lbl_white = QLabel("...")
            self.lbl_white.setStyleSheet(f"color: {COLOR_TEXT_DIM}; padding: 2px 5px;")
        self.lbl_white.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        layout.addWidget(self.lbl_white, 43)

        # Black Move (43.5%)
        self.lbl_black: QLabel
        if black_node:
            self.lbl_black = MoveLabel(black_node.san(), black_node, STYLE_MOVE_LABEL)
            self.lbl_black.clicked.connect(self.move_clicked.emit)
        else:
            self.lbl_black = QLabel("...")
            self.lbl_black.setStyleSheet(f"color: {COLOR_TEXT_DIM}; padding: 2px 5px;")
        self.lbl_black.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        layout.addWidget(self.lbl_black, 43)

        # Styling
        self.setStyleSheet(STYLE_MOVE_ROW)

    def set_black_move(self, node: chess.pgn.ChildNode) -> None:
        # Replace the placeholder black label
        layout = cast(QHBoxLayout, self.layout())
        layout.removeWidget(self.lbl_black)
        self.lbl_black.deleteLater()

        self.black_node = node
        self.lbl_black = MoveLabel(node.san(), node, STYLE_MOVE_LABEL)
        self.lbl_black.clicked.connect(self.move_clicked.emit)
        layout.addWidget(self.lbl_black, 43)

    def get_move_labels(self) -> list[MoveLabel]:
        labels = []
        if isinstance(self.lbl_white, MoveLabel):
            labels.append(self.lbl_white)
        if isinstance(self.lbl_black, MoveLabel):
            labels.append(self.lbl_black)
        return labels


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
        current: Optional[chess.pgn.ChildNode] = node
        while current:
            # Add move
            move_text = current.san()
            if current.parent and current.parent.board().turn == chess.WHITE:
                move_text = f"{current.parent.board().fullmove_number}. {move_text}"
            else:
                move_number = (
                    str(current.parent.board().fullmove_number) + "... "
                    if node is current
                    else ""
                )
                move_text = f"{move_number}{move_text}"

            lbl = MoveLabel(
                move_text,
                current,
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
            """,
            )
            lbl.clicked.connect(self.move_clicked.emit)
            self.content_layout.addWidget(lbl)

            # Add comment if any
            if current.comment:
                filtered_comment = _filter_comment(current.comment)
                if filtered_comment:
                    comment_lbl = QLabel(filtered_comment)
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
                current = None

    def populate_inline(self, node: chess.pgn.ChildNode) -> None:
        # Helper to add moves to the SAME layout for nested variations
        current: Optional[chess.pgn.ChildNode] = node
        while current:
            move_text = current.san()
            if current.parent and current.parent.board().turn == chess.WHITE:
                move_text = f"{current.parent.board().fullmove_number}. {move_text}"
            else:
                move_number = (
                    str(current.parent.board().fullmove_number) + "... "
                    if node is current
                    else ""
                )
                move_text = f"{move_number}{move_text}"

            lbl = MoveLabel(
                move_text,
                current,
                f"""
                QLabel {{
                    color: {COLOR_TEXT_DIM};
                    background-color: transparent;
                    border-radius: 3px;
                }}
                QLabel:hover {{
                    background-color: {COLOR_BG_ROW_HOVER};
                }}
                """,
            )
            lbl.clicked.connect(self.move_clicked.emit)
            self.content_layout.addWidget(lbl)

            if current.variations:
                current = current.variations[0]
            else:
                current = None

    def get_move_labels(self) -> list[MoveLabel]:
        labels = []
        # Iterate over the layout items to find MoveLabels
        for child in self.content_widget.children():
            if isinstance(child, MoveLabel):
                labels.append(child)
        return labels


class AnalysisBoardWidget(QScrollArea):
    move_clicked = Signal(object)

    def __init__(
        self, game: Optional[chess.pgn.Game] = None, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Make the frame focusable
        self.setFocusPolicy(Qt.StrongFocus)

        # Track hover state for scrollbar visibility
        self.is_hovered = False
        self.scrollbar_hovered = False

        # Create overlay scrollbar
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.overlay_scrollbar = QScrollBar(Qt.Orientation.Vertical, self)
        self.overlay_scrollbar.hide()

        # Sync overlay scrollbar with native scrollbar
        native_sb = self.verticalScrollBar()
        native_sb.valueChanged.connect(self.overlay_scrollbar.setValue)
        native_sb.rangeChanged.connect(self.overlay_scrollbar.setRange)
        self.overlay_scrollbar.valueChanged.connect(native_sb.setValue)

        # Initial state sync
        self.overlay_scrollbar.setRange(native_sb.minimum(), native_sb.maximum())
        self.overlay_scrollbar.setValue(native_sb.value())

        # Install event filter on overlay scrollbar to detect hover
        self.overlay_scrollbar.installEventFilter(self)

        self.container = QWidget()
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setWidget(self.container)

        # Track active node and node-to-label mapping
        self.active_node: Optional[chess.pgn.ChildNode] = None
        self.node_to_label: dict[chess.pgn.ChildNode, MoveLabel] = {}

        # Initialize style
        self.setStyleSheet(STYLE_SCROLL_AREA)
        self._update_scrollbar_style()

        if game:
            self.process_game(game)

    def process_game(self, game: chess.pgn.Game) -> None:
        # Add initial comment if any
        if game.comment:
            filtered_comment = _filter_comment(game.comment)
            if filtered_comment:
                self.add_annotation(filtered_comment)

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
                # Register move labels
                for lbl in current_row_widget.get_move_labels():
                    self.node_to_label[lbl.node] = lbl

                # If there are variations for this White move (siblings of main_next)
                if variations:
                    # Add them as InlineMovesWidget
                    for var_node in variations:
                        var_widget = InlineMovesWidget(var_node)
                        var_widget.move_clicked.connect(self.move_clicked.emit)
                        self.main_layout.addWidget(var_widget)
                        # Register move labels
                        for lbl in var_widget.get_move_labels():
                            self.node_to_label[lbl.node] = lbl

                # If comment
                if main_next.comment:
                    filtered_comment = _filter_comment(main_next.comment)
                    if filtered_comment:
                        self.add_annotation(filtered_comment)
                        # Close row because annotation breaks flow
                        current_row_widget = None

            else:  # Black's turn
                # Try to append to existing row
                if current_row_widget and current_row_widget.black_node is None:
                    current_row_widget.set_black_move(main_next)
                    # Register the newly added black move label
                    for lbl in current_row_widget.get_move_labels():
                        if lbl.node == main_next:
                            self.node_to_label[lbl.node] = lbl
                else:
                    # Create new row with empty white
                    current_row_widget = MoveRowWidget(
                        str(move_number), white_node=None, black_node=main_next
                    )
                    current_row_widget.move_clicked.connect(self.move_clicked.emit)
                    self.main_layout.addWidget(current_row_widget)
                    # Register move labels
                    for lbl in current_row_widget.get_move_labels():
                        self.node_to_label[lbl.node] = lbl

                # If there are variations for this Black move
                if variations:
                    for var_node in variations:
                        var_widget = InlineMovesWidget(var_node)
                        var_widget.move_clicked.connect(self.move_clicked.emit)
                        self.main_layout.addWidget(var_widget)
                        # Register move labels
                        for lbl in var_widget.get_move_labels():
                            self.node_to_label[lbl.node] = lbl

                # If comment
                if main_next.comment:
                    filtered_comment = _filter_comment(main_next.comment)
                    if filtered_comment:
                        self.add_annotation(filtered_comment)
                        current_row_widget = None

            current_node = main_next

    def add_annotation(self, text: str) -> None:
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(STYLE_ANNOTATION)
        self.main_layout.addWidget(lbl)

    def set_active_node(self, node: chess.pgn.ChildNode) -> None:
        """Set the active node and update the visual highlighting."""
        # Deactivate previous active node
        if self.active_node and self.active_node in self.node_to_label:
            self.node_to_label[self.active_node].set_active(False)

        # Activate new node
        if node in self.node_to_label:
            label = self.node_to_label[node]
            label.set_active(True)
            self.active_node = node

            # Scroll to center the active label
            # Calculate label's center Y relative to the container
            label_pos = label.mapTo(self.container, label.rect().center())
            label_y = label_pos.y()

            # Calculate viewport height
            viewport_height = self.viewport().height()

            # Calculate target scroll position (top of viewport)
            target_scroll = label_y - viewport_height // 2

            # Clamp and set scrollbar value
            scrollbar = self.verticalScrollBar()
            target_scroll = max(
                scrollbar.minimum(), min(target_scroll, scrollbar.maximum())
            )
            scrollbar.setValue(target_scroll)

    def prev_move(self) -> None:
        if self.active_node and self.active_node.parent:
            self.set_active_node(self.active_node.parent)

    def next_move(self) -> None:
        if self.active_node and len(self.active_node.variations) > 0:
            self.set_active_node(self.active_node.variations[0])

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Left:
            self.prev_move()
        elif event.key() == Qt.Key_Right:
            self.next_move()
        else:
            # Pass other keys to the base class
            super().keyPressEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Position the overlay scrollbar."""
        super().resizeEvent(event)
        if hasattr(self, "overlay_scrollbar"):
            sb_width = 12  # Max width
            self.overlay_scrollbar.setGeometry(
                self.width() - sb_width, 0, sb_width, self.height()
            )

    def enterEvent(self, event: QEnterEvent) -> None:
        """Show scrollbar when mouse enters the widget."""
        self.is_hovered = True
        self._update_scrollbar_style()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        """Hide scrollbar when mouse leaves the widget."""
        self.is_hovered = False
        self.scrollbar_hovered = False
        self._update_scrollbar_style()
        super().leaveEvent(event)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Track hover state on the scrollbar itself."""
        if hasattr(self, "overlay_scrollbar") and obj == self.overlay_scrollbar:
            if event.type() == QEvent.Type.Enter:
                self.scrollbar_hovered = True
                self._update_scrollbar_style()
            elif event.type() == QEvent.Type.Leave:
                self.scrollbar_hovered = False
                self._update_scrollbar_style()
        return bool(super().eventFilter(obj, event))

    def _update_scrollbar_style(self) -> None:
        """Update scrollbar appearance based on hover state."""
        if not hasattr(self, "overlay_scrollbar"):
            return

        # Determine visibility and style
        if self.scrollbar_hovered:
            # Full width handle when hovering scrollbar
            handle_margin = 0
            handle_width = 12
            color = "rgba(128, 128, 128, 0.6)"
            self.overlay_scrollbar.show()
        elif self.is_hovered:
            # Thinner handle (via margins) when hovering widget
            handle_margin = 2  # (12 - 8) / 2
            handle_width = 8
            color = "rgba(128, 128, 128, 0.4)"
            self.overlay_scrollbar.show()
        else:
            # Invisible
            handle_margin = 2
            handle_width = 8
            color = "transparent"
            self.overlay_scrollbar.hide()

        self.overlay_scrollbar.setStyleSheet(
            f"""
            QScrollBar:vertical {{
                background-color: transparent;
                width: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {color};
                border-radius: {handle_width // 2}px;
                min-height: 50px;
                margin: 0px {handle_margin}px 0px {handle_margin}px;
            }}
            QScrollBar::add-line:vertical {{
                height: 0px;
            }}
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """
        )

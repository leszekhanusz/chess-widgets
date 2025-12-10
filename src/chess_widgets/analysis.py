import re
from typing import Optional, cast

import chess
import chess.pgn
from PySide6.QtCore import QEvent, QObject, QRect, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QCursor,
    QEnterEvent,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPen,
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QScrollBar,
    QVBoxLayout,
    QWidget,
)
from typing_extensions import Self

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

STYLE_MOVE_LABEL_HOVER = f"""
    QLabel {{
        background-color: {COLOR_BG_ROW_HOVER};
        color: #1F1F1F;
    }}
"""


def _filter_comment(text: str) -> str:
    """Remove [%...] annotations from comment text."""
    # Remove [%...] blocks
    text = re.sub(r"\[%[^]]+\]", "", text)
    # Trim whitespace from the beginning and end
    text = text.strip()
    return text


def _is_linear_branch(node: chess.pgn.GameNode) -> bool:
    """Check if a variation branch is linear (no sub-branching)."""
    current: Optional[chess.pgn.GameNode] = node
    while current:
        if len(current.variations) > 1:
            return False
        if current.variations:
            current = current.variations[0]
        else:
            current = None
    return True


class ExpandButton(QWidget):
    toggled = Signal(bool)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.is_expanded = True
        self.setFixedWidth(12)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Color configuration
        self.color_icon = QColor("#888888")
        self.color_hover = QColor("#4D4D4D")

        self.is_hovered = False

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.is_expanded = not self.is_expanded
        self.toggled.emit(self.is_expanded)
        self.update()

    def enterEvent(self, event: QEnterEvent) -> None:
        self.is_hovered = True
        self.update()

    def leaveEvent(self, event: QEvent) -> None:
        self.is_hovered = False
        self.update()

    def paintEvent(self, event: QEvent) -> None:
        painter = QPainter(self)

        # Set pen icon
        pen_icon = QPen(self.color_hover if self.is_hovered else self.color_icon)
        painter.setPen(pen_icon)

        # Draw icon text
        text = "[−]" if self.is_expanded else "[+]"
        # Center vertically
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)


class MoveLabel(QFrame):
    clicked = Signal(object)  # Emits the node
    hovered = Signal(object)  # Emits the node when hovered, None when unhovered

    def __init__(
        self,
        text: str,
        node: chess.pgn.ChildNode,
        base_style: str,
        parent: Optional[QWidget] = None,
        start_widget: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.node = node
        self.start_widget = start_widget
        self.base_style = base_style
        self.is_active = False
        self.is_hovered = False

        self.content_layout = QHBoxLayout(self)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(2)

        if start_widget:
            self.content_layout.addSpacing(5)
            self.content_layout.addWidget(start_widget)

        self.label = QLabel(text)
        self.content_layout.addWidget(self.label)

        self._update_style()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        # Enable mouse tracking to receive enter/leave events
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def text(self) -> str:
        return str(self.label.text())

    def setText(self, text: str) -> None:
        self.label.setText(text)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self.is_active:
            self.clicked.emit(self.node)

    def enterEvent(self, event: QEnterEvent) -> None:
        """Handle mouse enter - apply hover styling."""
        if not self.is_active:
            self.is_hovered = True
            self._update_style()
            self.hovered.emit(self.node)
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        """Handle mouse leave - remove hover styling."""
        if self.is_hovered:
            self.is_hovered = False
            self._update_style()
            self.hovered.emit(None)
        super().leaveEvent(event)

    def _update_style(self) -> None:
        """Update the stylesheet based on current state."""
        # We need to target QLabel inside the frame for text color/bg
        # The frame itself can also have bg.
        # existing STYLE_MOVE_LABEL targets QLabel.
        # Depending on how complex the styles are, we might need to adjust them.
        # STYLE_MOVE_LABEL = "QLabel { ... }"
        # We want the style to apply to self (QFrame) OR the child label?
        # The visual design was a label with padding.
        # If we use QFrame, we should apply the style to the *label* or the *frame*?
        # If we act as a container, the hover effect should probably be on
        # the text label? BUT the user wants "MoveRowWidget and MoveLabel to
        # stay generic". If we put ExpandButton INSIDE MoveLabel, should the
        # button highlight when MoveLabel hovers? Usually checking [move] ->
        # highlights move. Clicking [+] -> expands/collapses.
        # The [+] should probably NOT trigger the move click.
        # ExpandButton handles its own click.

        # Let's apply the style to the inner QLabel to match previous behavior
        # But wait, previous behavior was `self.setStyleSheet`. `MoveLabel` IS a
        # `QLabel`. Now `MoveLabel` IS a `QFrame`.
        # If we apply `QLabel { ... }` to `QFrame`, it cascades to children `QLabel`.

        style = self.base_style
        if self.is_active:
            style += STYLE_MOVE_LABEL_ACTIVE
        elif self.is_hovered:
            style += STYLE_MOVE_LABEL_HOVER

        # The styles assume "QLabel".
        # Example:
        # STYLE_MOVE_LABEL_HOVER = "QLabel { background-color: ... }"
        # This will work fine applied to the QFrame parent, affecting the child QLabel.
        self.setStyleSheet(style)

    def set_active(self, active: bool) -> None:
        self.is_active = active
        if active:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._update_style()


class MoveRowWidget(QFrame):
    move_clicked = Signal(object)

    def __init__(
        self,
        number_text: str,
        white_node: Optional[chess.pgn.ChildNode] = None,
        black_node: Optional[chess.pgn.ChildNode] = None,
        parent: Optional[QWidget] = None,
        start_widget_white: Optional[QWidget] = None,
        start_widget_black: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.white_node = white_node
        self.black_node = black_node

        # Reference to another row for the black move
        # if the white and black moves are split
        self.black_split_row: Optional[Self] = None

        self.setLayout(QHBoxLayout())
        layout = cast(QHBoxLayout, self.layout())
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Move Number (13%)
        self.lbl_number = QLabel(number_text)
        self.lbl_number.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_number.setStyleSheet(STYLE_MOVE_NUMBER)

        layout.addWidget(self.lbl_number, stretch=13)

        # White Move (43.5%)
        self.lbl_white: QWidget  # Can be MoveLabel (QFrame) or QLabel

        if white_node:
            self.lbl_white = MoveLabel(
                white_node.san(),
                white_node,
                STYLE_MOVE_LABEL,
                start_widget=start_widget_white,
            )
            self.lbl_white.clicked.connect(self.move_clicked.emit)
        else:
            self.lbl_white = self._make_placeholder()

        layout.addWidget(self.lbl_white, stretch=43)

        # Black Move (43.5%)
        self.lbl_black: QWidget

        if black_node:
            self.lbl_black = MoveLabel(
                black_node.san(),
                black_node,
                STYLE_MOVE_LABEL,
                start_widget=start_widget_black,
            )
            self.lbl_black.clicked.connect(self.move_clicked.emit)
        else:
            self.lbl_black = self._make_placeholder()

        layout.addWidget(self.lbl_black, stretch=43)

        # Styling
        self.setStyleSheet(STYLE_MOVE_ROW)

    def _make_placeholder(self) -> QLabel:
        lbl = QLabel("...")
        lbl.setStyleSheet(f"color: {COLOR_TEXT_DIM}; padding: 2px 5px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return lbl

    def show_black_split_row(self, is_split: bool) -> None:
        assert self.black_split_row is not None

        self.black_split_row.setVisible(is_split)

        layout = cast(QHBoxLayout, self.layout())
        layout.removeWidget(self.lbl_black)

        if is_split:
            black_layout = cast(QHBoxLayout, self.black_split_row.layout())
            black_layout.addWidget(self.lbl_black, stretch=43)
            self.lbl_black = self._make_placeholder()
        else:
            self.black_node = self.black_split_row.black_node
            self.lbl_black.deleteLater()
            self.lbl_black = self.black_split_row.lbl_black

        layout.addWidget(self.lbl_black, stretch=43)

    def set_black_move(
        self, node: chess.pgn.ChildNode, start_widget: Optional[QWidget] = None
    ) -> None:
        # Replace the placeholder black label
        layout = cast(QHBoxLayout, self.layout())
        layout.removeWidget(self.lbl_black)
        self.lbl_black.deleteLater()

        self.black_node = node
        self.lbl_black = MoveLabel(
            node.san(), node, STYLE_MOVE_LABEL, start_widget=start_widget
        )
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
    # Signal emitted when we hit a complex branching point,
    # passing the node that has the branches
    branch_encountered = Signal(object)

    def __init__(
        self,
        start_node: chess.pgn.ChildNode,
        stop_on_complex_branch: bool = False,
        defer_populate: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.stop_on_complex_branch = stop_on_complex_branch

        # Container for flow content
        self.content_widget = QWidget()
        self.content_layout = FlowLayout(
            self.content_widget, margin=4, h_spacing=4, v_spacing=2
        )

        # Main layout: Indent Bar + Content
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)
        self.main_layout.addWidget(self.content_widget, 1)

        if not defer_populate:
            if self.stop_on_complex_branch:
                self.populate_linear(start_node)
            else:
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

            # Handle siblings of the CURRENT node (alternatives to this move)
            # We only do this if we are not at the start node
            # (start node siblings are handled by parent)
            if (
                current != node
                and current.parent
                and len(current.parent.variations) > 1
            ):
                for variation in current.parent.variations[1:]:
                    paren_start = QLabel("(")
                    paren_start.setStyleSheet(f"color: {COLOR_TEXT_DIM};")
                    self.content_layout.addWidget(paren_start)

                    self.populate_inline(variation)

                    paren_end = QLabel(")")
                    paren_end.setStyleSheet(f"color: {COLOR_TEXT_DIM};")
                    self.content_layout.addWidget(paren_end)

            # Move to next node
            if current.variations:
                current = current.variations[0]
            else:
                current = None

    def populate_linear(self, node: chess.pgn.ChildNode) -> None:
        current: Optional[chess.pgn.ChildNode] = node
        while current:
            # 1. Render the current move
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

            # 2. Render siblings (alternatives to THIS move)
            # We only do this if we are not at the start node
            # (start node siblings handled by parent)
            if (
                current != node
                and current.parent
                and len(current.parent.variations) > 1
            ):
                for variation in current.parent.variations[1:]:
                    paren_start = QLabel("(")
                    paren_start.setStyleSheet(f"color: {COLOR_TEXT_DIM};")
                    self.content_layout.addWidget(paren_start)

                    self.populate_inline(variation)

                    paren_end = QLabel(")")
                    paren_end.setStyleSheet(f"color: {COLOR_TEXT_DIM};")
                    self.content_layout.addWidget(paren_end)

            # 3. Check next moves (continuations) to decide whether to continue or stop
            next_moves = current.variations
            if not next_moves:
                # End of line
                current = None
            elif len(next_moves) == 1:
                # Linear continuation
                current = next_moves[0]
            else:
                # Branching point ( > 1 variations)
                # Heuristic: Simple or Complex?
                # Simple: 2 branches, 2nd one is linear/leaf.
                is_simple = False
                if len(next_moves) == 2:
                    if _is_linear_branch(next_moves[1]):
                        is_simple = True

                if is_simple:
                    # Continue with main line.
                    # The alternative (next_moves[1]) will be rendered in
                    # the NEXT iteration as a sibling of next_moves[0].
                    current = next_moves[0]
                else:
                    # Complex branching: Stop here and emit signal
                    # The parent (VariationBranchWidget) will pick this up
                    self.branch_encountered.emit(current)
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

    def set_collapsed(self, collapsed: bool) -> None:
        """
        If collapsed is True, show only the first move label and hide everything else.
        If collapsed is False, show everything.
        """
        first_move_found = False

        # We iterate over the layout items.
        # FlowLayout items are reachable via count() and itemAt().
        # However, calling child.setVisible() on widgets is usually enough if they
        # are in the layout.

        # Let's iterate over the children of content_widget directly
        for child in self.content_widget.findChildren(
            QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly
        ):
            if isinstance(child, MoveLabel) and not first_move_found:
                # This is the first move
                child.setVisible(True)
                first_move_found = True
            else:
                # Everything else (comments, parens, subsequent moves)
                child.setVisible(not collapsed)


class ExpandWidget(QWidget):
    toggled = Signal(bool)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.is_expanded = True
        self.setFixedWidth(12)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Color configuration
        self.color_icon = QColor("#888888")
        self.color_line = QColor("#E0E0E0")  # Matches COLOR_VARIATION_BAR
        self.color_hover = QColor("#4D4D4D")

        self.is_hovered = False

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.is_expanded = not self.is_expanded
        self.toggled.emit(self.is_expanded)
        self.update()

    def enterEvent(self, event: QEnterEvent) -> None:
        self.is_hovered = True
        self.update()

    def leaveEvent(self, event: QEvent) -> None:
        self.is_hovered = False
        self.update()

    def paintEvent(self, event: QEvent) -> None:
        painter = QPainter(self)

        # Draw vertical line
        icon_height = 28

        if self.is_expanded:
            pen_line = QPen(self.color_line)
            pen_line.setWidth(1)
            painter.setPen(pen_line)

            # Line from bottom of icon to bottom of widget
            line_cx = self.width() // 2
            line_vertical_margin = 4
            line_cy = icon_height + line_vertical_margin
            painter.drawLine(
                line_cx, line_cy, line_cx, self.height() - line_vertical_margin
            )

        # Set pen icon
        pen_icon = QPen(self.color_hover if self.is_hovered else self.color_icon)
        painter.setPen(pen_icon)

        # Draw icon text
        text = "[−]" if self.is_expanded else "[+]"
        painter.drawText(
            QRect(0, 0, self.width(), icon_height), Qt.AlignmentFlag.AlignCenter, text
        )


class VariationBranchWidget(QWidget):
    move_clicked = Signal(object)

    def __init__(
        self,
        start_node: chess.pgn.ChildNode,
        collapsible: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.start_node = start_node
        self.collapsible = collapsible

        # Main Layout: Horizontal for ExpandWidget + Content
        # Content Layout: Vertical for Header + Subtree

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.expand_btn: Optional[ExpandWidget] = None

        if self.collapsible:
            self.expand_btn = ExpandWidget()
            self.expand_btn.toggled.connect(self.on_toggle)
            self.main_layout.addWidget(self.expand_btn)

        # Content container (Vertical)
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        self.main_layout.addWidget(self.content_container, 1)

        # Header (Inline Moves)
        self.header_widget = QWidget()
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(2)
        # Align to top so inline moves stay at the top
        self.header_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.sub_tree: Optional[QWidget] = None  # Will be TreeMovesWidget

        # Inline moves for this linear segment
        self.inline_widget = InlineMovesWidget(
            start_node, stop_on_complex_branch=True, defer_populate=True
        )
        self.inline_widget.move_clicked.connect(self.move_clicked.emit)
        self.inline_widget.branch_encountered.connect(self.on_branch_encountered)

        self.header_layout.addWidget(self.inline_widget)
        self.content_layout.addWidget(self.header_widget)

        # Now populate, so signals can be emitted
        self.inline_widget.populate_linear(start_node)

        # If collapsible, initially collapsed?
        # ExpandWidget defaults to is_expanded=True.
        # So we should be expanded by default. Default is fine.

    def on_branch_encountered(self, node: chess.pgn.ChildNode) -> None:
        # We hit a complex branch at `node`.
        # `node` is the last linear move. `node.variations` has the branches.
        # We need to create a TreeMovesWidget for these variations
        # and add it to our body.

        # Create sub-tree
        # "Everytime there is a variation possible from the main line,
        # a single TreeMovesWidget should be made"
        # Here we have multiple variations from `node`.
        self.sub_tree = TreeMovesWidget(node.variations, collapsible=self.collapsible)
        self.sub_tree.move_clicked.connect(self.move_clicked.emit)

        self.content_layout.addWidget(self.sub_tree)

        # Sync state with expand button if exists
        if self.expand_btn and not self.expand_btn.is_expanded:
            self.sub_tree.setVisible(False)

    def on_toggle(self, checked: bool) -> None:
        # "checked" means "expanded" in our ExpandWidget logic
        is_expanded = checked
        if self.sub_tree:
            self.sub_tree.setVisible(is_expanded)

        # Determine collapsed state for inline widget (inverse of expanded)
        self.inline_widget.set_collapsed(not is_expanded)

    def get_move_labels(self) -> list[MoveLabel]:
        labels = self.inline_widget.get_move_labels()
        if self.sub_tree and isinstance(self.sub_tree, TreeMovesWidget):
            labels.extend(self.sub_tree.get_move_labels())
        return labels


class TreeMovesWidget(QWidget):
    move_clicked = Signal(object)

    def __init__(
        self,
        variation_nodes: list[chess.pgn.ChildNode],
        collapsible: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 0, 0, 0)  # Indent for the tree level
        self.main_layout.setSpacing(2)

        self.branches = []
        for node in variation_nodes:
            branch = VariationBranchWidget(node, collapsible=collapsible)
            branch.move_clicked.connect(self.move_clicked.emit)
            self.main_layout.addWidget(branch)
            self.branches.append(branch)

    def get_move_labels(self) -> list[MoveLabel]:
        labels = []
        for branch in self.branches:
            labels.extend(branch.get_move_labels())
        return labels


class AnalysisBoardWidget(QScrollArea):
    move_clicked = Signal(object)
    move_hovered = Signal(object)  # Emits node when hovered, None when unhovered

    def __init__(
        self,
        game: Optional[chess.pgn.Game] = None,
        collapsible: bool = True,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.collapsible = collapsible
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Make the frame focusable
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

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

        self.setWidget(self.container)

        # Track active node and node-to-label mapping
        self.active_node: Optional[chess.pgn.GameNode] = None
        self.node_to_label: dict[chess.pgn.GameNode, MoveLabel] = {}

        # Initialize style
        self.setStyleSheet(STYLE_SCROLL_AREA)
        self._update_scrollbar_style()

        if game:
            self.process_game(game)

    def set_game(self, game: chess.pgn.Game) -> None:
        self.clear()
        self.process_game(game)

    def clear(self) -> None:
        """Clear the current game and reset the view."""
        # Remove all widgets from main_layout
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Reset state
        self.active_node = None
        self.node_to_label = {}
        self.scrollbar_hovered = False
        self._update_scrollbar_style()

    def process_game(self, game: chess.pgn.Game) -> None:
        # Add initial comment if any
        if game.comment:
            filtered_comment = _filter_comment(game.comment)
            if filtered_comment:
                self.add_annotation(filtered_comment)

        current_node: chess.pgn.ChildNode = game  # type: ignore
        current_row_widget: Optional[MoveRowWidget] = None
        split_row: bool = False

        while current_node.variations:
            # Check for existing sibling variations of the CURRENT line
            # (alternatives to main_next)
            # Standard PGN structure: node.variations[0] is main move,
            # others are alts.
            # Here `current_node.variations[0]` is the main line next move.
            # `current_node.variations[1:]` are the alternatives/variations
            # at this point.

            main_next = current_node.variations[0]
            variations = current_node.variations[1:]

            is_white = current_node.board().turn == chess.WHITE
            move_number = current_node.board().fullmove_number

            if is_white:
                # Prepare expand button if needed
                start_widget = None
                tree_widget = None
                expand_btn = None
                split_row = False

                has_comment = bool(
                    main_next.comment and _filter_comment(main_next.comment)
                )
                should_expand = (variations or has_comment) and self.collapsible

                if should_expand:
                    expand_btn = ExpandButton()
                    start_widget = expand_btn

                    if variations:
                        # Create tree widget now so we can connect
                        tree_widget = TreeMovesWidget(
                            variations, collapsible=self.collapsible
                        )
                        tree_widget.move_clicked.connect(self.move_clicked.emit)

                        # Connect toggle
                        expand_btn.toggled.connect(tree_widget.setVisible)

                        # Default state
                        tree_widget.setVisible(expand_btn.is_expanded)

                # Start new row
                current_row_widget = MoveRowWidget(
                    str(move_number),
                    white_node=main_next,
                    start_widget_white=start_widget,
                )
                current_row_widget.move_clicked.connect(self.move_clicked.emit)
                self.main_layout.addWidget(current_row_widget)
                self._register_move_labels(current_row_widget.get_move_labels())

                # If comment
                if main_next.comment:
                    filtered_comment = _filter_comment(main_next.comment)
                    if filtered_comment:
                        comment_lbl = self.add_annotation(filtered_comment)
                        if expand_btn:
                            expand_btn.toggled.connect(comment_lbl.setVisible)
                            comment_lbl.setVisible(expand_btn.is_expanded)
                        # Split the row because annotation breaks flow
                        split_row = True

                # If there are variations for this White move (siblings of main_next)
                if variations:
                    if not tree_widget:
                        # Non-collapsible or created without button
                        # (shouldn't happen if logic matches)
                        tree_widget = TreeMovesWidget(
                            variations, collapsible=self.collapsible
                        )
                        tree_widget.move_clicked.connect(self.move_clicked.emit)

                    self.main_layout.addWidget(tree_widget)
                    self._register_move_labels(tree_widget.get_move_labels())

                    # Split the row because variations breaks flow
                    split_row = True

            else:  # Black's turn
                # Prepare expand button if needed
                start_widget = None
                tree_widget = None
                expand_btn = None

                has_comment = bool(
                    main_next.comment and _filter_comment(main_next.comment)
                )
                should_expand = (variations or has_comment) and self.collapsible

                if should_expand:
                    expand_btn = ExpandButton()
                    start_widget = expand_btn

                    if variations:
                        tree_widget = TreeMovesWidget(
                            variations, collapsible=self.collapsible
                        )
                        tree_widget.move_clicked.connect(self.move_clicked.emit)

                        expand_btn.toggled.connect(tree_widget.setVisible)
                        tree_widget.setVisible(expand_btn.is_expanded)

                # Try to append to existing row
                if (
                    not split_row
                    and current_row_widget
                    and current_row_widget.black_node is None
                ):
                    current_row_widget.set_black_move(
                        main_next, start_widget=start_widget
                    )
                    self._register_move_labels(
                        [
                            lbl
                            for lbl in current_row_widget.get_move_labels()
                            if lbl.node == main_next
                        ]
                    )
                else:
                    previous_row_widget = current_row_widget

                    # Create new row with empty white
                    current_row_widget = MoveRowWidget(
                        str(move_number),
                        white_node=None,
                        black_node=main_next,
                        start_widget_black=start_widget,
                    )

                    # Hide this row if the white move is collapsed
                    if previous_row_widget:
                        previous_row_widget.black_split_row = current_row_widget
                        previous_white_lbl = cast(
                            MoveLabel,
                            previous_row_widget.lbl_white,
                        )
                        if isinstance(previous_white_lbl.start_widget, ExpandButton):
                            white_expand_btn = previous_white_lbl.start_widget
                            show_row = previous_row_widget.show_black_split_row
                            white_expand_btn.toggled.connect(show_row)

                    current_row_widget.move_clicked.connect(self.move_clicked.emit)
                    self.main_layout.addWidget(current_row_widget)
                    self._register_move_labels(current_row_widget.get_move_labels())

                # If comment
                if main_next.comment:
                    filtered_comment = _filter_comment(main_next.comment)
                    if filtered_comment:
                        comment_lbl = self.add_annotation(filtered_comment)
                        if expand_btn:
                            expand_btn.toggled.connect(comment_lbl.setVisible)
                            comment_lbl.setVisible(expand_btn.is_expanded)
                        current_row_widget = None

                # If there are variations for this Black move
                if variations:
                    if not tree_widget:
                        tree_widget = TreeMovesWidget(
                            variations, collapsible=self.collapsible
                        )
                        tree_widget.move_clicked.connect(self.move_clicked.emit)

                    self.main_layout.addWidget(tree_widget)
                    self._register_move_labels(tree_widget.get_move_labels())

            current_node = main_next

        self.main_layout.addStretch(1)

    def _register_move_labels(self, labels: list[MoveLabel]) -> None:
        """Register move labels and connect their signals."""
        for lbl in labels:
            self.node_to_label[lbl.node] = lbl
            lbl.hovered.connect(self.move_hovered.emit)

    def add_annotation(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(STYLE_ANNOTATION)
        self.main_layout.addWidget(lbl)
        return lbl

    def set_active_node(self, node: chess.pgn.GameNode) -> None:
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
            self.move_clicked.emit(self.active_node)

    def next_move(self) -> None:
        if self.active_node and len(self.active_node.variations) > 0:
            self.set_active_node(self.active_node.variations[0])
            self.move_clicked.emit(self.active_node)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Left:
            self.prev_move()
        elif event.key() == Qt.Key.Key_Right:
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
        # Clear all hover states when leaving the widget
        self._clear_all_hover_states()
        self._update_scrollbar_style()
        super().leaveEvent(event)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Track hover state on the scrollbar itself."""
        if hasattr(self, "overlay_scrollbar") and obj == self.overlay_scrollbar:
            if event.type() == QEvent.Type.Enter:
                self.scrollbar_hovered = True
                # Clear all hover states when entering scrollbar
                self._clear_all_hover_states()
                self._update_scrollbar_style()
            elif event.type() == QEvent.Type.Leave:
                self.scrollbar_hovered = False
                self._update_scrollbar_style()
        return bool(super().eventFilter(obj, event))

    def _clear_all_hover_states(self) -> None:
        """Clear hover state from all MoveLabels."""
        for label in self.node_to_label.values():
            if label.is_hovered:
                label.is_hovered = False
                label._update_style()

    def _update_scrollbar_style(self) -> None:
        """Update scrollbar appearance based on hover state."""
        if not hasattr(self, "overlay_scrollbar"):
            return

        # Check if scrolling is actually needed
        native_sb = self.verticalScrollBar()
        scrolling_needed = native_sb.maximum() > native_sb.minimum()

        # Determine visibility and style
        if self.scrollbar_hovered and scrolling_needed:
            # Full width handle when hovering scrollbar
            handle_margin = 0
            handle_width = 12
            color = "rgba(128, 128, 128, 0.6)"
            self.overlay_scrollbar.show()
        elif self.is_hovered and scrolling_needed:
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

import chess
import chess.pgn
import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent

from chess_widgets.analysis import (
    AnalysisBoardWidget,
    ExpandButton,
    MoveLabel,
    MoveRowWidget,
    TreeMovesWidget,
)


@pytest.fixture
def app(qapp: object) -> object:
    return qapp


def test_collapsible_moves(app: object) -> None:
    """Test standard flow for collapsible moves."""
    # Structure: 1. e4 (with variation)
    # 1. e4 (main)
    #    (1. d4 - alt)

    game = chess.pgn.Game()
    _ = game.add_variation(chess.Move.from_uci("e2e4"))
    _ = game.add_variation(chess.Move.from_uci("d2d4"))

    # Analysis board with collapsible=True
    board_widget = AnalysisBoardWidget(game, collapsible=True)
    board_widget.show()

    # We should have a move row for e4?
    # Actually logic: e4 is main next (variations[0]). d4 is variations[1].
    # So e4 is main line. d4 is variation.
    # Logic in process_game:
    # 1. Start new row for e4 (white).
    # 2. Add ExpandButton because there are variations.
    # 3. Create TreeMovesWidget for variations (d4).
    # 4. Collapse TreeMovesWidget by default? No, expand by default.

    # Check widgets in main_layout
    # Expected: row(e4) + tree_widget(d4)
    assert board_widget.main_layout.count() >= 2

    row_item = board_widget.main_layout.itemAt(0)
    tree_item = board_widget.main_layout.itemAt(1)

    row_widget = row_item.widget()
    tree_widget = tree_item.widget()

    assert isinstance(row_widget, MoveRowWidget)
    assert isinstance(tree_widget, TreeMovesWidget)

    # Verify row has expand button
    # We passed it as start_widget_white.
    # MoveRowWidget passes it to MoveLabel.
    # MoveLabel layout: [start_widget, label]

    lbl_white = row_widget.lbl_white
    assert isinstance(lbl_white, MoveLabel)

    # Find ExpandButton in lbl_white
    expand_btn = None
    for child in lbl_white.findChildren(ExpandButton):
        expand_btn = child
        break

    assert expand_btn is not None
    assert expand_btn.is_expanded is True

    # Verify tree is visible
    assert tree_widget.isVisible() is True

    # Click expand button to collapse
    # Simulate click
    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPoint(0, 0),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    expand_btn.mousePressEvent(event)

    assert expand_btn.is_expanded is False
    assert tree_widget.isVisible() is False

    # Click again to expand
    expand_btn.mousePressEvent(event)

    assert expand_btn.is_expanded is True
    assert tree_widget.isVisible() is True


def test_collapsible_moves_black(app: object) -> None:
    """Test collapsible moves for black."""
    # 1. e4 e5 (with variation 1... c5)

    game = chess.pgn.Game()
    e4 = game.add_variation(chess.Move.from_uci("e2e4"))

    _ = e4.add_variation(chess.Move.from_uci("e7e5"))
    _ = e4.add_variation(chess.Move.from_uci("c7c5"))

    board_widget = AnalysisBoardWidget(game, collapsible=True)
    board_widget.show()

    # e4 is row 0.
    # e5 is appended to row 0.
    # c5 is variation of e5 line (siblings of e5).
    # So row 0 should have expand button for BLACK move?

    # Row 0 contains e4 and e5.
    row_item = board_widget.main_layout.itemAt(0)
    row_widget = row_item.widget()
    assert isinstance(row_widget, MoveRowWidget)

    lbl_black = row_widget.lbl_black
    assert isinstance(lbl_black, MoveLabel)

    # Find ExpandButton in lbl_black
    expand_btn = None
    for child in lbl_black.findChildren(ExpandButton):
        expand_btn = child
        break

    assert expand_btn is not None

    # Get tree widget
    # It should be the next item in main_layout
    tree_item = board_widget.main_layout.itemAt(1)
    tree_widget = tree_item.widget()
    assert isinstance(tree_widget, TreeMovesWidget)

    assert tree_widget.isVisible() is True

    # Collapse
    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPoint(0, 0),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    expand_btn.mousePressEvent(event)
    assert tree_widget.isVisible() is False

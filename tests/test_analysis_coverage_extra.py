from typing import Any, cast

import chess
import chess.pgn
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QEnterEvent

from chess_widgets.analysis import (
    AnalysisBoardWidget,
    ExpandButton,
    MoveLabel,
    MoveRowWidget,
    TreeMovesWidget,
)


def test_expand_button_events(qtbot: Any) -> None:
    """Test ExpandButton events: enter, leave, paint."""
    btn = ExpandButton()
    with qtbot.waitExposed(btn):
        btn.show()

    # Enter event
    # We can trigger it by sending an event
    enter_event = QEnterEvent(QPoint(10, 10), QPoint(10, 10), QPoint(0, 0))
    # Direct call to ensure coverage logic is hit
    btn.enterEvent(enter_event)
    assert btn.is_hovered is True

    # Paint event
    # To cover paintEvent, we just need it to run.
    # showing the widget and waiting should trigger it.
    # If not, we can try to call it delicately.
    # But QPainter(self) fails if not in a real paint event.
    # Let's trust that showing it covers it, or if missed, we accept it is hard to
    # unit test paint.
    # OR we can mock QPainter? No.
    # The coverage report says 179-188 is missing.
    # Let's try calling it with a hack?
    # No, let's rely on standard widget painting.
    btn.update()
    qtbot.wait(50)  # Allow event loop to process paint

    # Leave event
    leave_event = QEnterEvent(QPoint(-1, -1), QPoint(-1, -1), QPoint(0, 0))
    btn.leaveEvent(leave_event)
    assert btn.is_hovered is False


def test_move_label_set_text(qtbot: Any) -> None:
    """Test MoveLabel.setText."""
    game = chess.pgn.Game()
    node = game.add_variation(chess.Move.from_uci("e2e4"))
    lbl = MoveLabel("e4", node, "QLabel { }")
    qtbot.addWidget(lbl)
    lbl.setText("e4!")
    assert lbl.text() == "e4!"


def test_black_split_row_collapsible(qtbot: Any) -> None:
    """Test splitting black row when white move is collapsed."""
    game = chess.pgn.Game()
    e4 = game.add_variation(chess.Move.from_uci("e2e4"))
    e4.comment = "Start"
    e5 = e4.add_variation(chess.Move.from_uci("e7e5"))

    board = AnalysisBoardWidget(game, collapsible=True)
    qtbot.addWidget(board)
    with qtbot.waitExposed(board):
        board.show()

    layout = board.main_layout
    assert layout.count() >= 3

    row1 = layout.itemAt(0).widget()
    # It might be filtered comment logic creates labels.
    # Check widgets

    # 0 -> Row white (e4)
    # 1 -> Comment
    # 2 -> Row black (e5)

    row1 = layout.itemAt(0).widget()
    assert isinstance(row1, MoveRowWidget)
    lbl_white = cast(MoveLabel, row1.lbl_white)
    assert "e4" in lbl_white.text()

    # Get expand button

    expand_btn = None
    for child in lbl_white.findChildren(ExpandButton):
        expand_btn = child
        break
    assert expand_btn is not None

    # Collapse
    qtbot.mouseClick(expand_btn, Qt.MouseButton.LeftButton)

    assert expand_btn.is_expanded is False

    # Check that black move is moved to row1
    lbl_black = cast(MoveLabel, row1.lbl_black)
    assert "e5" in lbl_black.text()
    assert lbl_black.node == e5

    # Expand again
    qtbot.mouseClick(expand_btn, Qt.MouseButton.LeftButton)
    assert expand_btn.is_expanded is True
    from PySide6.QtWidgets import QLabel

    lbl_black_placeholder = cast(QLabel, row1.lbl_black)
    assert lbl_black_placeholder.text() == "..."


def test_non_collapsible_variations(qtbot: Any) -> None:
    """Test non-collapsible mode logic."""
    game = chess.pgn.Game()
    e4 = game.add_variation(chess.Move.from_uci("e2e4"))
    _ = e4.parent.add_variation(chess.Move.from_uci("d2d4"))  # Variation for first move

    # e4...
    _ = e4.add_variation(chess.Move.from_uci("e7e5"))
    _ = e4.add_variation(chess.Move.from_uci("c7c5"))  # Variation for black

    board = AnalysisBoardWidget(game, collapsible=False)
    qtbot.addWidget(board)
    with qtbot.waitExposed(board):
        board.show()

    # Needs some time for async stuff if any? No.

    # Check for ExpandButtons - shoud be None
    expand_btns = board.findChildren(ExpandButton)
    assert len(expand_btns) == 0

    # There should be TreeMovesWidgets for d4 and c5
    trees = board.findChildren(TreeMovesWidget)
    # We expect at least one for d4 and one for c5.
    assert len(trees) >= 2
    # Wait, d4 is alternative to e4.
    # e4 is white.
    # c5 is alternative to e5. e5 is black.

    # In process_game for e4:
    # Variations exists (d4). collapsible=False.
    # Line 1018: if variations:
    # Line 1022: TreeMovesWidget created.

    # In process_game for e5:
    # Variations exists (c5). collapsible=False.
    # Line 1113: if variations:
    # Line 1115: TreeMovesWidget created.

    assert len(trees) >= 2

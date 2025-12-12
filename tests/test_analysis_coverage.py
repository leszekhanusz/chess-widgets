import chess
import chess.pgn
import pytest
from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QEnterEvent, QKeyEvent
from PySide6.QtWidgets import QApplication, QLabel

from chess_widgets.analysis import (
    AnalysisBoardWidget,
    ExpandButton,
    ExpandWidget,
    InlineMovesWidget,
    MoveLabel,
    MoveRowWidget,
    VariationBranchWidget,
    _is_linear_branch,
)


@pytest.fixture
def app(qapp: object) -> object:
    return qapp


def test_helper_is_linear_branch() -> None:
    """Test _is_linear_branch helper."""
    # Linear: 1 -> 2 -> 3
    game = chess.pgn.Game()
    node = game.add_variation(chess.Move.from_uci("e2e4"))
    node.add_variation(chess.Move.from_uci("e7e5"))
    # _is_linear_branch starts from a node.
    # Passing game (root) checks if root->next is linear path.
    # But game has 1 variation (e4). e4 has 1 (e5).
    # So it should be True.
    assert _is_linear_branch(game) is True

    # Branching: 1 -> (2a, 2b)
    game = chess.pgn.Game()
    node = game.add_variation(chess.Move.from_uci("d2d4"))
    node.add_variation(chess.Move.from_uci("d7d5"))
    node.add_variation(chess.Move.from_uci("g8f6"))

    # From start, it's linear until the first move, but the first move has variations.
    # _is_linear_branch checks if the *whole branch* starting from node is linear.
    # Here game has 1 child (d2d4). d2d4 has 2 children.
    # So game -> d2d4 is linear-ish, but d2d4 is not.
    # The function checks "while current: if len(variations) > 1: return False".

    assert _is_linear_branch(game) is False

    # Branching deeper: 1 -> 2 -> (3a, 3b)
    game = chess.pgn.Game()
    node = game.add_variation(chess.Move.from_uci("e2e4"))
    node = node.add_variation(chess.Move.from_uci("e7e5"))
    node.add_variation(chess.Move.from_uci("g1f3"))
    node.add_variation(chess.Move.from_uci("f1c4"))

    assert _is_linear_branch(game) is False


def test_move_label_events(app: object) -> None:
    """Test MoveLabel interactions."""
    game = chess.pgn.Game()
    node = game.add_variation(chess.Move.from_uci("e2e4"))

    label = MoveLabel("e4", node, "base_style")

    # Test initial state
    assert label.is_active is False
    assert label.cursor().shape() == Qt.CursorShape.PointingHandCursor

    # Test set_active True
    label.set_active(True)
    assert label.is_active is True
    assert label.cursor().shape() == Qt.CursorShape.ArrowCursor
    # Style should contain active style
    assert "active" in label.styleSheet() or "3d8cd7" in label.styleSheet()

    # Test set_active False
    label.set_active(False)
    assert label.is_active is False
    assert label.cursor().shape() == Qt.CursorShape.PointingHandCursor

    # Test hover events when inactive
    hovered_node = None

    def on_hover(n):
        nonlocal hovered_node
        hovered_node = n

    label.hovered.connect(on_hover)

    # Enter event when inactive -> should emit node and apply hover style
    label.enterEvent(QEnterEvent(QPoint(0, 0), QPoint(0, 0), QPoint(0, 0)))
    assert label.is_hovered is True
    assert hovered_node == node
    # Check that hover style is applied (line 189)
    assert "E4E4E4" in label.styleSheet() or "e4e4e4" in label.styleSheet()

    # Leave event when hovered -> should emit None and remove hover style
    hovered_node = None
    label.leaveEvent(QEvent(QEvent.Type.Leave))
    assert label.is_hovered is False
    assert hovered_node is None

    # Test hover events when active (should not trigger hover)
    label.set_active(True)
    hovered_node = None
    label.enterEvent(QEnterEvent(QPoint(0, 0), QPoint(0, 0), QPoint(0, 0)))
    # Should not set is_hovered or emit when active
    assert label.is_hovered is False
    assert hovered_node is None

    # Reset to inactive for click tests
    label.set_active(False)

    # Test click emission
    # Mock emission
    emitted_node = None
    emitted_event = "not_set"

    def on_click(n, event):
        nonlocal emitted_node, emitted_event
        emitted_node = n
        emitted_event = event

    label.clicked.connect(on_click)

    # Click when inactive -> should emit
    label.mousePressEvent(None)
    assert emitted_node == node
    assert emitted_event is None

    # Click when active -> should emit too
    emitted_node = None
    emitted_event = "not_set"
    label.set_active(True)
    label.mousePressEvent(None)
    assert emitted_node == node


def test_inline_moves_populate_complex(app: object) -> None:
    """Test InlineMovesWidget with complex branching coverage."""
    # Create a complex scenario:
    # 1. e4 e5
    # 2. Nf3 (Nc3)
    #    (Nc3 is a sibling of Nf3)

    game = chess.pgn.Game()
    e4 = game.add_variation(chess.Move.from_uci("e2e4"))
    e5 = e4.add_variation(chess.Move.from_uci("e7e5"))

    # Main line Nf3
    nf3 = e5.add_variation(chess.Move.from_uci("g1f3"))

    # Sibling variation Nc3
    nc3 = e5.add_variation(chess.Move.from_uci("b1c3"))
    # Add follow up to Nc3 to hit line 500 (iterating in populate_inline)
    nc3.add_variation(chess.Move.from_uci("a7a6"))

    # Add comments
    nf3.comment = "Main line [%clk 0:01:00]"
    nc3.comment = "Alternative"

    widget = InlineMovesWidget(e4)  # Start at e4

    # Verify labels
    labels = widget.move_labels
    # Should have e4... but wait, start_node is e4.
    # populate(node) starts iterating `current = node`.
    # So it renders e4 first.
    # Then e5.
    # Then checks variations of e5. e5 has Nf3 and Nc3.
    # It renders Nf3 (main)
    # It sees Nc3 is sibling of Nf3?
    # Logic:
    # 1. Render current (e4).
    # 2. Check siblings of current. e4 parent is Game. Game has 1 var (e4). No siblings.
    # 3. Next = e5.

    # Loop 2: current=e5.
    # Render e5.
    # Check siblings of e5? e5 parent is e4. e4 has 1 var (e5). No siblings.
    # Next = Nf3.

    # Loop 3: current=Nf3.
    # Render Nf3.
    # Check siblings of Nf3? Nf3 parent is e5. e5 has 2 vars: Nf3, Nc3.
    # YES siblings.
    # Iterate variations[1:] -> Nc3.
    # Call populate_inline(Nc3).

    # populate_inline(Nc3):
    # Render Nc3.

    move_texts = [label.text() for label in labels]
    # e4 is white. "1. e4"
    # e5 is black. "1... e5"
    # Nf3 is white. "2. Nf3"
    # Nc3 is white. "2. Nc3" (inside parens visually)

    assert any("e4" in t for t in move_texts)
    assert any("e5" in t for t in move_texts)
    assert any("Nf3" in t for t in move_texts)
    assert any("Nc3" in t for t in move_texts)

    # Check comment rendering
    # We can't easily check child widgets types directly without iterating layout items,
    # but we can assume if code ran without error, it added them.


def test_variation_branch_and_tree(app: object) -> None:
    """Test VariationBranchWidget and TreeMovesWidget."""
    # Create a branching structure
    # 1. e4 e5
    # 2. Nf3 (2. f4)
    #    2... Nc6
    game = chess.pgn.Game()
    e4 = game.add_variation(chess.Move.from_uci("e2e4"))
    e5 = e4.add_variation(chess.Move.from_uci("e7e5"))

    nf3 = e5.add_variation(chess.Move.from_uci("g1f3"))
    nf3.add_variation(chess.Move.from_uci("b8c6"))

    f4 = e5.add_variation(chess.Move.from_uci("f2f4"))  # King's Gambit

    # Start branch at e5 (so next are Nf3 and f4)
    # VariationBranchWidget takes a start_node and renders it linearly
    # until it hits a branch.
    # Here if we start at e5:
    # It renders e5.
    # Next has 2 variations: Nf3 (main), f4 (alt).
    # Logic says: "if len(next_moves) > 1 ... is_simple?"
    # Nf3 -> Nc6 (linear). f4 -> leaf (linear).
    # is_simple check: next_moves[1] is f4. _is_linear_branch(f4) -> True.
    # So is_simple = True.
    # It should CONTINUE main line (Nf3).
    # And handle f4 as sibling in the next iteration of populate_linear.

    # Let's force a complex branch so it splits.
    # Make f4 have branches.
    f4.add_variation(chess.Move.from_uci("e5f4"))
    f4.add_variation(chess.Move.from_uci("d7d5"))

    # Now next_moves[1] (f4) is NOT linear.
    # is_simple should be False.
    # It should emit branch_encountered.

    # Add comments to test coverage of populate_linear comments
    nf3.comment = "Linear comment"

    branch_widget = VariationBranchWidget(e5, collapsible=True)
    branch_widget.show()

    # It should have stopped at e5?
    # loop e5.
    # next is [Nf3, f4]. f4 is complex.
    # Stop. Emit branch_encountered(e5).
    # Then VariationBranchWidget.on_branch_encountered(e5) is called.
    # It should create a TreeMovesWidget for [Nf3, f4].

    assert branch_widget.sub_tree is not None
    assert branch_widget.expand_btn is not None

    # Toggle expand
    branch_widget.on_toggle(False)
    assert branch_widget.sub_tree.isVisible() is False

    branch_widget.on_toggle(True)
    assert branch_widget.sub_tree.isVisible() is True

    # Check move labels
    labels = branch_widget.move_labels
    texts = [label.text() for label in labels]
    assert any("e5" in t for t in texts)
    assert any("Nf3" in t for t in texts)
    assert any("f4" in t for t in texts)


def test_variation_branch_collapsed_then_populate(app: object) -> None:
    """Test VariationBranchWidget when collapsed and then a branch is encountered."""
    # This targets line 694: self.sub_tree.setVisible(False)

    # Structure: 1. e4 (branch here)
    # But VariationBranchWidget needs a linear start.
    # So: 1. e4 -> linear.
    # At e4, we have complex variations? No, VariationBranchWidget starts AT a node.
    # It renders that node, then next, etc.
    # Let's say we have:
    # 1. e4 (linear)
    # 2. e5 (complex branch: 3. Nf3 / 3. Nc6 / 3. d3)

    game = chess.pgn.Game()
    e4 = game.add_variation(chess.Move.from_uci("e2e4"))
    e5 = e4.add_variation(chess.Move.from_uci("e7e5"))

    e5.add_variation(chess.Move.from_uci("g1f3"))
    e5.add_variation(chess.Move.from_uci("b1c3"))
    e5.add_variation(chess.Move.from_uci("d2d3"))

    # Create widget starting at e4. It should encounter branch at e5.
    # But we want it to be COLLAPSED when it encounters the branch.

    # 1. Create widget, collapsible=True
    # It starts expanded.
    branch_widget = VariationBranchWidget(e4, collapsible=True)

    # 2. Collapse it BEFORE the inline widget encounters the branch.
    # We manually simulate the expand button state change because on_toggle
    # reacts to the signal but doesn't change the button state if called directly.
    # And on_branch_encountered reads the BUTTON state.
    branch_widget.on_toggle(False)
    assert branch_widget.expand_btn is not None
    branch_widget.expand_btn.is_expanded = False
    assert branch_widget.expand_btn.is_expanded is False

    # Now manually call on_branch_encountered with a fake node that has variations
    # We need a node with variations to pass to TreeMovesWidget constructor
    dummy_node = game.add_variation(chess.Move.from_uci("a2a3"))
    dummy_node.add_variation(chess.Move.from_uci("a7a6"))  # var 0
    dummy_node.add_variation(chess.Move.from_uci("h7h6"))  # var 1

    # Calling this should trigger line 694
    branch_widget.on_branch_encountered(dummy_node)

    # Verify sub_tree was created and is HIDDEN
    assert branch_widget.sub_tree is not None
    assert branch_widget.sub_tree.isVisible() is False


def test_inline_moves_stop_complex_no_defer(app: object) -> None:
    """Test InlineMovesWidget with stop_on_complex_branch=True & immediate populate."""
    game = chess.pgn.Game()
    node = game.add_variation(chess.Move.from_uci("e2e4"))

    # Should hit line 292
    widget = InlineMovesWidget(node, stop_on_complex_branch=True, defer_populate=False)
    assert widget.layout() is not None


def test_inline_moves_collapsed(app: object) -> None:
    """Test InlineMovesWidget set_collapsed method."""
    game = chess.pgn.Game()
    node = game.add_variation(chess.Move.from_uci("e2e4"))
    node.add_variation(chess.Move.from_uci("e7e5"))

    # We need a widget with multiple items
    widget = InlineMovesWidget(node)
    widget.show()  # Must show widget for isVisible() to work on children

    # By default, not collapsed
    # Check visibility of children.
    # e4 is first move. e5 is second.
    # We can check specific move labels
    labels = widget.move_labels
    assert len(labels) == 2

    # Collapse
    widget.set_collapsed(True)

    # First label (e4) should be visible
    # Second label (e5) should be hidden
    assert labels[0].isVisible() is True
    assert labels[1].isVisible() is False

    # Uncollapse
    widget.set_collapsed(False)
    assert labels[0].isVisible() is True
    assert labels[1].isVisible() is True


def test_analysis_board_full_flow(app: object) -> None:
    """Test AnalysisBoardWidget processing a full game."""
    import textwrap

    pgn = textwrap.dedent(
        """
    [Event "Test"]
    [Site "?"]
    [Date "2024.01.01"]
    [Round "?"]
    [White "White"]
    [Black "Black"]
    [Result "*"]
    [Annotator "Test"]

    1. e4 e5 2. Nf3 (2. f4) Nc6 3. Bb5 a6 (3... Nf6 4. O-O) 4. Ba4 *
    """
    )
    import io

    game = chess.pgn.read_game(io.StringIO(pgn))
    assert game is not None
    game.comment = "Start game comment"

    board_widget = AnalysisBoardWidget(game)
    board_widget.show()

    # 1. Check annotations
    # We can check if QLabels with specific text exist in main_layout
    found_comment = False
    for i in range(board_widget.main_layout.count()):
        item = board_widget.main_layout.itemAt(i)
        w = item.widget()
        if isinstance(w, QLabel) and "Start game comment" in w.text():
            found_comment = True
            break
    assert found_comment

    # 2. Check navigation
    # Initial active node is None until clicked or set
    assert board_widget.active_node is None

    # Find e4 node
    node_e4 = game.variations[0]
    board_widget.set_active_node(node_e4)
    assert board_widget.active_node == node_e4
    assert board_widget.node_to_label[node_e4].is_active is True

    # Next move -> e5
    board_widget.next_move()
    node_e5 = node_e4.variations[0]
    assert board_widget.active_node == node_e5

    # Prev move -> e4
    board_widget.prev_move()
    assert board_widget.active_node == node_e4

    # Prev move -> Root (Game) -> active_node should be Game?
    # node_to_label usually doesn't contain Root unless we mapped it?
    # The code `if self.active_node and self.active_node.parent:`
    # If parent is game, is it in node_to_label? unlikely.
    # Implementation of set_active_node: `if node in self.node_to_label:`
    # So if root is not in node_to_label, it won't highlight,
    # but active_node *might* not update
    # effectively if it requires being in the map to update `self.active_node`.
    # Code:
    # if node in self.node_to_label:
    #    ...
    #    self.active_node = node
    # So if we go to root, and root is not in map, active_node stays at e4.

    board_widget.prev_move()
    # Should still be e4 if root is not mapped
    assert board_widget.active_node == node_e4

    # 3. Keyboard events
    # Simulate Right key
    event = QKeyEvent(
        QEvent.Type.KeyPress, Qt.Key.Key_Right, Qt.KeyboardModifier.NoModifier
    )
    board_widget.keyPressEvent(event)
    # Should move to e5
    assert board_widget.active_node == node_e5

    # Simulate Left key
    event = QKeyEvent(
        QEvent.Type.KeyPress, Qt.Key.Key_Left, Qt.KeyboardModifier.NoModifier
    )
    board_widget.keyPressEvent(event)
    assert board_widget.active_node == node_e4

    # Simulate other key (coverage line 864)
    # Using Key_A which is not Left/Right
    event = QKeyEvent(
        QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier
    )
    board_widget.keyPressEvent(event)

    # 4. Scrollbar hover events
    # First, make the widget small enough that scrolling is needed
    board_widget.resize(500, 100)
    # Process events to ensure resize is applied
    from PySide6.QtWidgets import QApplication

    QApplication.processEvents()

    # Trigger enterEvent
    board_widget.enterEvent(QEnterEvent(QPoint(0, 0), QPoint(0, 0), QPoint(0, 0)))
    assert board_widget.is_hovered is True
    # Scrollbar should be visible only if scrolling is needed
    native_sb = board_widget.verticalScrollBar()
    scrolling_needed = native_sb.maximum() > native_sb.minimum()
    assert board_widget.overlay_scrollbar.isVisible() == scrolling_needed

    # Trigger leaveEvent
    board_widget.leaveEvent(QEvent(QEvent.Type.Leave))
    assert board_widget.is_hovered is False
    assert board_widget.overlay_scrollbar.isVisible() is False

    # Trigger scrollbar hover via eventFilter
    board_widget.overlay_scrollbar = getattr(
        board_widget, "overlay_scrollbar"
    )  # ensure access
    # Mock event filter call
    board_widget.eventFilter(board_widget.overlay_scrollbar, QEvent(QEvent.Type.Enter))
    assert board_widget.scrollbar_hovered is True
    assert board_widget.overlay_scrollbar.isVisible() == scrolling_needed

    board_widget.eventFilter(board_widget.overlay_scrollbar, QEvent(QEvent.Type.Leave))
    assert board_widget.scrollbar_hovered is False

    # 5. Resize
    board_widget.resize(500, 500)
    # resizeEvent should trigger and place scrollbar
    sb_geo = board_widget.overlay_scrollbar.geometry()
    assert sb_geo.x() == 500 - 12

    # 6. Test _clear_all_hover_states (lines 957-958)
    # Manually set a label to hovered state
    if node_e4 in board_widget.node_to_label:
        label = board_widget.node_to_label[node_e4]
        label.is_hovered = True
        label._update_style()
        assert label.is_hovered is True
        # Now clear all hover states
        board_widget._clear_all_hover_states()
        assert label.is_hovered is False


def test_expand_widget(app: object) -> None:
    """Test ExpandWidget toggling."""
    widget = ExpandWidget()
    assert widget.is_expanded is True
    # Can't check text directly as it's painted, but we can check state

    # Simulate click
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtGui import QMouseEvent

    event = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPoint(0, 0),
        QPoint(0, 0),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mousePressEvent(event)  # Toggles to False
    assert widget.is_expanded is False

    widget.mousePressEvent(event)  # Toggles back to True
    assert widget.is_expanded is True

    # Test enter/leave events (lines 577-582)
    widget.enterEvent(QEnterEvent(QPoint(0, 0), QPoint(0, 0), QPoint(0, 0)))
    assert widget.is_hovered is True

    widget.leaveEvent(QEvent(QEvent.Type.Leave))
    assert widget.is_hovered is False

    # Test paint event (lines 585-609)
    widget.repaint()
    QApplication.processEvents()

    # Manually trigger paint via render which is synchronous and reliable for coverage
    from PySide6.QtGui import QPixmap

    w = ExpandWidget()
    w.resize(20, 100)
    # We don't even need to show it if we render to a pixmap?
    # Actually w.render() works on invisible widgets if we use QPainter
    # redirection or just render(QPainter) or render(QPaintDevice).
    target = QPixmap(100, 100)
    w.render(target)


def test_scrollbar_safeguard(app: object) -> None:
    """Test _update_scrollbar_style safeguard."""
    board_widget = AnalysisBoardWidget()
    # Delete attribute to trigger safeguard (line 902 check)
    del board_widget.overlay_scrollbar
    # Calling this should not raise error, just return logic
    board_widget._update_scrollbar_style()
    # Trigger event that calls it
    board_widget.enterEvent(QEnterEvent(QPoint(0, 0), QPoint(0, 0), QPoint(0, 0)))


def test_set_game_and_clear(app: object) -> None:
    """Test set_game and clear methods of AnalysisBoardWidget."""
    import io
    import textwrap

    # Create initial game
    pgn1 = textwrap.dedent(
        """
    [Event "Test1"]
    [Site "?"]
    [Date "2024.01.01"]
    [Round "?"]
    [White "White"]
    [Black "Black"]
    [Result "*"]

    1. e4 e5 2. Nf3 Nc6 *
    """
    )
    game1 = chess.pgn.read_game(io.StringIO(pgn1))
    assert game1 is not None

    # Create widget with initial game
    board_widget = AnalysisBoardWidget(game1)
    board_widget.show()

    # Verify initial game is loaded
    assert board_widget.main_layout.count() > 0
    node_e4 = game1.variations[0]
    assert node_e4 in board_widget.node_to_label

    # Set active node
    board_widget.set_active_node(node_e4)
    assert board_widget.active_node == node_e4

    # Create second game
    pgn2 = textwrap.dedent(
        """
    [Event "Test2"]
    [Site "?"]
    [Date "2024.01.02"]
    [Round "?"]
    [White "Player1"]
    [Black "Player2"]
    [Result "*"]

    1. d4 d5 2. c4 *
    """
    )
    game2 = chess.pgn.read_game(io.StringIO(pgn2))
    assert game2 is not None

    # Use set_game to replace the game (covers lines 714-715)
    board_widget.set_game(game2)

    # Verify old game is cleared and new game is loaded
    assert node_e4 not in board_widget.node_to_label
    node_d4 = game2.variations[0]
    assert node_d4 in board_widget.node_to_label

    # Verify active_node was reset
    assert board_widget.active_node is None

    # Test clear method directly (covers lines 720-730)
    board_widget.clear()

    # Verify everything is cleared
    assert board_widget.main_layout.count() == 0
    assert board_widget.active_node is None
    assert len(board_widget.node_to_label) == 0
    assert board_widget.scrollbar_hovered is False


def test_analysis_board_collapse(app: object) -> None:
    """Test AnalysisBoardWidget collapse method."""
    import io
    import textwrap

    # Create a game with variations and comments to trigger expand buttons
    pgn_text = textwrap.dedent(
        """
        [Event "Test"]
        [Site "Test"]
        [Date "2023.01.01"]
        [Round "1"]
        [White "White"]
        [Black "Black"]
        [Result "*"]

        1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 (3... Nf6) 4. Ba4 Nf6 5. O-O
        (5. d3 d6 6. Bg5 (6. c3) (6. Nbd2)) *
        """
    )

    pgn = chess.pgn.read_game(io.StringIO(pgn_text))
    widget = AnalysisBoardWidget(pgn)

    # Helper to count visible items or expanded buttons
    def count_expanded_buttons(w: object) -> int:
        count = 0
        if isinstance(w, AnalysisBoardWidget):
            layout = w.main_layout
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    count += count_expanded_buttons(item.widget())
        elif isinstance(w, MoveRowWidget):
            for lbl in [w.lbl_white, w.lbl_black]:
                if isinstance(lbl, MoveLabel) and isinstance(
                    lbl.start_widget, ExpandButton
                ):
                    if lbl.start_widget.is_expanded:
                        count += 1
        return count

    # Initially expanded
    initial_expanded = count_expanded_buttons(widget)
    assert initial_expanded > 0

    # Collapse
    widget.collapse(True)
    collapsed_expanded = count_expanded_buttons(widget)
    assert collapsed_expanded == 0

    # Expand
    widget.collapse(False)
    final_expanded = count_expanded_buttons(widget)
    assert final_expanded == initial_expanded

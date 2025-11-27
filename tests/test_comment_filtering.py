import chess.pgn
from PySide6.QtWidgets import QLabel
from pytestqt.qtbot import QtBot

from chess_widgets.analysis import AnalysisBoardWidget


def test_comment_filtering(qtbot: QtBot) -> None:
    # Create a dummy game with comments
    game = chess.pgn.Game()
    game.comment = "Initial comment [%csl Gf3]"

    node = game.add_variation(chess.Move.from_uci("e2e4"))
    node.comment = "Normal comment [%cal Ge2e4] with annotation"

    node = node.add_variation(chess.Move.from_uci("e7e5"))
    node.comment = "[%csl Ge5] Only annotation"

    node = node.add_variation(chess.Move.from_uci("d2d4"))
    node.comment = "Line 1\nLine 2 [%csl Gf3]"

    # Initialize widget
    widget = AnalysisBoardWidget(game)
    qtbot.addWidget(widget)

    # Helper to find all QLabels in the widget
    labels = widget.findChildren(QLabel)
    texts = [lbl.text() for lbl in labels]

    # Verify filtering
    # 1. Initial comment should be "Initial comment"
    assert "Initial comment" in texts
    assert "Initial comment [%csl Gf3]" not in texts

    # 2. Normal comment should be "Normal comment  with annotation"
    assert "Normal comment  with annotation" in texts
    assert "Normal comment [%cal Ge2e4] with annotation" not in texts

    # 3. "Only annotation" should result in NO label with that text
    # (empty string filtered out)
    # Note: If the filtering returns empty string, the code should NOT add a label.
    # So we shouldn't find an empty string label or a label with just spaces.
    # But wait, if it's empty, we said we wouldn't add it.
    # Let's check that we don't see the original text.
    assert "[%csl Ge5] Only annotation" not in texts
    assert "Only annotation" in texts
    # Ah, my test case string was "[%csl Ge5] Only annotation".
    # So "Only annotation" SHOULD remain.

    # Let's add a case that should be COMPLETELY removed.
    node = node.add_variation(chess.Move.from_uci("g1f3"))
    node.comment = "[%csl Gf3][%cal Gf3g5]"

    # Re-init widget to include new move? Or just process again?
    # AnalysisBoardWidget processes game in __init__.
    widget = AnalysisBoardWidget(game)
    qtbot.addWidget(widget)
    labels = widget.findChildren(QLabel)
    texts = [lbl.text() for lbl in labels]

    # Check that the completely removed comment is not present as a label
    # It's hard to check "not present" for empty string if there are other labels.
    # But we can check that no label contains the original text.
    for t in texts:
        assert "[%csl" not in t
        assert "[%cal" not in t

    # Check specific expected texts
    assert "Initial comment" in texts
    assert "Normal comment  with annotation" in texts
    assert "Only annotation" in texts
    assert "Line 1\nLine 2" in texts

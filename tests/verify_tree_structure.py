import sys

import chess.pgn
from PySide6.QtWidgets import QApplication, QWidget

from chess_widgets.analysis import (
    AnalysisBoardWidget,
    InlineMovesWidget,
    MoveRowWidget,
    TreeMovesWidget,
    VariationBranchWidget,
)


def print_widget_tree(widget: QWidget, indent: int = 0) -> None:
    indent_str = " " * indent
    widget_type = type(widget).__name__
    info = ""

    if isinstance(widget, MoveRowWidget):
        white = widget.lbl_white.text() if hasattr(widget.lbl_white, "text") else "..."
        black = widget.lbl_black.text() if hasattr(widget.lbl_black, "text") else "..."
        info = f"[{white} {black}]"
    elif isinstance(widget, InlineMovesWidget):
        # Count moves
        moves = [lbl.text() for lbl in widget.move_labels]
        info = f"Moves: {len(moves)} " + (f"({moves[0]}...)" if moves else "")
    elif isinstance(widget, VariationBranchWidget):
        info = f"Start: {widget.start_node.san()}"

    print(f"{indent_str}{widget_type} {info}")

    # Traverse children via layout or known attributes
    children: list[QWidget] = []

    if isinstance(widget, AnalysisBoardWidget):
        # Main layout items
        layout = widget.main_layout
        for i in range(layout.count()):
            item = layout.itemAt(i)
            # mypy workaround: itemAt returns QLayoutItem,
            # widget() returns QWidget/None.
            if item.widget():
                w = item.widget()
                if w:
                    children.append(w)

    elif isinstance(widget, TreeMovesWidget):
        children.extend(widget.branches)

    elif isinstance(widget, VariationBranchWidget):
        # Header has inline widget
        children.append(widget.inline_widget)
        # Body has sub_tree
        if widget.sub_tree:
            children.append(widget.sub_tree)

    elif isinstance(widget, QWidget):
        # Generic traversal if needed,
        # but for our specific widgets we want logical children
        pass

    for child in children:
        print_widget_tree(child, indent + 2)


def main() -> None:
    app = QApplication(sys.argv)
    _ = app  # Suppress unused variable warning

    pgn_path = "examples/test_variations_4moves.pgn"
    print(f"Loading {pgn_path}...")
    with open(pgn_path) as f:
        game = chess.pgn.read_game(f)

    print("Creating AnalysisBoardWidget...")
    widget = AnalysisBoardWidget(game, collapsible=True)

    print("\nWidget Hierarchy:")
    print_widget_tree(widget)

    print("\nVerifying Tree Structure...")
    # Basic assertions based on output inspection expectation
    found_tree = False

    # We can inspect `widget.node_to_label` to check coverage too?
    # But inspecting the hierarchy is better.

    # Check if we have TreeMovesWidget in the main layout
    # (should be there for alternatives to 1. e4)
    layout = widget.main_layout
    for i in range(layout.count()):
        item = layout.itemAt(i)
        w = item.widget() if item else None
        if isinstance(w, TreeMovesWidget):
            found_tree = True
            print("Found top-level TreeMovesWidget (Correct)")
            if isinstance(w.branches[0], VariationBranchWidget):
                print("  Tree contains VariationBranchWidget (Correct)")
                # Check deeper nesting
                branch = w.branches[0]  # likely 1. d4
                if branch.sub_tree:
                    print("  Branch has sub_tree (Correct/Expected for complex PGN)")
                else:
                    # 1. d4 is 1. d4 d5 (1... Nf6).
                    # Wait, 1. d4... inline should stop at d5/Nf6 split.
                    # So it should have a sub_tree.
                    print("  Branch has NO sub_tree (Check if expected?)")
            break

    if not found_tree:
        print("ERROR: No TreeMovesWidget found at top level!")
        sys.exit(1)

    print("\nVerification Complete.")
    # Don't show window, just exit
    sys.exit(0)


if __name__ == "__main__":
    main()

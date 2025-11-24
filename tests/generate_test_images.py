import os
import sys

# Force offscreen platform to match CI environment
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import chess  # noqa: E402
from PySide6.QtCore import QPointF, QSize, Qt  # noqa: E402
from PySide6.QtGui import QImage, QMouseEvent  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from chess_widgets import BoardWidget  # noqa: E402


def save_snapshot(widget: BoardWidget, filename: str) -> None:
    """Render widget to an image and save it."""
    # Ensure directory exists
    assets_dir = os.path.join(os.path.dirname(__file__), "assets", "images")
    os.makedirs(assets_dir, exist_ok=True)

    path = os.path.join(assets_dir, filename)

    # Create a QImage with the same size as the widget
    image = QImage(widget.size(), QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)

    # Render the widget into the image
    widget.render(image)

    # Save
    image.save(path)
    print(f"Saved {path}")


def main() -> None:
    """Generate reference images for visual regression tests.

    IMPORTANT: This script uses offscreen rendering (set via
    QT_QPA_PLATFORM env var) to ensure the generated images match what
    GitHub Actions will produce during CI. If you regenerate these images
    without offscreen rendering, the tests will fail in CI.
    """
    app = QApplication(sys.argv)

    # Fixed size for consistency
    SIZE = QSize(400, 400)

    # 1. Initial board
    widget = BoardWidget()
    widget.resize(SIZE)
    # Force layout/paint
    widget.show()
    app.processEvents()
    save_snapshot(widget, "initial_board.png")
    widget.close()

    # 2. Initial board flipped
    widget = BoardWidget()
    widget.resize(SIZE)
    widget.set_flipped(True)
    widget.show()
    app.processEvents()
    save_snapshot(widget, "initial_board_flipped.png")
    widget.close()

    # 3. Italian opening (from board)
    # 1. e4 e5 2. Nf3 Nc6 3. Bc4
    italian_fen = "r1bqk1nr/pppp1ppp/2n5/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    board = chess.Board(italian_fen)
    widget = BoardWidget(board=board)
    widget.resize(SIZE)
    widget.show()
    app.processEvents()
    save_snapshot(widget, "italian_opening_board.png")
    widget.close()

    # 4. Italian opening (from moves)
    widget = BoardWidget()
    widget.resize(SIZE)
    widget.show()
    moves = ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5"]
    for uci in moves:
        widget.play_move(chess.Move.from_uci(uci), animate=False)
    app.processEvents()
    save_snapshot(widget, "italian_opening_moves.png")
    widget.close()

    # 5. White pawn selected (legal moves)
    widget = BoardWidget()
    widget.resize(SIZE)
    widget.show()
    # Select e2 pawn (square e2 is 12)
    # We need to simulate a click or programmatically select
    # The widget doesn't expose selection publicly easily,
    # but we can simulate mouse event
    # e2 is at rank 2 (index 1), file e (index 4).
    # Board rect is full widget.
    # square size = 400 / 8 = 50.
    # e2 center: x = 4 * 50 + 25 = 225,
    # y = (7-1) * 50 + 25 = 325 (rank 2 is row 6 from top 0-7)
    # Wait, rank 1 is row 7. Rank 2 is row 6.
    # e2: file e (4), rank 2.
    # x = 4 * 50 + 25 = 225
    # y = (7 - 1) * 50 + 25 = 325.

    # Let's verify coordinate system in widget.py:
    # visual_row = 7 - rank (if not flipped), visual_col = file
    # rank 0-7. e2 is rank 1 (0-indexed). file 4.
    # visual_row = 7 - 1 = 6.
    # visual_col = 4.
    # x = 4 * 50 + 25 = 225.
    # y = 6 * 50 + 25 = 325.

    click_point = QPointF(225, 325)
    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        click_point,
        click_point,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mousePressEvent(event)

    app.processEvents()
    save_snapshot(widget, "white_pawn_selected.png")
    widget.close()

    # 6. Scandinavian opening (capture)
    # 1. e4 d5
    widget = BoardWidget()
    widget.resize(SIZE)
    widget.show()
    widget.play_move(chess.Move.from_uci("e2e4"), animate=False)
    widget.play_move(chess.Move.from_uci("d7d5"), animate=False)

    # Select e4 pawn to show capture on d5
    # e4 is rank 3 (index 3), file e (index 4).
    # visual_row = 7 - 3 = 4.
    # visual_col = 4.
    # x = 4 * 50 + 25 = 225.
    # y = 4 * 50 + 25 = 225.

    click_point = QPointF(225, 225)
    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        click_point,
        click_point,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mousePressEvent(event)

    app.processEvents()
    save_snapshot(widget, "scandinavian_capture.png")
    widget.close()


if __name__ == "__main__":
    main()

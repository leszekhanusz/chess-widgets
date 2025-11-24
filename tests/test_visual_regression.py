import math
import os
from typing import TYPE_CHECKING

import chess
from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QImage, QMouseEvent

from chess_widgets import BoardWidget

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets", "images")
SIZE = QSize(400, 400)


def compare_images(
    widget: BoardWidget, reference_filename: str, tolerance: float = 5.0
) -> None:
    """Render widget and compare with reference image using RMS difference."""
    # Render widget
    image = QImage(widget.size(), QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    widget.render(image)

    # Load reference
    ref_path = os.path.join(ASSETS_DIR, reference_filename)
    assert os.path.exists(ref_path), f"Reference image not found: {ref_path}"

    ref_image = QImage(ref_path)
    assert not ref_image.isNull(), f"Failed to load reference image: {ref_path}"

    # Compare size
    assert (
        image.size() == ref_image.size()
    ), f"Size mismatch: {image.size()} != {ref_image.size()}"

    # Fast path: strict equality
    if image == ref_image:
        return

    # Slow path: Calculate RMS difference
    # We iterate over pixels to calculate the difference
    width = image.width()
    height = image.height()
    diff_sum = 0.0

    # Check up to a reasonable number of pixels to avoid extremely slow tests
    # but 400x400 is small enough (160k pixels) to do in pure Python if needed.
    # Using pixel() which returns int is faster than pixelColor()

    for y in range(height):
        for x in range(width):
            p1 = image.pixel(x, y)
            p2 = ref_image.pixel(x, y)

            # Extract RGB (ignoring alpha for now as board is opaque usually,
            # but ARGB32 has alpha. Let's include alpha if needed, or just RGB)
            # qRgb/qRed/etc are C++ macros, in Python we shift manually or use QColor
            # Manual shift for speed: ARGB

            r1, g1, b1 = (p1 >> 16) & 0xFF, (p1 >> 8) & 0xFF, p1 & 0xFF
            r2, g2, b2 = (p2 >> 16) & 0xFF, (p2 >> 8) & 0xFF, p2 & 0xFF

            diff_sum += (r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2

    # Mean Squared Error
    total_components = width * height * 3
    mse = diff_sum / total_components
    rms = math.sqrt(mse)

    assert rms <= tolerance, (
        f"Image mismatch for {reference_filename}. "
        f"RMS difference: {rms:.2f} > tolerance {tolerance}"
    )


def test_initial_board(qtbot: "QtBot") -> None:
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.resize(SIZE)
    widget.show()
    qtbot.waitExposed(widget)

    compare_images(widget, "initial_board.png")


def test_initial_board_flipped(qtbot: "QtBot") -> None:
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.resize(SIZE)
    widget.set_flipped(True)
    widget.show()
    qtbot.waitExposed(widget)

    compare_images(widget, "initial_board_flipped.png")


def test_italian_opening_board(qtbot: "QtBot") -> None:
    italian_fen = "r1bqk1nr/pppp1ppp/2n5/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    board = chess.Board(italian_fen)
    widget = BoardWidget(board=board)
    qtbot.addWidget(widget)
    widget.resize(SIZE)
    widget.show()
    qtbot.waitExposed(widget)

    compare_images(widget, "italian_opening_board.png")


def test_italian_opening_moves(qtbot: "QtBot") -> None:
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.resize(SIZE)
    widget.show()
    qtbot.waitExposed(widget)

    moves = ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5"]
    for uci in moves:
        widget.play_move(chess.Move.from_uci(uci), animate=False)

    compare_images(widget, "italian_opening_moves.png")


def test_white_pawn_selected(qtbot: "QtBot") -> None:
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.resize(SIZE)
    widget.show()
    qtbot.waitExposed(widget)

    # Select e2 pawn
    # e2: file e (4), rank 2.
    # visual_row = 7 - 1 = 6.
    # visual_col = 4.
    # x = 4 * 50 + 25 = 225.
    # y = 6 * 50 + 25 = 325.
    click_point = QPointF(225, 325)

    # Use direct event to match generator behavior exactly

    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        click_point,
        click_point,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mousePressEvent(event)

    compare_images(widget, "white_pawn_selected.png")


def test_scandinavian_capture(qtbot: "QtBot") -> None:
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.resize(SIZE)
    widget.show()
    qtbot.waitExposed(widget)

    widget.play_move(chess.Move.from_uci("e2e4"), animate=False)
    widget.play_move(chess.Move.from_uci("d7d5"), animate=False)

    # Select e4 pawn
    # e4: file e (4), rank 3.
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

    compare_images(widget, "scandinavian_capture.png")

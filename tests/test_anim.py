import chess
from pytestqt.qtbot import QtBot

from chess_widgets import BoardWidget


def test_animation(qtbot: QtBot) -> None:
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()

    # Setup a move to animate
    move = chess.Move.from_uci("e2e4")

    # Trigger animation
    widget.play_move(move, animate=True)

    # Wait for animation to complete (approx 1000ms safe margin)
    qtbot.wait(1000)

    # Verify move was made on board
    assert widget._board.peek() == move

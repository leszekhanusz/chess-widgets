import chess
from pytestqt.qtbot import QtBot

from chess_widgets.board import BoardWidget


def test_play_move_interrupts_animation(qtbot: QtBot) -> None:
    """Test that playing a new move interrupts a running animation."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Play first move with animation
    move1 = chess.Move.from_uci("e2e4")
    widget.play_move(move1, animate=True)

    # Verify animation started
    assert widget._anim_timer.isActive()
    assert len(widget._animating_pieces) > 0

    # Immediately play another move before animation completes
    # This should trigger the animation interruption code:
    # if self._anim_timer.isActive():
    #     self._anim_timer.stop()
    #     self._animating_pieces = []
    move2 = chess.Move.from_uci("e7e5")
    widget.play_move(move2, animate=True)

    # Wait for second animation to complete
    qtbot.wait(1000)

    # Verify both moves were made
    assert len(widget._board.move_stack) == 2
    assert widget._board.move_stack[0] == move1
    assert widget._board.move_stack[1] == move2


def test_undo_interrupts_animation(qtbot: QtBot) -> None:
    """Test that undoing interrupts a running animation."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Play a move first (without animation)
    move1 = chess.Move.from_uci("e2e4")
    widget.play_move(move1, animate=False)

    # Play second move with animation
    move2 = chess.Move.from_uci("e7e5")
    widget.play_move(move2, animate=True)

    # Verify animation started
    assert widget._anim_timer.isActive()
    assert len(widget._animating_pieces) > 0

    # Immediately undo before animation completes
    # This should trigger the animation interruption code in undo_move:
    # if self._anim_timer.isActive():
    #     self._anim_timer.stop()
    #     self._animating_pieces = []
    widget.undo_move(animate=True)

    # Wait for undo animation to complete
    qtbot.wait(1000)

    # Verify undo was successful
    assert len(widget._board.move_stack) == 1
    assert widget._board.peek() == move1


def test_undo_regular_move_animated(qtbot: QtBot) -> None:
    """Test undoing a regular (non-castling) move with animation enabled."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Play a regular move (pawn move)
    move = chess.Move.from_uci("e2e4")
    widget.play_move(move, animate=False)

    assert widget._board.peek() == move
    assert widget._board.piece_at(chess.E4) == chess.Piece(chess.PAWN, chess.WHITE)
    assert widget._board.piece_at(chess.E2) is None

    # Undo with animation
    # This should trigger the non-castling animation code path:
    # else:
    #     # Standard undo animation
    #     piece = self._board.piece_at(move.from_square)
    #     if piece:
    #         start_pos = self._get_square_center(move.to_square)
    #         end_pos = self._get_square_center(move.from_square)
    #         self._animating_pieces.append(...)
    widget.undo_move(animate=True)

    # Animation should have started
    assert widget._anim_timer.isActive() or widget._anim_progress >= 1.0

    # Wait for animation to complete
    qtbot.wait(1000)

    # Verify undo was successful
    assert len(widget._board.move_stack) == 0
    assert widget._board.piece_at(chess.E2) == chess.Piece(chess.PAWN, chess.WHITE)
    assert widget._board.piece_at(chess.E4) is None


def test_undo_capture_move_animated(qtbot: QtBot) -> None:
    """Test undoing a capture move with animation."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Set up a capture
    widget.play_move(chess.Move.from_uci("e2e4"), animate=False)
    widget.play_move(chess.Move.from_uci("d7d5"), animate=False)

    # Capture move
    capture_move = chess.Move.from_uci("e4d5")
    widget.play_move(capture_move, animate=False)

    # Verify capture was made
    assert widget._board.piece_at(chess.D5) == chess.Piece(chess.PAWN, chess.WHITE)
    assert widget._board.piece_at(chess.E4) is None

    # Undo the capture with animation
    widget.undo_move(animate=True)

    # Wait for animation to complete
    qtbot.wait(1000)

    # Verify undo restored the position
    assert widget._board.piece_at(chess.E4) == chess.Piece(chess.PAWN, chess.WHITE)
    assert widget._board.piece_at(chess.D5) == chess.Piece(chess.PAWN, chess.BLACK)


def test_multiple_move_interruptions(qtbot: QtBot) -> None:
    """Test multiple rapid move interruptions."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Rapidly play multiple moves with animation
    moves = [
        chess.Move.from_uci("e2e4"),
        chess.Move.from_uci("e7e5"),
        chess.Move.from_uci("g1f3"),
        chess.Move.from_uci("b8c6"),
    ]

    for move in moves:
        widget.play_move(move, animate=True)
        # Don't wait - immediately play next move
        # This tests that animation interruption works correctly

    # Wait for final animation
    qtbot.wait(1000)

    # Verify all moves were made
    assert len(widget._board.move_stack) == 4
    for i, move in enumerate(moves):
        assert widget._board.move_stack[i] == move

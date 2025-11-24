import chess
from pytestqt.qtbot import QtBot

from chess_widgets.board import BoardWidget


def test_chess960_kingside_king_on_d1(qtbot: QtBot) -> None:
    """Test Chess960 kingside castling with king on d1, rook on h1.

    In this position, castling kingside means king goes d1->g1,
    and rook h1->f1. This is different from standard chess.
    """
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Chess960 Position with king on c1, rook on h1
    # Simpler: start with standard position, move king to c1
    board = chess.Board(chess960=True)
    # Start fresh with custom setup
    board.clear()
    board.set_piece_at(chess.C1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.H1, chess.Piece(chess.ROOK, chess.WHITE))
    board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    # Add black king for valid position
    board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    board.set_castling_fen("KQkq")
    board.turn = chess.WHITE

    widget.set_board(board)

    # Verify setup
    assert widget._board.chess960 is True
    assert widget._board.piece_at(chess.C1) == chess.Piece(chess.KING, chess.WHITE)
    assert widget._board.piece_at(chess.H1) == chess.Piece(chess.ROOK, chess.WHITE)

    # In Chess960, castling is king captures rook notation: c1h1
    castle_move = chess.Move.from_uci("c1h1")
    assert widget._board.is_castling(castle_move)

    # Play the move - this triggers chess960 logic
    widget.play_move(castle_move, animate=True)
    qtbot.wait(1000)

    # After castling: king on g1, rook on f1
    assert widget._board.piece_at(chess.G1) == chess.Piece(chess.KING, chess.WHITE)
    assert widget._board.piece_at(chess.F1) == chess.Piece(chess.ROOK, chess.WHITE)
    assert widget._board.piece_at(chess.C1) is None
    assert widget._board.piece_at(chess.H1) is None


def test_chess960_queenside_king_on_f1(qtbot: QtBot) -> None:
    """Test Chess960 queenside castling with king on f1, rook on a1.

    King goes f1->c1, rook a1->d1. This tests non-standard positions.
    """
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Chess960 Position 293: RNBBNKQR
    # King on f1, queenside rook on a1
    fen = "rnbbnkqr/pppppppp/8/8/8/8/PPPPPPPP/RNBBNKQR w KQkq - 0 1"
    board = chess.Board(fen, chess960=True)

    # Clear path for castling
    board.remove_piece_at(chess.B1)
    board.remove_piece_at(chess.C1)
    board.remove_piece_at(chess.D1)
    board.remove_piece_at(chess.E1)

    widget.set_board(board)

    # Verify setup
    assert widget._board.chess960 is True
    assert widget._board.piece_at(chess.F1) == chess.Piece(chess.KING, chess.WHITE)
    assert widget._board.piece_at(chess.A1) == chess.Piece(chess.ROOK, chess.WHITE)

    # Chess960 castling: king captures rook
    castle_move = chess.Move.from_uci("f1a1")
    assert widget._board.is_castling(castle_move)

    widget.play_move(castle_move, animate=True)
    qtbot.wait(1000)

    # After queenside castling: king on c1, rook on d1
    assert widget._board.piece_at(chess.C1) == chess.Piece(chess.KING, chess.WHITE)
    assert widget._board.piece_at(chess.D1) == chess.Piece(chess.ROOK, chess.WHITE)
    assert widget._board.piece_at(chess.F1) is None
    assert widget._board.piece_at(chess.A1) is None


def test_chess960_black_kingside_king_on_c8(qtbot: QtBot) -> None:
    """Test Chess960 black kingside castling with king on c8, rook on h8."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Chess960 position with black king on c8
    fen = "rbkqnbnr/pppppppp/8/8/8/8/PPPPPPPP/RBKQNBNR w KQkq - 0 1"
    board = chess.Board(fen, chess960=True)

    # Make a white move first, then clear black pieces for castling
    board.push_san("e4")
    board.remove_piece_at(chess.D8)
    board.remove_piece_at(chess.E8)
    board.remove_piece_at(chess.F8)
    board.remove_piece_at(chess.G8)

    widget.set_board(board)

    assert widget._board.chess960 is True
    assert widget._board.piece_at(chess.C8) == chess.Piece(chess.KING, chess.BLACK)
    assert widget._board.piece_at(chess.H8) == chess.Piece(chess.ROOK, chess.BLACK)

    # Black castles kingside: c8h8
    castle_move = chess.Move.from_uci("c8h8")
    assert widget._board.is_castling(castle_move)

    widget.play_move(castle_move, animate=True)
    qtbot.wait(1000)

    # After castling: king on g8, rook on f8
    assert widget._board.piece_at(chess.G8) == chess.Piece(chess.KING, chess.BLACK)
    assert widget._board.piece_at(chess.F8) == chess.Piece(chess.ROOK, chess.BLACK)
    assert widget._board.piece_at(chess.C8) is None
    assert widget._board.piece_at(chess.H8) is None


def test_chess960_rook_already_on_final_square(qtbot: QtBot) -> None:
    """Test Chess960 castling where rook is already on its final square.

    King on e1, rook on f1. Kingside castling: king e1->g1, rook stays f1.
    This is an edge case in Chess960.
    """
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Custom Chess960 position: king e1, rook f1
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKRBN w KQkq - 0 1"
    board = chess.Board(fen, chess960=True)

    # Clear g1 for castling
    board.remove_piece_at(chess.G1)

    widget.set_board(board)

    assert widget._board.chess960 is True
    assert widget._board.piece_at(chess.E1) == chess.Piece(chess.KING, chess.WHITE)
    assert widget._board.piece_at(chess.F1) == chess.Piece(chess.ROOK, chess.WHITE)

    # Castling: e1f1 (king captures rook)
    castle_move = chess.Move.from_uci("e1f1")
    assert widget._board.is_castling(castle_move)

    widget.play_move(castle_move, animate=True)
    qtbot.wait(1000)

    # King moves to g1, rook stays on f1
    assert widget._board.piece_at(chess.G1) == chess.Piece(chess.KING, chess.WHITE)
    assert widget._board.piece_at(chess.F1) == chess.Piece(chess.ROOK, chess.WHITE)
    assert widget._board.piece_at(chess.E1) is None


def test_chess960_undo_non_standard_castling(qtbot: QtBot) -> None:
    """Test undoing Chess960 castling with non-standard piece positions."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # King on c1, rook on h1 (matching first test)
    board = chess.Board(chess960=True)
    board.clear()
    board.set_piece_at(chess.C1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.H1, chess.Piece(chess.ROOK, chess.WHITE))
    board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    board.set_castling_fen("KQkq")
    board.turn = chess.WHITE

    widget.set_board(board)

    fen_before = widget._board.fen()

    # Castle: c1h1
    castle_move = chess.Move.from_uci("c1h1")
    widget.play_move(castle_move, animate=False)

    # Verify castling happened
    assert widget._board.piece_at(chess.G1) == chess.Piece(chess.KING, chess.WHITE)
    assert widget._board.piece_at(chess.F1) == chess.Piece(chess.ROOK, chess.WHITE)

    # Undo with animation
    widget.undo_move(animate=True)
    qtbot.wait(1000)

    # Verify position restored
    assert widget._board.fen() == fen_before
    assert widget._board.piece_at(chess.C1) == chess.Piece(chess.KING, chess.WHITE)
    assert widget._board.piece_at(chess.H1) == chess.Piece(chess.ROOK, chess.WHITE)
    assert widget._board.piece_at(chess.G1) is None
    assert widget._board.piece_at(chess.F1) is None

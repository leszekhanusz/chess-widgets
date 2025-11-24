import chess
from pytestqt.qtbot import QtBot

from chess_widgets import BoardWidget


def test_white_kingside_castle(qtbot: QtBot) -> None:
    """Test white kingside castling (O-O)."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()

    # Set up position where white can castle kingside
    board = chess.Board()
    board.push_san("e4")
    board.push_san("e5")
    board.push_san("Nf3")
    board.push_san("Nc6")
    board.push_san("Bc4")
    board.push_san("Bc5")

    widget.set_board(board)

    # Store position before castling
    fen_before_castle = widget._board.fen()

    # Castle kingside
    castle_move = chess.Move.from_uci("e1g1")
    widget.play_move(castle_move, animate=True)

    # Wait for animation to complete
    qtbot.wait(1000)

    # Verify castling was executed
    assert widget._board.peek() == castle_move
    assert widget._board.piece_at(chess.G1) == chess.Piece(chess.KING, chess.WHITE)
    assert widget._board.piece_at(chess.F1) == chess.Piece(chess.ROOK, chess.WHITE)
    assert widget._board.piece_at(chess.E1) is None
    assert widget._board.piece_at(chess.H1) is None

    # Undo the castling move
    widget.undo_move(animate=True)

    # Wait for undo animation to complete
    qtbot.wait(1000)

    # Verify position is restored after undo
    assert widget._board.fen() == fen_before_castle
    assert widget._board.piece_at(chess.E1) == chess.Piece(chess.KING, chess.WHITE)
    assert widget._board.piece_at(chess.H1) == chess.Piece(chess.ROOK, chess.WHITE)
    assert widget._board.piece_at(chess.G1) is None
    assert widget._board.piece_at(chess.F1) is None


def test_white_queenside_castle(qtbot: QtBot) -> None:
    """Test white queenside castling (O-O-O)."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()

    # Set up position where white can castle queenside
    board = chess.Board()
    board.push_san("d4")
    board.push_san("d5")
    board.push_san("Nc3")
    board.push_san("Nc6")
    board.push_san("Bf4")
    board.push_san("Bf5")
    board.push_san("Qd2")
    board.push_san("Qd7")

    widget.set_board(board)

    # Store position before castling
    fen_before_castle = widget._board.fen()

    # Castle queenside
    castle_move = chess.Move.from_uci("e1c1")
    widget.play_move(castle_move, animate=True)

    # Wait for animation to complete
    qtbot.wait(1000)

    # Verify castling was executed
    assert widget._board.peek() == castle_move
    assert widget._board.piece_at(chess.C1) == chess.Piece(chess.KING, chess.WHITE)
    assert widget._board.piece_at(chess.D1) == chess.Piece(chess.ROOK, chess.WHITE)
    assert widget._board.piece_at(chess.E1) is None
    assert widget._board.piece_at(chess.A1) is None

    # Undo the castling move
    widget.undo_move(animate=True)

    # Wait for undo animation to complete
    qtbot.wait(1000)

    # Verify position is restored after undo
    assert widget._board.fen() == fen_before_castle
    assert widget._board.piece_at(chess.E1) == chess.Piece(chess.KING, chess.WHITE)
    assert widget._board.piece_at(chess.A1) == chess.Piece(chess.ROOK, chess.WHITE)
    assert widget._board.piece_at(chess.C1) is None
    assert widget._board.piece_at(chess.D1) is None


def test_black_kingside_castle(qtbot: QtBot) -> None:
    """Test black kingside castling (O-O)."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()

    # Set up position where black can castle kingside
    board = chess.Board()
    board.push_san("e4")
    board.push_san("e5")
    board.push_san("Nc3")
    board.push_san("Nf6")
    board.push_san("Bc4")
    board.push_san("Bc5")
    board.push_san("d3")

    widget.set_board(board)

    # Store position before castling
    fen_before_castle = widget._board.fen()

    # Castle kingside
    castle_move = chess.Move.from_uci("e8g8")
    widget.play_move(castle_move, animate=True)

    # Wait for animation to complete
    qtbot.wait(1000)

    # Verify castling was executed
    assert widget._board.peek() == castle_move
    assert widget._board.piece_at(chess.G8) == chess.Piece(chess.KING, chess.BLACK)
    assert widget._board.piece_at(chess.F8) == chess.Piece(chess.ROOK, chess.BLACK)
    assert widget._board.piece_at(chess.E8) is None
    assert widget._board.piece_at(chess.H8) is None

    # Undo the castling move
    widget.undo_move(animate=True)

    # Wait for undo animation to complete
    qtbot.wait(1000)

    # Verify position is restored after undo
    assert widget._board.fen() == fen_before_castle
    assert widget._board.piece_at(chess.E8) == chess.Piece(chess.KING, chess.BLACK)
    assert widget._board.piece_at(chess.H8) == chess.Piece(chess.ROOK, chess.BLACK)
    assert widget._board.piece_at(chess.G8) is None
    assert widget._board.piece_at(chess.F8) is None


def test_black_queenside_castle(qtbot: QtBot) -> None:
    """Test black queenside castling (O-O-O)."""
    widget = BoardWidget()
    qtbot.addWidget(widget)
    widget.show()

    # Set up position where black can castle queenside
    board = chess.Board()
    board.push_san("e4")
    board.push_san("d5")
    board.push_san("Nc3")
    board.push_san("Nc6")
    board.push_san("Bc4")
    board.push_san("Bf5")
    board.push_san("d3")
    board.push_san("Qd7")
    board.push_san("Be3")

    widget.set_board(board)

    # Store position before castling
    fen_before_castle = widget._board.fen()

    # Castle queenside
    castle_move = chess.Move.from_uci("e8c8")
    widget.play_move(castle_move, animate=True)

    # Wait for animation to complete
    qtbot.wait(1000)

    # Verify castling was executed
    assert widget._board.peek() == castle_move
    assert widget._board.piece_at(chess.C8) == chess.Piece(chess.KING, chess.BLACK)
    assert widget._board.piece_at(chess.D8) == chess.Piece(chess.ROOK, chess.BLACK)
    assert widget._board.piece_at(chess.E8) is None
    assert widget._board.piece_at(chess.A8) is None

    # Undo the castling move
    widget.undo_move(animate=True)

    # Wait for undo animation to complete
    qtbot.wait(1000)

    # Verify position is restored after undo
    assert widget._board.fen() == fen_before_castle
    assert widget._board.piece_at(chess.E8) == chess.Piece(chess.KING, chess.BLACK)
    assert widget._board.piece_at(chess.A8) == chess.Piece(chess.ROOK, chess.BLACK)
    assert widget._board.piece_at(chess.C8) is None
    assert widget._board.piece_at(chess.D8) is None

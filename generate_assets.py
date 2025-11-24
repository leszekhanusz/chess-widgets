import os

import chess
import chess.svg

ASSETS_DIR = "src/chess_widgets/assets"
os.makedirs(ASSETS_DIR, exist_ok=True)

pieces = {
    "P": "wP",
    "N": "wN",
    "B": "wB",
    "R": "wR",
    "Q": "wQ",
    "K": "wK",
    "p": "bP",
    "n": "bN",
    "b": "bB",
    "r": "bR",
    "q": "bQ",
    "k": "bK",
}

for symbol, filename in pieces.items():
    piece = chess.Piece.from_symbol(symbol)
    svg_content = chess.svg.piece(piece)
    with open(f"{ASSETS_DIR}/{filename}.svg", "w") as f:
        f.write(svg_content)
    print(f"Generated {filename}.svg")

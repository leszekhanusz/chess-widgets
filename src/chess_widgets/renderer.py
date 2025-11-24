from importlib.resources import files
from typing import Dict, Optional, Tuple

import chess
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QRadialGradient
from PySide6.QtSvg import QSvgRenderer


class Renderer:
    def __init__(self) -> None:
        self.light_color = QColor("#f0d9b5")
        self.dark_color = QColor("#b58863")
        self.highlight_color = QColor(155, 199, 0, 105)  # Lime with alpha
        self.selected_color = QColor(20, 85, 30, 128)  # Green with alpha
        self.move_hint_color = QColor(20, 85, 30, 50)  # Faint green
        self.capture_hint_color = QColor(20, 85, 0, 76)  # Green with alpha for captures
        self.check_color = QColor(255, 0, 0, 100)  # Red with alpha for check

        self.piece_renderers: Dict[str, QSvgRenderer] = {}
        self.load_assets()

    def load_assets(self) -> None:
        pieces = [
            "wP",
            "wN",
            "wB",
            "wR",
            "wQ",
            "wK",
            "bP",
            "bN",
            "bB",
            "bR",
            "bQ",
            "bK",
        ]

        # Use importlib.resources to access package assets
        assets_path = files("chess_widgets").joinpath("assets")

        for p in pieces:
            svg_file = assets_path.joinpath(f"{p}.svg")
            # Read the SVG content and pass it to QSvgRenderer
            svg_data = svg_file.read_bytes()
            renderer = QSvgRenderer(svg_data)
            self.piece_renderers[p] = renderer

    def get_visual_coordinates(self, square: int, flipped: bool) -> Tuple[int, int]:
        rank = chess.square_rank(square)
        file = chess.square_file(square)

        if flipped:
            visual_row = rank
            visual_col = 7 - file
        else:
            visual_row = 7 - rank
            visual_col = file

        return visual_row, visual_col

    def draw_board(self, painter: QPainter, rect: QRectF, flipped: bool) -> None:
        square_size = rect.width() / 8

        for row in range(8):
            for col in range(8):
                # Determine color
                is_light = (row + col) % 2 == 0
                color = self.light_color if is_light else self.dark_color

                x = rect.x() + col * square_size
                y = rect.y() + row * square_size

                painter.fillRect(QRectF(x, y, square_size, square_size), color)

                # Draw coordinates
                rank_text = ""
                file_text = ""

                actual_rank = 8 - row if not flipped else row + 1
                actual_file = (
                    chr(ord("a") + col) if not flipped else chr(ord("h") - col)
                )

                # Draw rank on the right-most column
                if col == 7:
                    rank_text = str(actual_rank)
                    # Draw at top-right of the square
                    text_color = self.dark_color if is_light else self.light_color
                    painter.setPen(text_color)
                    font = painter.font()
                    font.setPixelSize(int(square_size * 0.2))
                    painter.setFont(font)
                    painter.drawText(
                        QRectF(x, y + 2, square_size - 2, square_size),
                        Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
                        rank_text,
                    )

                # Draw file on the bottom-most row
                if row == 7:
                    file_text = actual_file
                    # Draw at bottom-left of the square
                    text_color = self.dark_color if is_light else self.light_color
                    painter.setPen(text_color)
                    font = painter.font()
                    font.setPixelSize(int(square_size * 0.2))
                    painter.setFont(font)
                    painter.drawText(
                        QRectF(x + 2, y, square_size, square_size - 2),
                        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
                        file_text,
                    )

    def draw_dragged_piece(
        self,
        painter: QPainter,
        piece: chess.Piece,
        center_pos: Tuple[float, float],
        size: float,
    ) -> None:
        piece_code = (
            f"{'w' if piece.color == chess.WHITE else 'b'}{piece.symbol().upper()}"
        )
        renderer = self.piece_renderers.get(piece_code)
        if renderer:
            # Center the piece on the mouse cursor
            x = center_pos[0] - size / 2
            y = center_pos[1] - size / 2
            renderer.render(painter, QRectF(x, y, size, size))

    def draw_legal_moves(
        self,
        painter: QPainter,
        rect: QRectF,
        moves: list[chess.Move],
        flipped: bool,
        board: chess.Board,
        hide_square: Optional[int] = None,
    ) -> None:
        square_size = rect.width() / 8
        painter.setPen(Qt.PenStyle.NoPen)

        for move in moves:
            target = move.to_square
            if target == hide_square:
                continue

            visual_row, visual_col = self.get_visual_coordinates(target, flipped)

            x = rect.x() + visual_col * square_size
            y = rect.y() + visual_row * square_size
            center_x = x + square_size / 2
            center_y = y + square_size / 2

            # Check if target is occupied (capture)
            if board.piece_at(target):
                # Draw radial gradient for capture (green corners)
                # Gradient from transparent center to green edges
                # CSS: radial-gradient(
                #   transparent 0%, transparent 79%, rgba(20, 85, 0, 0.3) 80%
                # );

                radius = (square_size / 2) * 1.414

                gradient = QRadialGradient(center_x, center_y, radius)
                gradient.setColorAt(0.0, Qt.GlobalColor.transparent)
                gradient.setColorAt(0.79, Qt.GlobalColor.transparent)
                gradient.setColorAt(0.8, self.capture_hint_color)
                gradient.setColorAt(1.0, self.capture_hint_color)

                painter.setBrush(QBrush(gradient))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.fillRect(
                    QRectF(x, y, square_size, square_size), QBrush(gradient)
                )
            else:
                color = self.move_hint_color
                painter.setBrush(QBrush(color))
                radius = square_size * 0.15
                painter.drawEllipse(
                    QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2)
                )

    def highlight_last_move(
        self, painter: QPainter, rect: QRectF, move: Optional[chess.Move], flipped: bool
    ) -> None:
        if not move:
            return

        self.highlight_square(
            painter, rect, move.from_square, self.highlight_color, flipped
        )
        self.highlight_square(
            painter, rect, move.to_square, self.highlight_color, flipped
        )

    def highlight_square(
        self, painter: QPainter, rect: QRectF, square: int, color: QColor, flipped: bool
    ) -> None:
        square_size = rect.width() / 8
        visual_row, visual_col = self.get_visual_coordinates(square, flipped)

        x = rect.x() + visual_col * square_size
        y = rect.y() + visual_row * square_size

        painter.fillRect(QRectF(x, y, square_size, square_size), color)

    def draw_check_indicator(
        self, painter: QPainter, rect: QRectF, square: int, flipped: bool
    ) -> None:
        """Draw a red blurred circle behind the king when in check."""
        square_size = rect.width() / 8
        visual_row, visual_col = self.get_visual_coordinates(square, flipped)

        x = rect.x() + visual_col * square_size
        y = rect.y() + visual_row * square_size

        # Draw a radial gradient circle for the check indicator
        center_x = x + square_size / 2
        center_y = y + square_size / 2
        # Base radius smaller to ensure it stays within the square
        radius = square_size * 0.7

        # Save painter state
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Create a radial gradient for smooth blur effect
        gradient = QRadialGradient(center_x, center_y, radius)
        # Center is opaque red
        gradient.setColorAt(0, QColor(255, 0, 0, 150))
        # Edge fades to transparent
        gradient.setColorAt(1, QColor(255, 0, 0, 0))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(
            QRectF(
                center_x - radius,
                center_y - radius,
                radius * 2,
                radius * 2,
            )
        )

        painter.restore()

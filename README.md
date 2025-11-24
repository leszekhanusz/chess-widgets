# Python Chess Widgets

[![Tests](https://github.com/leszekhanusz/chess-widgets/actions/workflows/test.yml/badge.svg)](https://github.com/leszekhanusz/chess-widgets/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/leszekhanusz/chess-widgets/branch/main/graph/badge.svg)](https://codecov.io/gh/leszekhanusz/chess-widgets)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/chess-widgets.svg)](https://pypi.org/project/chess-widgets/)

A modern, feature-rich chess board widget for PySide6 applications, designed to mimic the visual style and user experience of Lichess. It is built on top of the powerful [python-chess](https://github.com/niklasf/python-chess) library.

![Fool's Mate Demo](examples/assets/fools_mate.gif)

## Features

- **Lichess-like Aesthetics**: Uses standard Lichess colors, SVG piece sets, and highlighting styles.
- **Interactive**: Supports both drag-and-drop and click-to-move interactions.
- **Smooth Animations**: Piece movements are animated for a better user experience.
- **Visual Indicators**:
  - Legal move highlights (dots for empty squares, rings for captures).
  - Last move highlighting.
  - Check indicator (red blurred glow behind the king).
  - Selected piece and hover highlights.
- **Responsive**: The board maintains its square aspect ratio and centers itself within the widget, scaling to fit the available space.
- **Board Flipping**: Easily toggle between White and Black perspectives.
- **Type Safe**: Fully typed codebase with `mypy` support (PEP 561 compliant).

## Installation

You can install the package from PyPI:

```bash
pip install chess-widgets
```

## Usage

Here is a simple example of how to use the `BoardWidget` in a PySide6 application:

```python
import sys
import chess
from PySide6.QtWidgets import QApplication, QMainWindow
from chess_widgets.board import BoardWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess Board Example")
        self.resize(600, 600)

        # Create the widget
        self.board_widget = BoardWidget()
        self.setCentralWidget(self.board_widget)

        # Connect to the move signal
        self.board_widget.move_played.connect(self.on_move_played)

        # Optional: Set an initial board state (defaults to starting position)
        # self.board_widget.set_board(chess.Board())

    def on_move_played(self, move: chess.Move, move_info: dict):
        interactive = move_info.get("interactive", False)
        print(f"{'Interactive' if interactive else 'Programmatic'} move: {move}")
        # The widget updates its internal board automatically for user moves.
        # You can access the board state via:
        # print(self.board_widget._board.fen())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

A more complex example with move history navigation, board flipping, and random moves played for the opposite color can be found in the [examples/demo.py](examples/demo.py) file.

![Demo](examples/assets/demo.png)


### API Overview

- **`set_board(board: chess.Board)`**: Sets the board state to display.
- **`set_flipped(flipped: bool)`**: Sets the board orientation (`True` for Black at bottom, `False` for White at bottom).
- **`play_move(move: chess.Move, animate: bool = True, interactive: bool = False)`**: Programmatically make a move on the board, optionally with animation.
- **`undo_move(move: chess.Move, animate: bool = True)`**: Programmatically unmake the last move on the board, optionally with animation.
- `move_played(chess.Move, dict)`: Emitted when a move is played. The dictionary contains move information (e.g., `{'interactive': True}`).
- `move_undone(chess.Move)`: Emitted when a move is undone.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to set up your development environment and submit changes.

## License

[MIT License](LICENSE)

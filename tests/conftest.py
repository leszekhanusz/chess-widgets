from typing import Generator

import pytest

from chess_widgets.board import BoardWidget


@pytest.fixture(autouse=True)
def speed_up_animations() -> Generator[None, None, None]:
    """Globally speed up animations for all tests.

    We set animation_increment to 0.5, which means the animation completes
    in two frames. Default is 0.05 (20 frames).
    """
    original_inc = BoardWidget.animation_increment
    BoardWidget.animation_increment = 0.5
    yield
    BoardWidget.animation_increment = original_inc

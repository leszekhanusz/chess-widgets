# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Breaking Change**: Renamed project from `lichess-board` to `chess-widgets`.
- **Breaking Change**: Renamed package from `lichess_board` to `chess_widgets`.
- **Breaking Change**: Renamed `ChessBoardWidget` to `BoardWidget` (imported directly from `chess_widgets`).

## [0.4.0] - 2025-11-22

### Added
- Added `move_undone` signal to `ChessBoardWidget`.
- Added mouse wheel support to demo application.
- Added visual regression tests for widget rendering.
- Added code coverage verification with pytest-cov and Codecov integration.
- Added project URLs to `pyproject.toml`.

### Changed
- Updated capture indicator to match Lichess style.
- Refactored `play_move` and `undo_move` to be more DRY.
- Refactored visual coordinate calculation to use a shared helper method.
- Refactored castling animation logic to support Chess960.
- Improved Chess960 tests to use non-standard starting positions.
- Added comprehensive tests to achieve 100% code coverage.

### Fixed
- Fixed visual regression tests for CI by using offscreen rendering.

### Removed
- Removed unused `draw_pieces` method.
- Removed unneeded code in demo.py.

## [0.3.0] - 2025-11-21

### Added
- Added support for Python 3.13 and 3.14.
- Added badges to README for build status and supported Python versions.
- Added Python version classifiers to `pyproject.toml`.

## [0.2.0] - 2025-11-21

### Added
- Added `make fix` target to Makefile for auto-formatting code with `isort` and `black`.
- Added single source of truth for versioning in `src/lichess_board/__version__.py`.
- Added `interactive` flag to `move_played` signal payload (inside `move_info` dictionary).
- Added functionality to hide the mouse cursor while dragging pieces for a better visual experience.

### Changed
- **Breaking Change**: Dropped support for Python 3.9. Now requires Python 3.10 or later.
- **Breaking Change**: The `move_played` signal now emits `(chess.Move, dict)` instead of `(chess.Move, bool)`. The dictionary contains move information, currently `{'interactive': bool}`.
- Updated `play_move` and `undo_move` to clear legal move highlights (dots) before executing/undoing moves.
- Pinned development dependencies to specific versions in `pyproject.toml`.
- Added version constraints to runtime dependencies (`PySide6`, `python-chess`) to prevent breaking changes from major version updates.

### Fixed
- Fixed an issue where legal move highlights would persist when navigating through move history.

## [0.1.0] - 2023-10-27

### Added
- Initial release of `lichess-board`.
- Basic chess board widget with Lichess-like aesthetics.
- Support for drag-and-drop and click-to-move interactions.
- Move animation support.
- Board flipping support.
- Legal move highlighting.
- Check indicator.

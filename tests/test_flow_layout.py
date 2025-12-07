import pytest
from PySide6.QtCore import QRect, Qt
from PySide6.QtWidgets import QLabel, QLayout, QLayoutItem, QStyle, QWidget

from chess_widgets.flow_layout import FlowLayout


@pytest.fixture
def app(qapp: object) -> object:
    return qapp


def test_flow_layout_basic(app: object) -> None:
    """Test basic adding and counting of items."""
    widget = QWidget()
    layout = FlowLayout(widget, margin=10, h_spacing=5, v_spacing=5)

    assert layout.count() == 0
    assert layout.hasHeightForWidth() is True
    assert layout.expandingDirections() == Qt.Orientation(0)

    # Add items
    for i in range(5):
        layout.addWidget(QLabel(f"Label {i}"))

    assert layout.count() == 5

    # Test itemAt
    item = layout.itemAt(2)
    assert item is not None
    wid = item.widget()
    assert isinstance(wid, QLabel)
    assert wid.text() == "Label 2"

    # Test itemAt out of bounds
    assert layout.itemAt(10) is None
    assert layout.itemAt(-1) is None

    # Test takeAt
    item = layout.takeAt(0)
    assert item is not None
    wid = item.widget()
    assert isinstance(wid, QLabel)
    assert wid.text() == "Label 0"
    assert layout.count() == 4

    # Test takeAt out of bounds
    assert layout.takeAt(10) is None

    # Clean up (implicit via __del__ and widget deletion, but explicit for coverage)
    item = layout.takeAt(0)
    while item:
        item = layout.takeAt(0)
    assert layout.count() == 0


def test_flow_layout_spacing_explicit(app: object) -> None:
    """Test explicit spacing."""
    layout = FlowLayout(margin=10, h_spacing=20, v_spacing=30)
    assert layout.horizontalSpacing() == 20
    assert layout.verticalSpacing() == 30


def test_flow_layout_spacing_smart(app: object) -> None:
    """Test smart spacing (inheritance from style)."""
    # Parent is a widget
    parent = QWidget()
    layout = FlowLayout(parent)
    # The exact value depends on the style, but it should be an integer
    assert isinstance(layout.horizontalSpacing(), int)
    assert isinstance(layout.verticalSpacing(), int)

    # Parent is another layout (or no widget parent)
    # FlowLayout constructor takes QWidget parent, so we simulate nesting if needed
    # But smartSpacing handles "no parent" check too
    orphan_layout = FlowLayout()
    assert orphan_layout.horizontalSpacing() == -1

    # Mock parent to return specific style metric?
    # Hard to mock QStyle via PySide easily without full setup.
    # We trust QStyle calls are made.


def test_flow_layout_geometry_and_size(app: object) -> None:
    """Test size calculations and setGeometry logic."""
    parent = QWidget()
    layout = FlowLayout(parent, margin=0, h_spacing=0, v_spacing=0)

    # Add 3 widgets of size 100x100
    for _ in range(3):
        lbl = QLabel("Test")
        lbl.setFixedSize(100, 100)
        layout.addWidget(lbl)

    # Minimum size should be at least one item
    min_size = layout.minimumSize()
    assert min_size.width() >= 100
    assert min_size.height() >= 100

    size_hint = layout.sizeHint()
    assert size_hint == min_size

    # Test doLayout via setGeometry
    # 1. Wide enough for all 3
    layout.setGeometry(QRect(0, 0, 300, 100))
    assert layout.count() == 3
    # Positions should be (0,0), (100,0), (200,0)

    item0 = layout.itemAt(0)
    item1 = layout.itemAt(1)
    item2 = layout.itemAt(2)

    assert item0 is not None
    assert item1 is not None
    assert item2 is not None

    assert item0.geometry().x() == 0
    assert item0.geometry().y() == 0

    assert item1.geometry().x() == 100
    assert item1.geometry().y() == 0

    # 2. Narrow, forcing wrap
    # Width 150 -> should fit 1 per row (if spacing 0) but let's see.
    # Actually if width is 150, and item is 100:
    # Item 1 at 0. Next x at 100. Fits.
    # Item 2 at 100. Next x at 200. > 150? Yes. Should wrap.

    layout.setGeometry(QRect(0, 0, 150, 300))
    # item0 at (0,0)
    # item1 should be at (0, 100) because "next_x - space_x > effective_rect.right()"
    # effective right is 150. next_x for item2 would be 100 + 100 = 200.

    assert item0.geometry().x() == 0
    assert item0.geometry().y() == 0

    assert item1.geometry().x() == 0
    assert item1.geometry().y() == 100

    assert item2.geometry().x() == 0
    assert item2.geometry().y() == 200

    # Test heightForWidth
    h = layout.heightForWidth(150)
    # Should be 300 (3 rows of 100)
    assert h >= 300


def test_flow_layout_constrain_large_item(app: object) -> None:
    """Test that an item larger than layout width is constrained."""
    parent = QWidget()
    layout = FlowLayout(parent)

    lbl = QLabel("Huge " * 20)
    # Ensure it wants to be big but can shrink
    lbl.setMinimumWidth(10)
    layout.addWidget(lbl)

    # Layout width only 200
    layout.setGeometry(QRect(0, 0, 200, 500))

    # The item size should be constrained to 200 width (or less due to margins)
    # Note: FlowLayout.doLayout updates item geometry
    item = layout.itemAt(0)
    assert item is not None
    # Code says: if size.width() > effective_rect.width(): size.setWidth(...)
    assert item.geometry().width() <= 200


def test_flow_layout_height_for_width_constraint(app: object) -> None:
    """Test constrained width triggers heightForWidth recalculation."""
    parent = QWidget()
    layout = FlowLayout(parent)

    lbl = QLabel("Word " * 50)
    lbl.setWordWrap(True)
    layout.addWidget(lbl)

    # Wide: Height should be small
    layout.setGeometry(QRect(0, 0, 1000, 50))
    item = layout.itemAt(0)
    assert item is not None
    h_wide = item.geometry().height()

    # Narrow: Height should be large
    layout.setGeometry(QRect(0, 0, 100, 500))
    item = layout.itemAt(0)
    assert item is not None
    h_narrow = item.geometry().height()

    assert h_narrow > h_wide


def test_smart_spacing_nested_layout(app: object) -> None:
    """Test smartSpacing when parent is Layout (though unusual for FlowLayout usage)."""
    # This hits the 'else' branch in smartSpacing
    # We need a structure: Widget -> Layout -> FlowLayout (as child layout?)
    # QLayouts usually cannot be parented to QLayouts directly in constructor in PySide?
    # Actually they can be added.

    widget = QWidget()
    main_layout = FlowLayout(widget)
    sub_layout = FlowLayout()
    main_layout.addItem(sub_layout)

    # Now sub_layout.parent() is main_layout (which is a QLayout)
    # Wait, addItem doesn't re-parent usually?
    # setParent for layout?

    # Let's try to simulate the code path:
    # parent = self.parent() -> if not widget -> cast(QLayout, parent).spacing()

    # We can manually create a FlowLayout with another Layout as parent?
    # Not standard in Qt python bindings easily.
    # But we can create a subclass that claims to have a layout parent
    # or just mock parent() method?

    class MockLayout(QLayout):
        def addItem(self, item: QLayoutItem) -> None:
            pass

        def count(self) -> int:
            return 0

        def itemAt(self, i: int) -> QLayoutItem | None:
            return None

        def takeAt(self, i: int) -> QLayoutItem | None:  # type: ignore[override]
            return None

        def spacing(self) -> int:
            return 123

    mock_parent = MockLayout()
    _ = FlowLayout()
    # Mocking setParent isn't easy as it's C++.
    # Instead, we subclass FlowLayout and mock parent()

    class TestFlowLayout(FlowLayout):
        def parent(self) -> QWidget:  # type: ignore
            return mock_parent  # type: ignore

    test_layout = TestFlowLayout()
    # Should hit lines 130-131
    assert (
        test_layout.smartSpacing(QStyle.PixelMetric.PM_LayoutHorizontalSpacing) == 123
    )

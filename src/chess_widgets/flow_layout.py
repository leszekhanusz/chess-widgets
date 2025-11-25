from typing import List, Optional, cast

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QLayout, QLayoutItem, QStyle, QWidget


class FlowLayout(QLayout):
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        margin: int = -1,
        h_spacing: int = -1,
        v_spacing: int = -1,
    ) -> None:
        super().__init__(parent)
        if margin >= 0:
            self.setContentsMargins(margin, margin, margin, margin)
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self._items: List[QLayoutItem] = []

    def __del__(self) -> None:
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item: QLayoutItem) -> None:
        self._items.append(item)

    def horizontalSpacing(self) -> int:
        if self._h_spacing >= 0:
            return self._h_spacing
        return int(self.smartSpacing(QStyle.PixelMetric.PM_LayoutHorizontalSpacing))

    def verticalSpacing(self) -> int:
        if self._v_spacing >= 0:
            return self._v_spacing
        return int(self.smartSpacing(QStyle.PixelMetric.PM_LayoutVerticalSpacing))

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> Optional[QLayoutItem]:
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> Optional[QLayoutItem]:  # type: ignore[override]
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self) -> Qt.Orientation:
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self.doLayout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())

        margins = self.contentsMargins()
        size += QSize(
            margins.left() + margins.right(), margins.top() + margins.bottom()
        )
        return size

    def doLayout(self, rect: QRect, test_only: bool) -> int:
        margins = self.contentsMargins()
        left, top, right, bottom = (
            margins.left(),
            margins.top(),
            margins.right(),
            margins.bottom(),
        )
        effective_rect = rect.adjusted(+left, +top, -right, -bottom)
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0

        for item in self._items:
            wid = item.widget()
            space_x = self.horizontalSpacing()
            space_y = self.verticalSpacing()

            size = item.sizeHint()

            # Constrain width to available space
            if size.width() > effective_rect.width():
                size.setWidth(effective_rect.width())
                if wid and wid.hasHeightForWidth():
                    size.setHeight(wid.heightForWidth(size.width()))

            next_x = x + size.width() + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + size.width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), size))

            x = next_x
            line_height = max(line_height, size.height())

        return int(y + line_height - rect.y() + bottom)

    def smartSpacing(self, pm: QStyle.PixelMetric) -> int:
        parent = self.parent()
        if not parent:
            return -1
        elif parent.isWidgetType():
            widget_parent = cast(QWidget, parent)
            return int(widget_parent.style().pixelMetric(pm, None, widget_parent))
        else:
            # QLayout doesn't have spacing() method in all bindings?
            # But usually it does if it inherits from QLayout.
            return int(cast(QLayout, parent).spacing())
